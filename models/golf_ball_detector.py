"""
Modern Golf Ball Detector — Faster R-CNN + Kalman Filter

Based on:
  Zhang et al., "Efficient Golf Ball Detection and Tracking Based on
  Convolutional Neural Networks and Kalman Filter", IEEE SMC 2020.
  Repo: https://github.com/rucv/golf_ball

Key features:
  1. Faster R-CNN (ResNet-50 FPN) for golf ball detection
  2. Adaptive crop-based refinement around Kalman-predicted position
  3. Kalman filter (constant velocity) with automatic reset on drift
  4. Robust across varied resolutions (720p to 4K) and frame rates

This module is a drop-in replacement for the YOLOv8 BallDetector:
    detector = GolfBallDetector(model_path="models/golf_ball_frcnn.pt")
    detections = detector.detect(frame_bgr)
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

    Predicts next ball position for crop-based search.
    Auto-resets when state becomes invalid or diverges.
    """

    def __init__(
        self,
        process_noise: float = 0.1,
        measurement_noise: float = 0.0001,
    ) -> None:
        self.F = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ], dtype=np.float64)

        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
        ], dtype=np.float64)

        self.Q = process_noise * np.eye(4, dtype=np.float64)
        self.R = measurement_noise * np.eye(2, dtype=np.float64)

        self.x: np.ndarray = np.zeros(4, dtype=np.float64)
        self.P: np.ndarray = np.eye(4, dtype=np.float64) * 1000.0
        self._initialized = False
        self._consecutive_misses = 0

    def predict(self) -> Tuple[float, float]:
        """Predict next state. Returns (x_pred, y_pred)."""
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return float(self.x[0]), float(self.x[1])

    def update(self, measurement: Tuple[float, float]) -> None:
        """Incorporate a measurement (x, y). Auto-resets if diverged."""
        z = np.array(measurement, dtype=np.float64)
        if not np.isfinite(self.x).all() or not np.isfinite(self.P).all():
            self.reset()
            self.x[0], self.x[1] = z
            self._initialized = True
            return

        y_residual = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        try:
            K = self.P @ self.H.T @ np.linalg.pinv(S)
        except np.linalg.LinAlgError:
            self.reset()
            self.x[0], self.x[1] = z
            self._initialized = True
            return
        self.x = self.x + K @ y_residual
        self.P = (np.eye(4) - K @ self.H) @ self.P
        self._initialized = True
        self._consecutive_misses = 0

    def mark_miss(self) -> None:
        """Signal that no detection was found this frame."""
        self._consecutive_misses += 1

    def should_reset(self, max_consecutive: int = 8) -> bool:
        """Check if the Kalman track has diverged (too many consecutive misses)."""
        return self._consecutive_misses >= max_consecutive

    @property
    def position(self) -> Tuple[float, float]:
        return float(self.x[0]), float(self.x[1])

    @property
    def initialized(self) -> bool:
        return self._initialized and np.isfinite(self.x).all()

    def reset(self) -> None:
        self.x = np.zeros(4, dtype=np.float64)
        self.P = np.eye(4, dtype=np.float64) * 1000.0
        self._initialized = False
        self._consecutive_misses = 0


# ── Faster R-CNN Ball Detector ───────────────────────────────────────────

