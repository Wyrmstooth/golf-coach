"""
Modern Golf Ball Detector — Faster R-CNN + Kalman Filter

Based on the approach from:
  Zhang et al., "Efficient Golf Ball Detection and Tracking Based on
  Convolutional Neural Networks and Kalman Filter", IEEE SMC 2020.
  Repo: https://github.com/rucv/golf_ball

Key innovations from the paper, implemented cleanly with modern PyTorch:
  1. Faster R-CNN (ResNet-50 FPN) for golf ball detection
  2. Crop-based refinement: crop 300×300 around predicted position, re-detect
  3. Kalman filter (constant velocity) for temporal smoothing

This module is a drop-in replacement for the YOLOv8 BallDetector — it exposes
the same detect(frame_bgr) → List[BallDetection] interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from models.ball_detector import BallDetection


# ── Kalman Filter (constant velocity model) ──────────────────────────────

class KalmanBallTracker:
    """
    4-D constant-velocity Kalman filter: state = [x, y, vx, vy].

    Predicts next ball position, which is used to crop a search region
    around the expected location before running detection (crop trick from
    the paper). After detection, the measurement is fed back via update().
    """

    def __init__(
        self,
        process_noise: float = 0.1,
        measurement_noise: float = 0.0001,
    ) -> None:
        # State transition (constant velocity, dt = 1 frame)
        self.F = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ], dtype=np.float64)

        # Observation matrix: we only observe x, y
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
        ], dtype=np.float64)

        self.Q = process_noise * np.eye(4, dtype=np.float64)
        self.R = measurement_noise * np.eye(2, dtype=np.float64)

        # State estimate and covariance
        self.x: np.ndarray = np.zeros(4, dtype=np.float64)
        self.P: np.ndarray = np.eye(4, dtype=np.float64) * 1000.0
        self._initialized = False

    def predict(self) -> Tuple[float, float]:
        """Predict next state. Returns (x_pred, y_pred)."""
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return float(self.x[0]), float(self.x[1])

    def update(self, measurement: Tuple[float, float]) -> None:
        """Incorporate a measurement (x, y)."""
        z = np.array(measurement, dtype=np.float64)
        if not np.isfinite(self.x).all():
            self.reset()
            self.x[0], self.x[1] = z
            self._initialized = True
            return
        y_residual = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        try:
            K = self.P @ self.H.T @ np.linalg.pinv(S)
        except np.linalg.LinAlgError:
            return
        self.x = self.x + K @ y_residual
        self.P = (np.eye(4) - K @ self.H) @ self.P
        self._initialized = True

    @property
    def position(self) -> Tuple[float, float]:
        """Current filtered position."""
        return float(self.x[0]), float(self.x[1])

    def reset(self) -> None:
        """Reset the filter."""
        self.x = np.zeros(4, dtype=np.float64)
        self.P = np.eye(4, dtype=np.float64) * 1000.0
        self._initialized = False


# ── Faster R-CNN Ball Detector ───────────────────────────────────────────

class GolfBallDetector:
    """
    Faster R-CNN + Kalman Filter golf ball detector.

    Uses torchvision's Faster R-CNN with ResNet-50 FPN backbone, fine-tuned
    on golf ball data. Maintains a Kalman filter for temporal tracking and
    uses crop-based refinement for improved small-object detection.

    Usage (drop-in replacement for BallDetector):
        detector = GolfBallDetector(model_path="models/golf_ball_frcnn.pt")
        detections = detector.detect(frame_bgr)
        # detections is List[BallDetection] — same interface
    """

    def __init__(
        self,
        model_path: str = "models/golf_ball_frcnn.pt",
        conf_threshold: float = 0.5,
        device: str = "auto",
        crop_size: int = 300,
        enable_kalman: bool = True,
    ) -> None:
        """
        Args:
            model_path: Path to fine-tuned Faster R-CNN weights (.pt).
            conf_threshold: Minimum confidence score for a detection.
            device: 'auto', 'cpu', or 'cuda'.
            crop_size: Size of the crop window (pixels) around predicted position.
            enable_kalman: Enable Kalman filter for temporal tracking.
        """
        self.model_path = Path(model_path)
        self.conf_threshold = float(conf_threshold)
        self.crop_size = int(crop_size)
        self.enable_kalman = enable_kalman

        if device == "auto":
            self.device = "cuda" if _cuda_available() else "cpu"
        else:
            self.device = device

        self._model: Optional[object] = None
        self._kalman = KalmanBallTracker()
        self._frame_count: int = 0

    # ── Public API ──────────────────────────────────────────────────────

    def detect(self, frame_bgr: np.ndarray) -> List[BallDetection]:
        """
        Run ball detection on a single BGR frame.

        1. Predict next position with Kalman, crop around it, detect.
        2. If no detections in crop, fall back to full-frame detection.
        3. Update Kalman with best detection.
        """
        self._ensure_model_loaded()

        if frame_bgr is None or frame_bgr.size == 0:
            return []

        h, w = frame_bgr.shape[:2]

        # Step 1: Predict next position with Kalman
        if self.enable_kalman and self._kalman._initialized:
            pred_x, pred_y = self._kalman.predict()
        else:
            pred_x, pred_y = None, None  # type: ignore[assignment]

        # Step 2a: Try crop detection first
        results: List[BallDetection] = []
        if pred_x is not None and pred_y is not None:
            crop_frame, offset_x, offset_y = self._crop_around(
                frame_bgr, int(pred_x), int(pred_y), self.crop_size
            )
            try:
                detections = self._detect_on_frame(crop_frame)
                for det in detections:
                    if not (np.isfinite(det.x) and np.isfinite(det.y)):
                        continue
                    results.append(BallDetection(
                        x=det.x + offset_x,
                        y=det.y + offset_y,
                        width=det.width,
                        height=det.height,
                        confidence=det.confidence,
                    ))
                results.sort(key=lambda d: d.confidence, reverse=True)
            except Exception:
                results = []

        # Step 2b: Fall back to full-frame detection if crop missed
        if not results:
            try:
                detections = self._detect_on_frame(frame_bgr)
                results = [BallDetection(
                    x=det.x, y=det.y, width=det.width,
                    height=det.height, confidence=det.confidence,
                ) for det in detections]
                results.sort(key=lambda d: d.confidence, reverse=True)
            except Exception:
                results = []

        # Step 3: Update Kalman with best detection
        if results and self.enable_kalman:
            best = results[0]
            if np.isfinite(best.x) and np.isfinite(best.y):
                self._kalman.update((best.x, best.y))

        self._frame_count += 1
        return results

    def reset(self) -> None:
        """Reset Kalman state (e.g. for a new video)."""
        self._kalman.reset()
        self._frame_count = 0

    # ── Internal ────────────────────────────────────────────────────────

    def _ensure_model_loaded(self) -> None:
        """Lazy-load the Faster R-CNN model."""
        if self._model is not None:
            return

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Golf ball detector model not found at {self.model_path}. "
                "Train with: python training/train_golf_ball_detector.py"
            )

        import torch

        # Two classes: background (0) and golf ball (1)
        from torchvision.models.detection import fasterrcnn_resnet50_fpn
        from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

        model = fasterrcnn_resnet50_fpn(weights=None)
        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes=2)

        checkpoint = torch.load(str(self.model_path), map_location=self.device)
        model.load_state_dict(checkpoint)
        model.to(self.device)
        model.eval()

        self._model = model

    def _detect_on_frame(self, frame_bgr: np.ndarray) -> List[BallDetection]:
        """Run Faster R-CNN on a single BGR frame (or crop)."""
        import torch
        import torchvision.transforms.functional as TF

        # Convert BGR → RGB
        rgb = frame_bgr[:, :, ::-1].copy()
        img_tensor = TF.to_tensor(rgb).to(self.device)

        with torch.no_grad():
            predictions = self._model([img_tensor])[0]

        detections: List[BallDetection] = []
        boxes = predictions["boxes"].cpu().numpy()
        scores = predictions["scores"].cpu().numpy()

        for box, score in zip(boxes, scores):
            if score < self.conf_threshold:
                continue
            x1, y1, x2, y2 = box
            w = x2 - x1
            h = y2 - y1
            # Filter tiny false positives (< 3px either dimension)
            if w < 3 or h < 3:
                continue
            detections.append(BallDetection(
                x=float((x1 + x2) / 2),
                y=float((y1 + y2) / 2),
                width=float(w),
                height=float(h),
                confidence=float(score),
            ))

        detections.sort(key=lambda d: d.confidence, reverse=True)
        return detections

    @staticmethod
    def _crop_around(
        frame: np.ndarray,
        cx: int,
        cy: int,
        size: int,
    ) -> Tuple[np.ndarray, int, int]:
        """
        Crop a size×size region centered at (cx, cy), clamped to image bounds.
        Returns (cropped_frame, offset_x, offset_y).
        """
        h, w = frame.shape[:2]
        half = size // 2

        x1 = max(cx - half, 0)
        y1 = max(cy - half, 0)
        x2 = min(cx + half, w)
        y2 = min(cy + half, h)

        return frame[y1:y2, x1:x2], x1, y1


# ── Helpers ──────────────────────────────────────────────────────────────

def _cuda_available() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False
