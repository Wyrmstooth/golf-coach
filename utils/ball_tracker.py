"""
Ball tracking and trajectory construction for Module 3.

This module uses a BallDetector to track the golf ball across a short
time window around the IMPACT phase and produces a smoothed 2D
trajectory plus basic quality metrics.

Key design:
  - Full-frame detection runs FIRST (reliable across varied resolutions/FPS)
  - Crop-based Kalman detection is used as refinement, not sole tracker
  - Kalman resets when no detections for N consecutive frames (prevents drift)
  - Total time budget and per-frame timeout prevent hanging on production
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from scipy.ndimage import gaussian_filter1d

from models.ball_detector import BallDetector, BallDetection


@dataclass
class BallTrajectoryPoint:
    frame: int
    t_sec: float
    x: Optional[float]
    y: Optional[float]
    confidence: float


class BallTracker:
    """
    Track the golf ball in a short window around the IMPACT phase.

    Processes every frame around impact using the ball detector.
    Falls back gracefully when detections are sparse.
    Includes timeouts to prevent production hangs on CPU.
    """

    def __init__(
        self,
        window_before_impact: int = 5,
        window_after_impact: int = 70,
        min_confidence: float = 0.4,
        max_interpolation_gap: int = 5,
    ) -> None:
        self.window_before_impact = int(window_before_impact)
        self.window_after_impact = int(window_after_impact)
        self.min_confidence = float(min_confidence)
        self.max_interpolation_gap = int(max_interpolation_gap)

        # Safety limits to prevent infinite processing on production
        self.max_total_frames = 150          # hard cap on frames processed per video
        self.frame_timeout_sec = 8.0         # skip frame if detection takes longer
        self.total_time_budget_sec = 180.0   # abort if total tracking exceeds this
        self.max_consecutive_misses = 15     # stop early if ball lost for this many frames

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def track(
        self,
        video_path: str,
        impact_range: Tuple[int, int],
        fps: float,
        detector: BallDetector,
    ) -> Tuple[List[BallTrajectoryPoint], Dict[str, float]]:
        """
        Track ball trajectory around the IMPACT phase.

        Args:
            video_path: Path to video file.
            impact_range: (start_frame, end_frame) of IMPACT phase.
            fps: Video frames per second (used for time labels and motion scaling).
            detector: Configured BallDetector instance.

        Returns:
            (trajectory_points, quality_metrics) — coordinates are in
            original video pixel space regardless of any internal scaling.
        """
        import time as _time

        path = Path(video_path)
        if not path.exists():
            return [], {"status": "video_not_found"}

        cap = cv2.VideoCapture(str(path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if fps <= 0:
            fps = 30.0

        impact_start, impact_end = impact_range
        start_frame = max(0, impact_start - self.window_before_impact)
        end_frame = min(total_frames - 1, impact_end + self.window_after_impact)

        # Apply hard frame cap
        num_to_process = end_frame - start_frame + 1
        if num_to_process > self.max_total_frames:
            end_frame = start_frame + self.max_total_frames - 1
            end_frame = min(end_frame, total_frames - 1)
            num_to_process = end_frame - start_frame + 1

        print(f"   Ball tracking: frames {start_frame}-{end_frame} ({num_to_process} frames) @ {fps:.0f} fps")

        # Adaptive downscale for very large frames (4K+).
        # Ball detection works best when the ball occupies ~10-30px.
        max_process_dim = 1280
        scale_factor = 1.0
        if max(original_width, original_height) > max_process_dim:
            scale_factor = max_process_dim / max(original_width, original_height)

        if scale_factor != 1.0:
            print(f"   Downscaling {original_width}x{original_height} → "
                  f"{int(original_width*scale_factor)}x{int(original_height*scale_factor)} "
                  f"for ball detection")

        # Reset detector (Kalman filter) for fresh video
        if hasattr(detector, 'reset'):
            detector.reset()

        # Expose adaptive crop size to the detector based on resolution
        effective_width = int(original_width * scale_factor) if scale_factor < 1.0 else original_width
        effective_height = int(original_height * scale_factor) if scale_factor < 1.0 else original_height
        adaptive_crop = max(200, min(500, effective_width // 4))
        if hasattr(detector, 'set_adaptive_crop'):
            detector.set_adaptive_crop(adaptive_crop)

        trajectory: List[BallTrajectoryPoint] = []
        tracker_start_time = _time.time()
        consecutive_misses = 0
        last_detection_frame = start_frame

        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            current_frame = start_frame

            while current_frame <= end_frame:
                # ── Time budget check ──
                elapsed = _time.time() - tracker_start_time
                if elapsed > self.total_time_budget_sec:
                    print(f"   ⚠️  Total time budget ({self.total_time_budget_sec}s) exceeded at frame {current_frame}")
                    break

                # ── Early termination: ball lost for too long ──
                if consecutive_misses >= self.max_consecutive_misses:
                    print(f"   ⚠️  Ball lost for {consecutive_misses}+ frames — stopping early")
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                # ── Downscale for detection ──
                if scale_factor < 1.0:
                    proc_frame = cv2.resize(
                        frame, (int(original_width * scale_factor), int(original_height * scale_factor)),
                        interpolation=cv2.INTER_AREA,
                    )
                else:
                    proc_frame = frame

                # ── Per-frame detection with timeout ──
                detections: List[BallDetection] = []
                det_start = _time.time()
                try:
                    detections = detector.detect(proc_frame)
                except Exception as e:
                    print(f"   ⚠️  Detection error at frame {current_frame}: {e}")
                    detections = []

                det_elapsed = _time.time() - det_start
                if det_elapsed > 2.0:
                    print(f"   Slow frame {current_frame}: detection took {det_elapsed:.1f}s")

                # ── Build trajectory point ──
                if detections and detections[0].confidence >= self.min_confidence:
                    best = detections[0]
                    inv_scale = 1.0 / scale_factor if scale_factor < 1.0 else 1.0
                    point = BallTrajectoryPoint(
                        frame=current_frame,
                        t_sec=current_frame / fps,
                        x=best.x * inv_scale,
                        y=best.y * inv_scale,
                        confidence=best.confidence,
                    )
                    consecutive_misses = 0
                    last_detection_frame = current_frame
                else:
                    point = BallTrajectoryPoint(
                        frame=current_frame,
                        t_sec=current_frame / fps,
                        x=None,
                        y=None,
                        confidence=0.0,
                    )
                    consecutive_misses += 1

                trajectory.append(point)
                current_frame += 1

        finally:
            cap.release()

        elapsed_total = _time.time() - tracker_start_time

        if not trajectory:
            return [], {"status": "no_frames"}

        # Smooth, interpolate, and compute quality
        smoothed = self._smooth_and_interpolate(trajectory)
        quality = self._compute_quality_metrics(smoothed)
        quality["_elapsed_sec"] = round(float(elapsed_total), 1)

        detected_count = sum(1 for p in smoothed if p.x is not None)
        print(f"   Ball tracking done: {detected_count}/{len(smoothed)} frames "
              f"detected in {elapsed_total:.1f}s "
              f"(detection rate {quality.get('detection_rate', 0):.0%})")

        return smoothed, quality

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _smooth_and_interpolate(
        self,
        points: List[BallTrajectoryPoint],
    ) -> List[BallTrajectoryPoint]:
        """Gaussian smoothing + short-gap interpolation for x/y."""
        frames = np.array([p.frame for p in points], dtype=np.int32)
        xs = np.array(
            [np.nan if p.x is None else p.x for p in points], dtype=np.float32
        )
        ys = np.array(
            [np.nan if p.y is None else p.y for p in points], dtype=np.float32
        )

        xs_filled = self._interpolate_short_gaps(frames, xs)
        ys_filled = self._interpolate_short_gaps(frames, ys)

        # Apply gentle smoothing — adapt sigma to trajectory length
        sigma = 1.0 if len(xs_filled) < 50 else 1.5
        if len(xs_filled) > 3:
            xs_smooth = gaussian_filter1d(xs_filled, sigma=sigma)
            ys_smooth = gaussian_filter1d(ys_filled, sigma=sigma)
        else:
            xs_smooth = xs_filled
            ys_smooth = ys_filled

        smoothed: List[BallTrajectoryPoint] = []
        for i, p in enumerate(points):
            x_val = float(xs_smooth[i]) if not np.isnan(xs_smooth[i]) else None
            y_val = float(ys_smooth[i]) if not np.isnan(ys_smooth[i]) else None
            conf = p.confidence

            smoothed.append(
                BallTrajectoryPoint(
                    frame=p.frame,
                    t_sec=p.t_sec,
                    x=x_val,
                    y=y_val,
                    confidence=conf,
                )
            )

        return smoothed

    def _interpolate_short_gaps(
        self,
        frames: np.ndarray,
        values: np.ndarray,
    ) -> np.ndarray:
        """Interpolate through gaps up to max_interpolation_gap frames."""
        arr = values.copy()
        isnan = np.isnan(arr)
        if not isnan.any():
            return arr

        idx = np.arange(len(arr))
        gap_starts: List[int] = []
        gap_ends: List[int] = []
        in_gap = False

        for i, is_missing in enumerate(isnan):
            if is_missing and not in_gap:
                in_gap = True
                gap_starts.append(i)
            elif not is_missing and in_gap:
                in_gap = False
                gap_ends.append(i - 1)

        if in_gap:
            gap_ends.append(len(arr) - 1)

        for start, end in zip(gap_starts, gap_ends):
            gap_len = end - start + 1
            if gap_len > self.max_interpolation_gap:
                continue

            left_idx = start - 1
            right_idx = end + 1
            if left_idx < 0 or right_idx >= len(arr):
                continue
            if np.isnan(arr[left_idx]) or np.isnan(arr[right_idx]):
                continue

            x0, x1 = frames[left_idx], frames[right_idx]
            y0, y1 = arr[left_idx], arr[right_idx]
            for i in range(start, end + 1):
                xi = frames[i]
                t = (xi - x0) / max((x1 - x0), 1e-6)
                arr[i] = y0 + t * (y1 - y0)

        return arr

    def _compute_quality_metrics(
        self,
        points: List[BallTrajectoryPoint],
    ) -> Dict[str, float]:
        """Basic quality metrics for the tracked trajectory."""
        if not points:
            return {"status": "empty"}

        has_detection = [p.x is not None and p.y is not None for p in points]
        total = len(points)
        detected = sum(has_detection)

        detection_rate = detected / max(total, 1)

        longest_gap = 0
        current_gap = 0
        for ok in has_detection:
            if ok:
                longest_gap = max(longest_gap, current_gap)
                current_gap = 0
            else:
                current_gap += 1
        longest_gap = max(longest_gap, current_gap)

        avg_conf = float(
            np.mean([p.confidence for p in points if p.confidence > 0.0])
        ) if detected > 0 else 0.0

        return {
            "status": "ok" if detected > 0 else "no_detections",
            "detection_rate": float(detection_rate),
            "longest_gap_frames": float(longest_gap),
            "avg_confidence": avg_conf,
            "num_frames": float(total),
        }
