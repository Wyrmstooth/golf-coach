"""
Live router – real-time address posture check and live swing recording.

Endpoints:
  WS   /api/live/address   Per-frame WebSocket: client → base64 JPEG → server → angles + corrections + annotated frame
  POST /api/live/swing     Accept browser-recorded video blob, run full analysis inline
"""
from __future__ import annotations

import base64
import json
import sys
import os
import uuid
import tempfile
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import cv2
import mediapipe_compat  # patches mp.solutions for MediaPipe 0.10.x  # noqa: F401
import mediapipe as mp

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

router = APIRouter()

# ── Module-level MediaPipe instances (avoid per-frame init overhead) ─────────
# Creating a new Pose instance every frame is extremely expensive and causes
# the "main thread is not in main loop" tkinter destructor crashes.
_mp_pose = mp.solutions.pose
_mp_drawing = mp.solutions.drawing_utils
_mp_drawing_styles = mp.solutions.drawing_styles
_pose_instance: Optional[Any] = None


def _get_pose() -> Any:
    """Lazy-init a single shared MediaPipe Pose instance."""
    global _pose_instance
    if _pose_instance is None:
        _pose_instance = _mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
    return _pose_instance


def _decode_frame(data_uri: str) -> Optional[np.ndarray]:
    """Decode a base64 data-URI (image/jpeg or image/png) into a BGR numpy array."""
    try:
        if "," in data_uri:
            data_uri = data_uri.split(",", 1)[1]
        img_bytes = base64.b64decode(data_uri)
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return frame
    except Exception:
        return None


def _angle_between(lm: Any, p1: int, p2: int, p3: int) -> float:
    """Compute the angle (degrees) at joint p2 formed by points p1–p2–p3."""
    a = np.array([lm[p1].x, lm[p1].y])
    b = np.array([lm[p2].x, lm[p2].y])
    c = np.array([lm[p3].x, lm[p3].y])
    ba, bc = a - b, c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9)
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))


def _check_address_posture_frame(frame: np.ndarray) -> Dict[str, Any]:
    """
    Run MediaPipe Pose on a single BGR frame.
    - Draws the full skeleton overlay onto a copy of the frame.
    - Calculates spine angle, knee flex, and lead arm angle.
    - Returns corrections, overall status, plus the annotated frame as base64 JPEG.
    """
    result: Dict[str, Any] = {
        "status": "no_pose",
        "angles": {},
        "corrections": [],
        "overall": "DETECTING...",
        "annotated_frame": None,
    }

    pose = _get_pose()

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb.flags.writeable = False
    pose_results = pose.process(rgb)
    rgb.flags.writeable = True

    if not pose_results.pose_landmarks:
        return result

    # ── Draw skeleton overlay ─────────────────────────────────────────────────
    annotated = frame.copy()
    _mp_drawing.draw_landmarks(
        annotated,
        pose_results.pose_landmarks,
        _mp_pose.POSE_CONNECTIONS,
        landmark_drawing_spec=_mp_drawing_styles.get_default_pose_landmarks_style(),
    )
    ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 78])
    if ok:
        result["annotated_frame"] = "data:image/jpeg;base64," + base64.b64encode(buf).decode()

    # ── Calculate posture angles ──────────────────────────────────────────────
    lm = pose_results.pose_landmarks.landmark
    spine_angle = _angle_between(lm, 11, 23, 25)   # shoulder → hip → knee
    left_knee   = _angle_between(lm, 23, 25, 27)
    right_knee  = _angle_between(lm, 24, 26, 28)
    left_arm    = _angle_between(lm, 11, 13, 15)
    avg_knee    = (left_knee + right_knee) / 2

    result["angles"] = {
        "spine":    round(spine_angle, 1),
        "knee":     round(avg_knee, 1),
        "left_arm": round(left_arm, 1),
    }

    # ── Corrections ───────────────────────────────────────────────────────────
    corrections: List[str] = []
    if spine_angle > 165:
        corrections.append("Stand more upright — too much forward tilt")
    elif spine_angle < 150:
        corrections.append("Bend more from the hips — not enough tilt")

    if avg_knee > 170:
        corrections.append("Bend your knees more — stay in an athletic stance")
    elif avg_knee < 130:
        corrections.append("Less knee bend — stance too deep")

    if left_arm < 150:
        corrections.append("Straighten your lead arm")

    result["status"] = "ok"
    result["corrections"] = corrections
    result["overall"] = "GOOD ADDRESS" if not corrections else "NEEDS ADJUSTMENT"

    return result


