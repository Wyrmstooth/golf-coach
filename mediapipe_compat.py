"""
MediaPipe compatibility shim for 0.10.x+

MediaPipe 0.10.x removed `mp.solutions` in favour of the Tasks API.
Importing this module patches `mediapipe.solutions` back onto the `mp`
namespace so all existing code that does:

    import mediapipe as mp
    mp.solutions.pose / mp.solutions.drawing_utils / mp.solutions.drawing_styles

continues to work without any other changes.
"""

from __future__ import annotations

import cv2
import mediapipe as mp
import numpy as np
from pathlib import Path
from typing import Optional, List
from urllib.request import urlretrieve

# Patch PoseLandmarker.__del__ to suppress the benign RuntimeError that fires
# when Python shuts down its thread executor before MediaPipe can free itself.
try:
    from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmarker as _PL
    _orig_pl_del = _PL.__del__

    def _safe_pl_del(self):
        try:
            _orig_pl_del(self)
        except Exception:
            pass

    _PL.__del__ = _safe_pl_del
except Exception:
    pass

_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_full/float16/latest/pose_landmarker_full.task"
)

# ---------------------------------------------------------------------------
# Locate the bundled pose landmarker model
# ---------------------------------------------------------------------------
_MODEL_PATH = Path(__file__).resolve().parent / "models" / "pose_landmarker_full.task"
if not _MODEL_PATH.exists():
    _MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        urlretrieve(_MODEL_URL, _MODEL_PATH)
    except Exception as exc:
        raise FileNotFoundError(
            f"Pose landmarker model not found at {_MODEL_PATH} and automatic download failed. "
            "Download it with:\n"
            f"  curl -L '{_MODEL_URL}' -o '{_MODEL_PATH}'"
        ) from exc


# ---------------------------------------------------------------------------
# Thin wrappers that reproduce the old mp.solutions.pose result shape
# ---------------------------------------------------------------------------

class _NLandmark:
    """Wraps a Tasks API NormalizedLandmark to match old .x/.y/.z/.visibility API."""
    __slots__ = ("x", "y", "z", "visibility")

    def __init__(self, lm):
        self.x = lm.x
        self.y = lm.y
        self.z = lm.z
        self.visibility = getattr(lm, "visibility", 1.0)


class _LandmarkList:
    """Wraps a list of landmarks to expose a .landmark attribute."""
    __slots__ = ("landmark",)

    def __init__(self, lm_list):
        self.landmark = [_NLandmark(lm) for lm in lm_list]


class _PoseResult:
    """Mimics the old mp.solutions.pose.Pose.process() return value."""
    __slots__ = ("pose_landmarks",)

    def __init__(self, lm_list: Optional[list]):
        self.pose_landmarks = _LandmarkList(lm_list) if lm_list else None


# ---------------------------------------------------------------------------
# mp.solutions.pose
# ---------------------------------------------------------------------------

POSE_CONNECTIONS = frozenset([
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
    (17, 19), (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28),
    (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32),
])

# Landmark index enum (partial - most commonly used)
class PoseLandmark:
    NOSE = 0
    LEFT_EYE_INNER = 1; LEFT_EYE = 2; LEFT_EYE_OUTER = 3
    RIGHT_EYE_INNER = 4; RIGHT_EYE = 5; RIGHT_EYE_OUTER = 6
    LEFT_EAR = 7; RIGHT_EAR = 8
    MOUTH_LEFT = 9; MOUTH_RIGHT = 10
    LEFT_SHOULDER = 11; RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13; RIGHT_ELBOW = 14
    LEFT_WRIST = 15; RIGHT_WRIST = 16
    LEFT_PINKY = 17; RIGHT_PINKY = 18
    LEFT_INDEX = 19; RIGHT_INDEX = 20
    LEFT_THUMB = 21; RIGHT_THUMB = 22
    LEFT_HIP = 23; RIGHT_HIP = 24
    LEFT_KNEE = 25; RIGHT_KNEE = 26
    LEFT_ANKLE = 27; RIGHT_ANKLE = 28
    LEFT_HEEL = 29; RIGHT_HEEL = 30
    LEFT_FOOT_INDEX = 31; RIGHT_FOOT_INDEX = 32


