"""
Video processing utilities for golf swing analysis
"""

import cv2
import io
import sys
import numpy as np
import mediapipe as mp
import subprocess
from pathlib import Path
from typing import Tuple, Optional, Dict, List
from tqdm import tqdm


def _safe_tqdm(*args, **kwargs):
    """
    tqdm wrapper that gracefully handles Windows OSError WinError 6.

    When uvicorn runs analysis in a background thread on Windows, sys.stderr
    is not connected to a real console handle and raises:
        OSError: [WinError 6] The handle is invalid
    We redirect tqdm to stdout and fall back to a null sink (io.StringIO)
    so the video-rendering loop always completes without crashing.
    """
    # Try stdout first; if it's also broken, use a null sink
    try:
        if sys.stdout and hasattr(sys.stdout, 'write'):
            sys.stdout.write('')  # probe for validity
            kwargs.setdefault('file', sys.stdout)
        else:
            kwargs['file'] = io.StringIO()
    except OSError:
        kwargs['file'] = io.StringIO()
    # Also disable the dynamic terminal-width detection that can trigger the error
    kwargs.setdefault('dynamic_ncols', False)
    return tqdm(*args, **kwargs)
from utils.biomechanics import calculate_joint_angle, extract_landmarks_from_mediapipe
from utils.ball_tracker import BallTrajectoryPoint