@router.websocket("/live/address")
async def live_address_ws(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time address posture feedback.

    Protocol:
      Client → JSON: { "frame": "<base64 data-URI>" }
      Server → JSON: { "status", "angles", "corrections", "overall" }
    """
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
                frame_data = payload.get("frame", "")
            except json.JSONDecodeError:
                frame_data = raw

            frame = _decode_frame(frame_data)
            if frame is None:
                await websocket.send_json(
                    {"status": "error", "message": "Could not decode frame."}
                )
                continue

            try:
                feedback = _check_address_posture_frame(frame)
                await websocket.send_json(feedback)
            except Exception as exc:
                await websocket.send_json(
                    {"status": "error", "message": str(exc)}
                )
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass


def _check_video(path: str) -> int:
    """Return frame count if readable, else 0."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return 0
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    cap.release()
    return frames if fps > 0 and width > 0 else 0


def _convert_video(src: str, dst: str) -> bool:
    """Try ffmpeg conversion. Return True on success."""
    import shutil
    import subprocess
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    cmd = [
        ffmpeg, "-y", "-i", src,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        dst,
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        return _check_video(dst) > 0
    except Exception:
        return False


@router.post("/live/swing")
async def live_swing(file: UploadFile = File(...)) -> Any:
    """
    Accept a browser-recorded video blob (webm/mp4), run full MLSwingAnalyzer
    analysis, persist output under output/{job_id}/ and return report + job_id.
    """
    suffix = Path(file.filename or "swing.mp4").suffix.lower()
    allowed = {".mp4", ".webm", ".mov", ".avi"}
    if suffix not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{suffix}'. Allowed: {allowed}",
        )

    job_id = str(uuid.uuid4())
    output_dir = str(ROOT / "output" / job_id)
    os.makedirs(output_dir, exist_ok=True)

    video_path = os.path.join(output_dir, f"input{suffix}")
    content = await file.read()
    with open(video_path, "wb") as f:
        f.write(content)

    # ── Validate / convert video ──────────────────────────────────────────
    frames = _check_video(video_path)
    if frames == 0:
        # Try ffmpeg conversion to MP4
        converted = os.path.join(output_dir, "input_converted.mp4")
        if _convert_video(video_path, converted):
            video_path = converted
            frames = _check_video(video_path)
        if frames == 0:
            raise HTTPException(
                status_code=400,
                detail="Recorded video is unreadable. Try uploading a regular video instead, or use a different browser.",
            )

    from backend.job_store import job_store
    job_store.create(job_id, video_path)
    job_store.update(job_id, output_dir=output_dir)

    try:
        from analyze_video import MLSwingAnalyzer  # type: ignore

        analyzer = MLSwingAnalyzer()
        report = analyzer.analyze_video(
            video_path=video_path,
            output_dir=output_dir,
            verbose=False,
            skip_video_render=False,
        )

        # ── Verify annotated video has content ────────────────────────────
        av_path = report.get("outputs", {}).get("annotated_video")
        if av_path and os.path.exists(av_path):
            av_frames = _check_video(av_path)
            if av_frames == 0:
                report["outputs"]["annotated_video"] = None
                report["outputs"]["annotated_video_data_uri"] = None

        job_store.update(
            job_id,
            status="done",
            progress=100,
            report=report,
            output_dir=output_dir,
        )

        report["_job_id"] = job_id
        return JSONResponse(content=report)
    except Exception:
        job_store.update(job_id, status="error", progress=0, error=traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {traceback.format_exc()}",
        )