class Pose:
    """
    Backward-compatible wrapper around mediapipe.tasks.python.vision.PoseLandmarker.

    Accepts the same keyword arguments as the old mp.solutions.pose.Pose() and
    returns results whose .pose_landmarks.landmark[i].x/y/z match the old API.
    """

    def __init__(self,
                 static_image_mode: bool = False,
                 model_complexity: int = 1,
                 smooth_landmarks: bool = True,
                 enable_segmentation: bool = False,
                 smooth_segmentation: bool = True,
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5):
        import sys
        if sys.version_info >= (3, 12):
            raise RuntimeError(
                f"mediapipe_compat requires Python 3.10/3.11 but you are running "
                f"Python {sys.version_info.major}.{sys.version_info.minor}.\n\n"
                "Run the backend with the golfpose environment:\n"
                "  & \"$env:USERPROFILE\\miniconda3\\envs\\golfpose\\python.exe\" "
                "-m uvicorn backend.main:app --reload --port 8000"
            )

        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        running_mode = (
            vision.RunningMode.IMAGE if static_image_mode
            else vision.RunningMode.VIDEO
        )

        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(_MODEL_PATH)),
            running_mode=running_mode,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
            min_pose_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            output_segmentation_masks=enable_segmentation,
        )

        try:
            self._landmarker = vision.PoseLandmarker.create_from_options(options)
        except AttributeError as exc:
            import sys
            raise RuntimeError(
                f"MediaPipe Tasks API failed to load its native library ({exc}).\n\n"
                "This almost always means you are running the wrong Python.\n"
                "Use the golfpose conda environment (Python 3.10):\n"
                "  & \"$env:USERPROFILE\\miniconda3\\envs\\golfpose\\python.exe\" "
                "-m uvicorn backend.main:app --reload --port 8000"
            ) from exc

        self._static = static_image_mode
        self._frame_ts = 0  # millisecond timestamp for VIDEO mode

    def process(self, image: np.ndarray) -> _PoseResult:
        """
        Process a single RGB frame and return a result compatible with the old API.
        image must be an RGB uint8 ndarray (same as old API).
        """
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)

        if self._static:
            result = self._landmarker.detect(mp_image)
        else:
            self._frame_ts += 33  # ~30 fps increment
            result = self._landmarker.detect_for_video(mp_image, self._frame_ts)

        if result.pose_landmarks and len(result.pose_landmarks) > 0:
            return _PoseResult(result.pose_landmarks[0])
        return _PoseResult(None)

    def close(self):
        try:
            self._landmarker.close()
        except Exception:
            pass

    def __del__(self):
        # Suppress RuntimeError from mediapipe executor shutdown during
        # Python interpreter teardown (harmless but noisy)
        try:
            self.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


# ---------------------------------------------------------------------------
# mp.solutions.drawing_utils
# ---------------------------------------------------------------------------

class DrawingSpec:
    def __init__(self, color=(0, 255, 0), thickness=2, circle_radius=2):
        self.color = color
        self.thickness = thickness
        self.circle_radius = circle_radius


_DEFAULT_CONNECTION_SPEC = DrawingSpec(color=(245, 117, 66), thickness=2)
_DEFAULT_LANDMARK_SPEC = DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=3)


def draw_landmarks(
    image: np.ndarray,
    landmark_list,
    connections=None,
    landmark_drawing_spec=None,
    connection_drawing_spec=None,
):
    """OpenCV-based drop-in for mp.solutions.drawing_utils.draw_landmarks."""
    if landmark_list is None:
        return

    h, w = image.shape[:2]
    lms = landmark_list.landmark

    # Draw connections
    if connections:
        conn_spec = connection_drawing_spec or _DEFAULT_CONNECTION_SPEC
        for start_idx, end_idx in connections:
            if start_idx >= len(lms) or end_idx >= len(lms):
                continue
            s, e = lms[start_idx], lms[end_idx]
            sp = (int(s.x * w), int(s.y * h))
            ep = (int(e.x * w), int(e.y * h))
            spec = (
                conn_spec.get((start_idx, end_idx), _DEFAULT_CONNECTION_SPEC)
                if isinstance(conn_spec, dict) else conn_spec
            )
            cv2.line(image, sp, ep, spec.color, spec.thickness)

    # Draw landmark dots
    lm_spec = landmark_drawing_spec or _DEFAULT_LANDMARK_SPEC
    for lm in lms:
        pt = (int(lm.x * w), int(lm.y * h))
        spec = (
            next(iter(lm_spec.values()), _DEFAULT_LANDMARK_SPEC)
            if isinstance(lm_spec, dict) else lm_spec
        )
        cv2.circle(image, pt, spec.circle_radius, spec.color, -1)


# ---------------------------------------------------------------------------
# mp.solutions.drawing_styles
# ---------------------------------------------------------------------------

def get_default_pose_landmarks_style() -> DrawingSpec:
    return DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=3)


# ---------------------------------------------------------------------------
# Build the solutions namespace objects
# ---------------------------------------------------------------------------

class _DrawingUtils:
    DrawingSpec = DrawingSpec
    draw_landmarks = staticmethod(draw_landmarks)


class _DrawingStyles:
    get_default_pose_landmarks_style = staticmethod(get_default_pose_landmarks_style)


class _PoseModule:
    Pose = Pose
    PoseLandmark = PoseLandmark
    POSE_CONNECTIONS = POSE_CONNECTIONS


class _Solutions:
    pose = _PoseModule()
    drawing_utils = _DrawingUtils()
    drawing_styles = _DrawingStyles()


# ---------------------------------------------------------------------------
# Patch mp.solutions onto the live mediapipe module object
# ---------------------------------------------------------------------------
if not hasattr(mp, "solutions"):
    mp.solutions = _Solutions()
