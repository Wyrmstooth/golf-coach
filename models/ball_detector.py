"""
Ball Detection Model

This module provides a factory function `create_ball_detector()` that returns
the appropriate detector based on config. Supported backends:

  - "faster_rcnn" — GolfBallDetector (Faster R-CNN + Kalman Filter)
    Based on: Zhang et al., IEEE SMC 2020
    Repo:     https://github.com/rucv/golf_ball

  - "yolo" — BallDetector (YOLOv8, legacy fallback)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Any

import numpy as np


@dataclass
class BallDetection:
    """Single ball detection in image coordinates."""
    x: float  # center x in pixels
    y: float  # center y in pixels
    width: float  # bounding box width in pixels
    height: float  # bounding box height in pixels
    confidence: float


class BallDetector:
    """
    YOLOv8-based golf ball detector.

    The detector expects a YOLOv8 model trained on a single "ball" class and
    saved as models/ball_detector.pt (default).
    """

    def __init__(
        self,
        model_path: str = "models/ball_detector.pt",
        conf_threshold: float = 0.4,
        iou_threshold: float = 0.45,
        device: str = "auto",
    ) -> None:
        """
        Initialize the detector. The underlying YOLO model is loaded lazily
        on first use so that importing this module does not require ultralytics
        to be installed in every environment.

        Args:
            model_path: Path to YOLOv8 model weights (.pt).
            conf_threshold: Minimum confidence for a detection to be kept.
            iou_threshold: IOU threshold used by YOLO's NMS.
            device: "auto", "cpu", or "cuda".
        """
        self.model_path = Path(model_path)
        self.conf_threshold = float(conf_threshold)
        self.iou_threshold = float(iou_threshold)
        self.device = device

        self._model: Optional[Any] = None

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #

    def _ensure_model_loaded(self) -> None:
        """Load YOLO model if not already loaded."""
        if self._model is not None:
            return

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Ball detector model not found at {self.model_path}. "
                "Train the detector and save weights as models/ball_detector.pt."
            )

        try:
            from ultralytics import YOLO  # type: ignore
        except Exception as e:  # pragma: no cover - runtime dependency
            raise ImportError(
                "ultralytics is required for ball detection. "
                "Install it with 'pip install ultralytics' and make sure PyTorch is installed."
            ) from e

        # Let YOLO handle device selection when device == "auto"
        model = YOLO(str(self.model_path))

        # Configure default prediction parameters
        model.overrides["conf"] = self.conf_threshold
        model.overrides["iou"] = self.iou_threshold

        if self.device != "auto":
            model.to(self.device)

        self._model = model

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #

    def detect(self, frame_bgr: np.ndarray) -> List[BallDetection]:
        """
        Run ball detection on a single BGR frame.

        Args:
            frame_bgr: OpenCV BGR image (H x W x 3).

        Returns:
            List of BallDetection objects sorted by descending confidence.
        """
        self._ensure_model_loaded()

        if frame_bgr is None or frame_bgr.size == 0:
            return []

        height, width = frame_bgr.shape[:2]

        # YOLO accepts numpy arrays directly; it will handle BGR/RGB internally.
        results = self._model.predict(
            source=frame_bgr,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            verbose=False,
        )

        detections: List[BallDetection] = []

        if not results:
            return detections

        # We expect exactly one image per call
        r = results[0]
        if r.boxes is None:
            return detections

        boxes = r.boxes.xywh.cpu().numpy()  # (x_c, y_c, w, h)
        scores = r.boxes.conf.cpu().numpy()

        for (x_c, y_c, w_box, h_box), score in zip(boxes, scores):
            # Filter by minimum size to reduce false positives
            if w_box < 2 or h_box < 2:
                continue

            # Clamp to image bounds to be safe
            x_c = float(np.clip(x_c, 0, width - 1))
            y_c = float(np.clip(y_c, 0, height - 1))

            detections.append(
                BallDetection(
                    x=x_c,
                    y=y_c,
                    width=float(w_box),
                    height=float(h_box),
                    confidence=float(score),
                )
            )

        # Sort by confidence descending
        detections.sort(key=lambda d: d.confidence, reverse=True)
        return detections


# ── Factory ──────────────────────────────────────────────────────────────

def create_ball_detector(config: dict | None = None) -> BallDetector | object:
    """
    Create a ball detector based on module3 config.

    Returns an object with a `detect(frame_bgr) -> List[BallDetection]` method,
    suitable for use with BallTracker.

    Config keys (under module3):
        backend:            "faster_rcnn" (default) or "yolo"
        ball_detection.*    YOLOv8 settings
        faster_rcnn.*       Faster R-CNN settings
    """
    module3_cfg = (config or {}).get("module3", {}) or {}
    backend = module3_cfg.get("backend", "faster_rcnn")

    if backend == "faster_rcnn":
        frcnn_cfg = module3_cfg.get("faster_rcnn", {}) or {}
        try:
            from models.golf_ball_detector import GolfBallDetector
            return GolfBallDetector(
                model_path=frcnn_cfg.get("model_path", "models/golf_ball_frcnn.pt"),
                conf_threshold=frcnn_cfg.get("conf_threshold", 0.5),
                device=frcnn_cfg.get("device", "auto"),
                crop_size=frcnn_cfg.get("crop_size", 300),
                enable_kalman=frcnn_cfg.get("enable_kalman", True),
            )
        except ImportError as e:
            raise ImportError(
                "Faster R-CNN detector requires torch and torchvision. "
                "Install with: pip install torch torchvision"
            ) from e

    elif backend == "yolo":
        yolo_cfg = module3_cfg.get("ball_detection", {}) or {}
        return BallDetector(
            model_path=yolo_cfg.get("model_path", "models/ball_detector.pt"),
            conf_threshold=yolo_cfg.get("conf_threshold", 0.4),
            iou_threshold=yolo_cfg.get("iou_threshold", 0.45),
            device=yolo_cfg.get("device", "auto"),
        )

    raise ValueError(f"Unknown ball detector backend: {backend}. Use 'faster_rcnn' or 'yolo'.")