class GolfBallDetector:
    """
    Faster R-CNN + Kalman Filter golf ball detector.

    Uses torchvision's Faster R-CNN with ResNet-50 FPN backbone, fine-tuned
    on golf ball data. Maintains a Kalman filter for temporal tracking and
    uses adaptive crop-based refinement for improved small-object detection
    across varying video resolutions.
    """

    def __init__(
        self,
        model_path: str = "models/golf_ball_frcnn.pt",
        conf_threshold: float = 0.5,
        device: str = "auto",
        crop_size: int = 300,
        enable_kalman: bool = True,
    ) -> None:
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
        self._det_fail_streak: int = 0  # consecutive frames with no detection

    def set_adaptive_crop(self, size: int) -> None:
        """
        Update crop window size dynamically based on video resolution.
        Larger frames need larger crop (ball is relatively smaller in 4K).
        """
        self.crop_size = max(150, min(600, int(size)))

    # ── Public API ──────────────────────────────────────────────────────

    def detect(self, frame_bgr: np.ndarray) -> List[BallDetection]:
        """
        Run ball detection on a single BGR frame.

        Strategy:
          1. Full-frame detection FIRST (reliable baseline)
          2. If Kalman is initialized AND tracking well, also try crop detection
          3. Merge results, preferring higher confidence
          4. Update Kalman with best detection
          5. Auto-reset Kalman if consecutive misses exceed threshold
        """
        self._ensure_model_loaded()

        if frame_bgr is None or frame_bgr.size == 0:
            return []

        h, w = frame_bgr.shape[:2]

        # ── Step 1: Full-frame detection (baseline) ──
        all_results: List[BallDetection] = []
        try:
            detections = self._detect_on_frame(frame_bgr)
            all_results.extend(detections)
        except Exception:
            pass

        # ── Step 2: Crop-based detection (refinement when Kalman is tracking) ──
        kalman_pred = None
        if self.enable_kalman and self._kalman.initialized and not self._kalman.should_reset():
            pred_x, pred_y = self._kalman.predict()
            pred_x = max(0, min(w - 1, pred_x))
            pred_y = max(0, min(h - 1, pred_y))
            kalman_pred = (pred_x, pred_y)

            crop_frame, offset_x, offset_y = self._crop_around(
                frame_bgr, int(pred_x), int(pred_y), self.crop_size
            )
            try:
                crop_dets = self._detect_on_frame(crop_frame)
                for det in crop_dets:
                    if not (np.isfinite(det.x) and np.isfinite(det.y)):
                        continue
                    world_x = det.x + offset_x
                    world_y = det.y + offset_y
                    # Distance from Kalman prediction — closer = more likely to be the real ball
                    pred_dist = np.hypot(world_x - pred_x, world_y - pred_y)
                    # Crop detections get a confidence bonus inversely proportional to distance
                    # from prediction. Max bonus ~0.15 for detections at the predicted spot.
                    bonus = max(0.0, 0.15 * (1.0 - pred_dist / (self.crop_size * 0.6)))
                    all_results.append(BallDetection(
                        x=world_x,
                        y=world_y,
                        width=det.width,
                        height=det.height,
                        confidence=min(1.0, det.confidence + bonus),
                    ))
            except Exception:
                pass

        # ── Sort by confidence ──
        all_results.sort(key=lambda d: d.confidence, reverse=True)

        # ── Step 3: Update Kalman or reset if track lost ──
        if all_results:
            best = all_results[0]
            if np.isfinite(best.x) and np.isfinite(best.y):
                self._kalman.update((best.x, best.y))
                self._det_fail_streak = 0
            else:
                self._det_fail_streak += 1
                self._kalman.mark_miss()
        else:
            self._det_fail_streak += 1
            self._kalman.mark_miss()

        # Auto-reset Kalman when tracking lost for too long
        if self._kalman.should_reset(max_consecutive=8):
            self._kalman.reset()

        self._frame_count += 1
        return all_results

    def reset(self) -> None:
        """Reset Kalman state for a new video."""
        self._kalman.reset()
        self._frame_count = 0
        self._det_fail_streak = 0

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

        # Check for Git LFS pointer (would crash torch.load())
        file_size = self.model_path.stat().st_size
        if file_size < 1000:
            with open(self.model_path, "rb") as f:
                header = f.read(50)
            if header.strip().startswith(b"version https://git-lfs"):
                raise RuntimeError(
                    f"Ball detector model at {self.model_path} is a Git LFS pointer ({file_size} bytes). "
                    "Download the real model file or set MODEL_URL env var."
                )
            raise RuntimeError(
                f"Ball detector model at {self.model_path} is too small ({file_size} bytes). "
                "The file may be corrupted."
            )

        print(f"   Loading ball detector model ({file_size // 1024 // 1024} MB → {self.device})...")

        import torch

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
            w_box = x2 - x1
            h_box = y2 - y1
            # Filter tiny false positives (< 2px either dimension)
            if w_box < 2 or h_box < 2:
                continue
            detections.append(BallDetection(
                x=float((x1 + x2) / 2),
                y=float((y1 + y2) / 2),
                width=float(w_box),
                height=float(h_box),
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
        Crop a sizexsize region centered at (cx, cy), clamped to image bounds.
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
