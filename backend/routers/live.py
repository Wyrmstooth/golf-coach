"""
Live router – real-time address posture check and live swing recording.

Endpoints:
  WS   /api/live/address   Per-frame WebSocket: client → base64 JPEG → server → angles + corrections
  POST /api/live/swing     Accept browser-recorded video blob, run full analysis inline
"""
from __future__ import annotations

import base64
import json
import sys
import os
import tempfile
import traceback
from pathlib import Path
from typing import Any, Dict

import numpy as np
import cv2
import mediapipe_compat  # patches mp.solutions for MediaPipe 0.10.x  # noqa: F401

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

router = APIRouter()


def _decode_frame(data_uri: str) -> np.ndarray | None:
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


def _check_address_posture_frame(frame: np.ndarray) -> Dict[str, Any]:
    """
    Run MediaPipe Pose + AddressPoseCorrector on a single BGR frame.
    Returns a structured dict of angles, corrections, and overall status.
    """
    import mediapipe as mp
    from golf_coach_app import AddressPoseCorrector  # type: ignore

    mp_pose = mp.solutions.pose
    corrector = AddressPoseCorrector()

    result: Dict[str, Any] = {
        "status": "no_pose",
        "angles": {},
        "corrections": [],
        "overall": "DETECTING...",
    }

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as pose:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if not results.pose_landmarks:
            return result

        feedback = corrector.check_address_posture(results.pose_landmarks)

        result["status"] = "ok"
        result["angles"] = feedback.get("angles", {})
        result["corrections"] = feedback.get("corrections", [])
        result["overall"] = (
            "GOOD ADDRESS" if not feedback.get("corrections") else "NEEDS ADJUSTMENT"
        )

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


@router.post("/live/swing")
async def live_swing(file: UploadFile = File(...)) -> Any:
    """
    Accept a browser-recorded video blob (webm/mp4), run full MLSwingAnalyzer
    analysis, and return the report inline (identical shape to /api/report/:id).
    """
    suffix = Path(file.filename or "swing.mp4").suffix.lower()
    allowed = {".mp4", ".webm", ".mov", ".avi"}
    if suffix not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{suffix}'. Allowed: {allowed}",
        )

    # Save to a temp file
    tmp_dir = tempfile.mkdtemp()
    video_path = os.path.join(tmp_dir, f"swing{suffix}")
    content = await file.read()
    with open(video_path, "wb") as f:
        f.write(content)

    output_dir = os.path.join(tmp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    try:
        from analyze_video import MLSwingAnalyzer  # type: ignore

        analyzer = MLSwingAnalyzer()
        report = analyzer.analyze_video(
            video_path=video_path,
            output_dir=output_dir,
            verbose=False,
            skip_video_render=False,
        )
        # Embed file contents as base64 for inline delivery (plots only, not video)
        _embed_files(report, output_dir)
        return JSONResponse(content=report)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {traceback.format_exc()}",
        )


def _embed_files(report: Dict[str, Any], output_dir: str) -> None:
    """
    Replace local file paths in report['outputs'] with base64-encoded data URIs
    so the frontend can render them without a separate file-serving endpoint.
    Only applies to PNG plots (MP4 is too large to embed).
    """
    outputs = report.get("outputs", {})
    for key in ("plot", "ball_plot"):
        path = outputs.get(key)
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            outputs[key] = f"data:image/png;base64,{b64}"