class VideoProcessor:
    """Handle video input/output and frame processing"""
    
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_style = mp.solutions.drawing_styles
    
    def get_video_properties(self, video_path: str) -> Dict:
        """
        Get video properties
        
        Args:
            video_path: Path to video file
        
        Returns:
            Dict with width, height, fps, frame_count
        """
        cap = cv2.VideoCapture(video_path)
        props = {
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        }
        cap.release()
        return props
    
    def calculate_upscale_factor(self, width: int, min_width: int = 640) -> float:
        """Calculate upscale factor for small videos"""
        if width < min_width:
            return min_width / width
        return 1.0
    
    def create_annotated_video(
        self,
        video_path: str,
        output_path: str,
        phase_ranges: Dict[str, Tuple[int, int]],
        show_pose: bool = True,
        slow_motion: float = 0.5,
        max_resolution: int = 1080,
        ball_trajectory: Optional[List[BallTrajectoryPoint]] = None,
        faults_by_phase: Optional[Dict[str, List[Dict]]] = None,
    ) -> str:
        """
        Create annotated video with phase labels and pose overlay
        
        Args:
            video_path: Input video path
            output_path: Output video path
            phase_ranges: Dict of phase ranges
            show_pose: Whether to show pose skeleton
            slow_motion: Speed multiplier (0.5 = half speed)
            max_resolution: Maximum output resolution (height)
        
        Returns:
            Path to output video
        """
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"🎬 Generating annotated video...")
        print(f"   Resolution: {width}x{height}, FPS: {fps:.1f}")
        
        # Calculate scale factor
        # For small videos: upscale to at least 640px width
        # For large videos (4K): downscale to max_resolution
        if width < 640:
            scale_factor = 640 / width
        elif height > max_resolution:
            scale_factor = max_resolution / height
            print(f"   ⚠️  Downscaling 4K video for faster processing")
        else:
            scale_factor = 1.0
        
        output_width = int(width * scale_factor)
        output_height = int(height * scale_factor)
        
        if scale_factor != 1.0:
            print(f"   Output resolution: {output_width}x{output_height}")
        
        # Setup output video with efficient codec
        output_fps = max(15, fps * slow_motion)
        print(f"   Output FPS: {output_fps:.1f}")
        
        # Try mp4v first (built-in OpenCV codec, no external library needed).
        # avc1 (H.264/libopenh264) is intentionally after mp4v because on Windows
        # an incorrect libopenh264 version can make out.release() deadlock even when
        # out.isOpened() returned True.
        out = None
        for codec in ['mp4v', 'avc1', 'XVID', 'MJPG']:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            out = cv2.VideoWriter(output_path, fourcc, output_fps, (output_width, output_height))
            if out.isOpened():
                if codec not in ('mp4v', 'avc1'):
                    print(f"   Using {codec} codec")
                break
            out.release()
        
        if not out or not out.isOpened():
            raise RuntimeError(f"Failed to create video writer for {output_path}")
        
        # Setup pose detector with lower complexity for 3x speed
        pose = self.mp_pose.Pose(
            static_image_mode=False, 
            model_complexity=1,  # Changed from 2 to 1 for 3x faster processing
            min_tracking_confidence=0.5
        ) if show_pose else None
        
        # Preindex ball trajectory by frame for quick lookup
        ball_by_frame: Dict[int, BallTrajectoryPoint] = {}
        if ball_trajectory:
            for pt in ball_trajectory:
                ball_by_frame[int(pt.frame)] = pt

        # Precompute per-phase fault labels and banner colors (if provided)
        phase_fault_labels: Dict[str, List[str]] = {}
        phase_banner_colors: Dict[str, Tuple[int, int, int]] = {}
        if faults_by_phase:
            severity_to_color = {
                "none": (0, 255, 0),       # green
                "minor": (0, 215, 255),    # yellow/cyan
                "major": (0, 165, 255),    # orange
                "critical": (0, 0, 255),   # red
            }
            severity_emoji = {
                "critical": "🔴",
                "major": "🟠",
                "minor": "🟡",
            }

            for phase_name, faults in (faults_by_phase or {}).items():
                counts = {"critical": 0, "major": 0, "minor": 0}
                labels: List[str] = []
                for fault in faults or []:
                    sev = (fault.get("severity") or "").lower()
                    if sev in counts:
                        counts[sev] += 1
                    title = fault.get("title")
                    if title:
                        emoji = severity_emoji.get(sev, "⚠️")
                        labels.append(f"{emoji} {title}")

                max_severity = "none"
                for sev in ("critical", "major", "minor"):
                    if counts[sev] > 0:
                        max_severity = sev
                        break

                phase_banner_colors[phase_name] = severity_to_color.get(
                    max_severity, (0, 255, 0)
                )
                # Show at most two fault titles on video overlay
                phase_fault_labels[phase_name] = labels[:2]

        try:
            for frame_idx in _safe_tqdm(range(total_frames), desc="Rendering video"):
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Upscale or downscale if needed
                if scale_factor != 1.0:
                    frame = cv2.resize(
                        frame,
                        (output_width, output_height),
                        interpolation=cv2.INTER_CUBIC,
                    )

                # Get current phase for this frame
                phase = self._get_phase_at_frame(frame_idx, phase_ranges)

                # Expose active faults for this phase to pose overlay (if any)
                if faults_by_phase:
                    self._active_phase_faults = faults_by_phase.get(phase, []) or []
                else:
                    self._active_phase_faults = []

                # Add pose overlay
                if show_pose and pose:
                    frame = self._add_pose_overlay(frame, pose)
                
                # Add annotations (phase label, angles, per-phase faults)
                frame = self._add_annotations(
                    frame,
                    phase,
                    frame_idx,
                    output_width,
                    output_height,
                    phase_banner_colors=phase_banner_colors,
                    phase_fault_labels=phase_fault_labels,
                )

                # Add ball overlay (Module 3)
                if ball_by_frame:
                    frame = self._add_ball_overlay(frame, frame_idx, ball_by_frame)
                
                out.write(frame)
        finally:
            cap.release()
            out.release()
            if pose:
                pose.close()
        
        print(f"✅ Saved annotated video: {output_path}")
        
        # Return directly without re-encoding (saves significant time)
        return output_path
    
    def _add_pose_overlay(self, frame: np.ndarray, pose) -> np.ndarray:
        """Add pose skeleton overlay to frame"""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)
        
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_style.get_default_pose_landmarks_style()
            )
            
            # Calculate and store angles
            landmarks = extract_landmarks_from_mediapipe(results.pose_landmarks, self.mp_pose)
            self._current_angles = self._calculate_angles(landmarks)

            # Highlight key joints when severe faults are present in this phase
            active_faults = getattr(self, "_active_phase_faults", []) or []
            if active_faults:
                # Map specific fault titles to landmark indices
                fault_joint_map: Dict[str, List[int]] = {
                    # DOWNSWING right arm collapse: right shoulder, elbow, wrist
                    "Right Arm Collapse": [
                        int(self.mp_pose.PoseLandmark.RIGHT_SHOULDER),
                        int(self.mp_pose.PoseLandmark.RIGHT_ELBOW),
                        int(self.mp_pose.PoseLandmark.RIGHT_WRIST),
                    ],
                    # ADDRESS excessive forward bend: shoulders and hips (spine proxy)
                    "Excessive Forward Bend": [
                        int(self.mp_pose.PoseLandmark.LEFT_SHOULDER),
                        int(self.mp_pose.PoseLandmark.RIGHT_SHOULDER),
                        int(self.mp_pose.PoseLandmark.LEFT_HIP),
                        int(self.mp_pose.PoseLandmark.RIGHT_HIP),
                    ],
                }

                h, w, _ = frame.shape
                highlight_indices: List[int] = []
                for fault in active_faults:
                    severity = (fault.get("severity") or "").lower()
                    if severity not in ("critical", "major"):
                        continue
                    title = fault.get("title")
                    if not title:
                        continue
                    indices = fault_joint_map.get(title)
                    if indices:
                        highlight_indices.extend(indices)

                for idx in set(highlight_indices):
                    if 0 <= idx < landmarks.shape[0]:
                        x = int(landmarks[idx][0] * w)
                        y = int(landmarks[idx][1] * h)
                        cv2.circle(frame, (x, y), 7, (0, 0, 255), -1)
        
        return frame
    
    def _calculate_angles(self, landmarks: np.ndarray) -> Dict[str, float]:
        """Calculate joint angles from landmarks"""
        angles = {}
        
        try:
            # Elbow angles: shoulder - elbow - wrist
            angles['L Elbow'] = calculate_joint_angle(landmarks, (11, 13, 15))
            angles['R Elbow'] = calculate_joint_angle(landmarks, (12, 14, 16))
            
            # Knee angles: hip - knee - ankle
            angles['L Knee'] = calculate_joint_angle(landmarks, (23, 25, 27))
            angles['R Knee'] = calculate_joint_angle(landmarks, (24, 26, 28))
        except:
            pass
        
        return angles
    
    def _add_annotations(
        self,
        frame: np.ndarray,
        phase: str,
        frame_idx: int,
        width: int,
        height: int,
        phase_banner_colors: Optional[Dict[str, Tuple[int, int, int]]] = None,
        phase_fault_labels: Optional[Dict[str, List[str]]] = None,
    ) -> np.ndarray:
        """Add phase label, angles, per-phase fault text, and frame counter"""
        scale = min(width, height) / 160.0
        
        # Phase label
        label_h = int(35 * scale)
        font_s = 0.4 * scale
        thick = max(1, int(2 * scale))

        # Pick border color based on phase severity (if provided)
        border_color = (0, 255, 0)
        if phase_banner_colors and phase in phase_banner_colors:
            border_color = phase_banner_colors[phase]

        cv2.rectangle(frame, (3, 3), (width-3, label_h), (0, 0, 0), -1)
        cv2.rectangle(frame, (3, 3), (width-3, label_h), border_color, 2)
        cv2.putText(frame, phase, (int(5*scale), int(25*scale)),
                   cv2.FONT_HERSHEY_DUPLEX, font_s, border_color, thick)
        
        # Phase-specific faults (short text under the header)
        if phase_fault_labels:
            labels = phase_fault_labels.get(phase) or []
            if labels:
                fault_y = label_h + int(12 * scale)
                fault_font = 0.3 * scale
                fault_thick = max(1, int(1 * scale))
                for idx, text in enumerate(labels):
                    y = min(height - int(60 * scale), fault_y + int(14 * scale) * idx)
                    cv2.putText(
                        frame,
                        text,
                        (int(5 * scale), y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        fault_font,
                        (255, 255, 255),
                        fault_thick,
                    )
        
        # Angles (if available)
        if hasattr(self, '_current_angles'):
            y_pos = height - int(45 * scale)
            line_h = int(10 * scale)
            small_f = 0.25 * scale
            small_t = max(1, int(1 * scale))
            
            for idx, (name, angle) in enumerate(self._current_angles.items()):
                color = (0, 255, 0) if 'Elbow' in name else (0, 255, 255)
                cv2.putText(frame, f"{name}:{angle:.0f}",
                           (3, y_pos + line_h * idx),
                           cv2.FONT_HERSHEY_SIMPLEX, small_f, color, small_t)
        
        # Frame counter
        cv2.putText(frame, f"#{frame_idx}",
                   (width - int(30*scale), height - int(3*scale)),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.25*scale, (150,150,150),
                   max(1, int(1*scale)))
        
        return frame

    def _add_ball_overlay(
        self,
        frame: np.ndarray,
        frame_idx: int,
        ball_by_frame: Dict[int, BallTrajectoryPoint],
        tail_length: int = 10,
    ) -> np.ndarray:
        """
        Draw ball position and a short tail of previous positions.
        """
        height, width = frame.shape[:2]

        # Current point
        pt = ball_by_frame.get(frame_idx)
        if not pt or pt.x is None or pt.y is None:
            return frame

        # Convert from float pixel coords
        x = int(np.clip(pt.x, 0, width - 1))
        y = int(np.clip(pt.y, 0, height - 1))

        # Draw current ball position (bright yellow)
        cv2.circle(frame, (x, y), 6, (0, 255, 255), -1)

        # Draw tail of previous positions
        for offset in range(1, tail_length + 1):
            prev_idx = frame_idx - offset
            prev_pt = ball_by_frame.get(prev_idx)
            if not prev_pt or prev_pt.x is None or prev_pt.y is None:
                continue

            px = int(np.clip(prev_pt.x, 0, width - 1))
            py = int(np.clip(prev_pt.y, 0, height - 1))

            # Fade color with age
            alpha = max(0.2, 1.0 - offset / float(tail_length + 1))
            color = (0, int(255 * alpha), int(255 * alpha))
            cv2.circle(frame, (px, py), 4, color, -1)

        return frame
    
    def _get_phase_at_frame(self, frame_idx: int, phase_ranges: Dict) -> str:
        """Get phase name for a specific frame"""
        for phase_name, (start, end) in phase_ranges.items():
            if start <= frame_idx <= end:
                return phase_name
        return "UNKNOWN"

    # ------------------------------------------------------------------
    # Fault callout body-region map
    # Maps fragments of fault titles → lists of MediaPipe landmark indices
    # that define the bounding box for the callout rectangle.
    # ------------------------------------------------------------------
    _FAULT_REGION_MAP: Dict[str, List[int]] = {
        # Arms
        "Right Arm":       [12, 14, 16],   # R shoulder, R elbow, R wrist
        "Left Arm":        [11, 13, 15],   # L shoulder, L elbow, L wrist
        "Arm Collapse":    [12, 14, 16],
        # Shoulders
        "Shoulder":        [11, 12],
        "Shoulder Tilt":   [11, 12],
        "Shoulder Plane":  [11, 12],
        # Hips
        "Hip":             [23, 24],
        "Hip Rotation":    [23, 24],
        "Early Extension": [23, 24, 11, 12],
        # Spine / posture
        "Spine":           [11, 12, 23, 24],
        "Forward Bend":    [11, 12, 23, 24],
        "Posture":         [11, 12, 23, 24],
        # Knees
        "Knee":            [25, 26],
        "Early Extension": [25, 26, 23, 24],
        # Wrists / club
        "Wrist":           [15, 16],
        "Club":            [15, 16],
        # Head
        "Head":            [0, 7, 8],
        "Eye":             [1, 4],
    }

    def _draw_fault_callouts(
        self,
        frame: np.ndarray,
        faults: List[Dict],
        landmarks: Optional[np.ndarray],
        scale: float = 1.0,
    ) -> np.ndarray:
        """
        Draw semi-transparent colored bounding boxes around the body regions
        associated with critical/major faults.

        Args:
            frame: BGR image to annotate (modified in-place copy returned)
            faults: list of fault dicts (keys: severity, title)
            landmarks: (N, 4) array of normalised [x, y, z, visibility] coords
            scale: UI scale factor matching _add_annotations
        """
        if not faults or landmarks is None or landmarks.shape[0] == 0:
            return frame

        h, w = frame.shape[:2]
        overlay = frame.copy()

        SEVERITY_COLOR = {
            "critical": (0, 0, 220),    # red (BGR)
            "major":    (0, 140, 255),  # orange
            "minor":    (0, 210, 255),  # yellow
        }
        SEVERITY_ALPHA = {"critical": 0.35, "major": 0.3, "minor": 0.25}
        PAD = int(18 * scale)

        for fault in faults:
            sev = (fault.get("severity") or "").lower()
            if sev not in SEVERITY_COLOR:
                continue
            title = fault.get("title") or ""

            # Find the best matching region
            indices: List[int] = []
            for keyword, lm_indices in self._FAULT_REGION_MAP.items():
                if keyword.lower() in title.lower():
                    indices = lm_indices
                    break
            if not indices:
                # Fallback: full upper body
                indices = [11, 12, 23, 24]

            # Gather pixel coords for region
            xs, ys = [], []
            for idx in indices:
                if 0 <= idx < landmarks.shape[0]:
                    vis = landmarks[idx][3] if landmarks.shape[1] > 3 else 1.0
                    if vis > 0.3:
                        xs.append(int(landmarks[idx][0] * w))
                        ys.append(int(landmarks[idx][1] * h))

            if not xs:
                continue

            x1 = max(0, min(xs) - PAD)
            y1 = max(0, min(ys) - PAD)
            x2 = min(w - 1, max(xs) + PAD)
            y2 = min(h - 1, max(ys) + PAD)

            color = SEVERITY_COLOR[sev]
            alpha = SEVERITY_ALPHA[sev]

            # Filled semi-transparent rectangle
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
            overlay = frame.copy()  # reset overlay for next fault

            # Border
            border_thick = max(2, int(2 * scale))
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, border_thick)

            # Label pill: "[SEV] Title (truncated)"
            label = f"[{sev.upper()}] {title[:28]}"
            font_scale = 0.35 * scale
            font_thick = max(1, int(1 * scale))
            (tw, th), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thick
            )
            lx = x1
            ly = max(th + 6, y1 - 4)
            cv2.rectangle(frame, (lx, ly - th - 4), (lx + tw + 8, ly + 2), color, -1)
            cv2.putText(
                frame, label,
                (lx + 4, ly),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                (255, 255, 255), font_thick, cv2.LINE_AA,
            )

        return frame

    def extract_phase_screenshots(
        self,
        video_path: str,
        output_dir: str,
        phase_ranges: Dict[str, Tuple[int, int]],
        faults_by_phase: Optional[Dict[str, List[Dict]]] = None,
        max_resolution: int = 1080,
    ) -> Dict[str, str]:
        """
        Extract one annotated screenshot per swing phase.

        For each phase the method seeks to the middle frame, draws the pose
        skeleton, phase banner, and fault callout boxes around the affected
        body region, then saves a PNG to output_dir.

        Args:
            video_path:      Input video path
            output_dir:      Directory to save PNGs
            phase_ranges:    Dict mapping phase name → (start_frame, end_frame)
            faults_by_phase: Optional dict mapping phase → list of fault dicts
            max_resolution:  Max height; larger videos are downscaled

        Returns:
            Dict mapping phase name → absolute PNG path (missing phases omitted)
        """
        from pathlib import Path
        output_dir = Path(output_dir)

        cap = cv2.VideoCapture(str(video_path))
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Same scale logic as create_annotated_video
        if width < 640:
            scale_factor = 640 / width
        elif height > max_resolution:
            scale_factor = max_resolution / height
        else:
            scale_factor = 1.0

        out_w = int(width  * scale_factor)
        out_h = int(height * scale_factor)
        ui_scale = min(out_w, out_h) / 160.0

        pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=1,
            min_detection_confidence=0.5,
        )

        saved: Dict[str, str] = {}

        PHASE_ORDER = ["ADDRESS", "BACKSWING", "TOP", "DOWNSWING", "IMPACT", "FOLLOW_THROUGH"]

        # Precompute banner colors
        severity_to_color = {
            "none":     (0, 200, 80),
            "minor":    (0, 215, 255),
            "major":    (0, 140, 255),
            "critical": (0, 0, 220),
        }
        severity_emoji = {"critical": "[CRIT]", "major": "[MAJOR]", "minor": "[MINOR]"}
        phase_banner_colors: Dict[str, Tuple[int, int, int]] = {}
        phase_fault_labels:  Dict[str, List[str]]            = {}
        if faults_by_phase:
            for pname, pfaults in faults_by_phase.items():
                counts = {"critical": 0, "major": 0, "minor": 0}
                labels: List[str] = []
                for f in (pfaults or []):
                    s = (f.get("severity") or "").lower()
                    if s in counts:
                        counts[s] += 1
                    t = f.get("title")
                    if t:
                        labels.append(f"{severity_emoji.get(s, '')} {t}")
                max_sev = "none"
                for s in ("critical", "major", "minor"):
                    if counts[s] > 0:
                        max_sev = s
                        break
                phase_banner_colors[pname] = severity_to_color[max_sev]
                phase_fault_labels[pname]  = labels[:2]

        try:
            for phase in PHASE_ORDER:
                if phase not in phase_ranges:
                    continue
                start, end = phase_ranges[phase]
                phase_span = max(0, end - start)
                if phase == "ADDRESS":
                    # Favor an earlier stable frame so the screenshot does not
                    # drift into the takeaway on clips with very short setup holds.
                    mid_frame = start + int(phase_span * 0.25)
                else:
                    mid_frame = (start + end) // 2

                # Seek to mid frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
                ret, frame = cap.read()
                if not ret or frame is None:
                    continue

                # Resize
                if scale_factor != 1.0:
                    frame = cv2.resize(
                        frame, (out_w, out_h), interpolation=cv2.INTER_CUBIC
                    )

                # Track landmarks for callouts
                current_landmarks: Optional[np.ndarray] = None

                # Pose overlay
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(rgb)
                if results.pose_landmarks:
                    self.mp_drawing.draw_landmarks(
                        frame,
                        results.pose_landmarks,
                        self.mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=self.mp_style.get_default_pose_landmarks_style(),
                    )
                    current_landmarks = extract_landmarks_from_mediapipe(
                        results.pose_landmarks, self.mp_pose
                    )
                    self._current_angles = self._calculate_angles(current_landmarks)

                # Phase banner + fault text labels
                frame = self._add_annotations(
                    frame, phase, mid_frame, out_w, out_h,
                    phase_banner_colors=phase_banner_colors,
                    phase_fault_labels=phase_fault_labels,
                )

                # Fault callout boxes (body region highlights)
                if faults_by_phase and current_landmarks is not None:
                    phase_faults = faults_by_phase.get(phase) or []
                    frame = self._draw_fault_callouts(
                        frame, phase_faults, current_landmarks, scale=ui_scale
                    )

                # Add "Phase Screenshot" watermark in bottom-right corner
                wm_text = f"Frame {mid_frame}  |  {phase.replace('_', ' ')}"
                wm_scale = 0.28 * ui_scale
                wm_thick = max(1, int(1 * ui_scale))
                (tw, th), _ = cv2.getTextSize(
                    wm_text, cv2.FONT_HERSHEY_SIMPLEX, wm_scale, wm_thick
                )
                cv2.rectangle(
                    frame,
                    (out_w - tw - 10, out_h - th - 10),
                    (out_w - 2, out_h - 2),
                    (0, 0, 0), -1,
                )
                cv2.putText(
                    frame, wm_text,
                    (out_w - tw - 6, out_h - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, wm_scale,
                    (180, 180, 180), wm_thick, cv2.LINE_AA,
                )

                png_name = f"phase_{phase}.png"
                png_path = output_dir / png_name
                cv2.imwrite(str(png_path), frame)
                saved[phase] = str(png_path)

        finally:
            cap.release()
            pose.close()

        print(f"📸 Saved {len(saved)} phase screenshots to {output_dir}")
        return saved
    
    def _reencode_video(self, video_path: str) -> str:
        """Re-encode video for better compatibility"""
        try:
            import shutil
            if shutil.which("ffmpeg"):
                reencoded_path = video_path.replace(".mp4", "_final.mp4")
                cmd = [
                    "ffmpeg", "-y", "-i", video_path,
                    "-vcodec", "libx264", "-crf", "23", "-preset", "fast",
                    "-pix_fmt", "yuv420p",
                    reencoded_path
                ]
                
                print("🔄 Re-encoding for compatibility...")
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    print(f"✅ Final video: {reencoded_path}")
                    return reencoded_path
                else:
                    print("⚠️  Re-encoding failed, using original video")
            else:
                print("⚠️  ffmpeg not found, skipping re-encoding")
        except Exception as e:
            print(f"⚠️  Re-encoding error: {e}")
        
        return video_path
    
    def create_video_from_images(
        self,
        image_files: list,
        output_path: str,
        phase_ranges: Dict[str, Tuple[int, int]],
        fps: int = 30,
        show_pose: bool = True
    ) -> str:
        """
        Create annotated video from image sequence
        
        Args:
            image_files: List of image file paths
            output_path: Output video path
            phase_ranges: Dict of phase ranges
            fps: Frame rate for output video
            show_pose: Whether to show pose skeleton
        
        Returns:
            Path to output video
        """
        print(f"\n🎬 Creating annotated video from images...")
        
        # Get frame size from first image
        first_frame = cv2.imread(str(image_files[0]))
        height, width = first_frame.shape[:2]
        
        # Upscale if needed
        scale_factor = self.calculate_upscale_factor(width)
        output_width = int(width * scale_factor)
        output_height = int(height * scale_factor)
        
        if scale_factor > 1.0:
            print(f"   Upscaling from {width}x{height} to {output_width}x{output_height}")
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (output_width, output_height))
        
        pose = self.mp_pose.Pose(static_image_mode=True, model_complexity=2) if show_pose else None
        
        try:
            for idx, img_file in enumerate(_safe_tqdm(image_files, desc="Rendering video")):
                frame = cv2.imread(str(img_file))
                if frame is None:
                    continue
                
                # Upscale if needed
                if scale_factor != 1.0:
                    frame = cv2.resize(frame, (output_width, output_height),
                                     interpolation=cv2.INTER_CUBIC)
                
                # Add pose overlay
                if show_pose and pose:
                    frame = self._add_pose_overlay(frame, pose)
                
                # Get current phase
                phase = self._get_phase_at_frame(idx, phase_ranges)
                
                # Add annotations (no per-phase fault overlays for image sequence)
                frame = self._add_annotations(
                    frame,
                    phase,
                    idx,
                    output_width,
                    output_height,
                    phase_banner_colors=None,
                    phase_fault_labels=None,
                )
                
                out.write(frame)
        finally:
            out.release()
            if pose:
                pose.close()
        
        print(f"\n💾 Saved: {output_path}")
        return str(output_path)
