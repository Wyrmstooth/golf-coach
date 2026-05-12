"""
Ball tracking and trajectory construction for Module 3.

This module uses a BallDetector to track the golf ball across a short
time window around the IMPACT phase and produces a smoothed 2D
trajectory plus basic quality metrics.
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

    The tracker is intentionally simple:
    - Runs the detector on each frame in the window.
    - Picks the highest-confidence detection per frame.
    - Smooths and interpolates the resulting trajectory.
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
            fps: Video frames per second.
            detector: Configured BallDetector instance.

        Returns:
            (trajectory_points, quality_metrics) — coordinates are in
            original video pixel space regardless of any internal scaling.
        """
        path = Path(video_path)
        if not path.exists():
            return [], {"status": "video_not_found"}

        cap = cv2.VideoCapture(str(path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        impact_start, impact_end = impact_range
        start_frame = max(0, impact_start - self.window_before_impact)
        end_frame = min(total_frames - 1, impact_end + self.window_after_impact)

        if fps <= 0:
            fps = 30.0

        # Downscale high-res frames for faster, more accurate detection.
        # The Faster R-CNN model works best on ≤1080p input; running it
        # on 4K frames is slow and detects poorly (tiny objects, huge kernels).
        max_process_dim = 1280
        scale_factor = 1.0
        if max(original_width, original_height) > max_process_dim:
            scale_factor = max_process_dim / max(original_width, original_height)
            process_width = int(original_width * scale_factor)
            process_height = int(original_height * scale_factor)
        else:
            process_width = original_width
            process_height = original_height

        trajectory: List[BallTrajectoryPoint] = []

        # Reset detector state (e.g. Kalman filter) for a fresh video
        if hasattr(detector, 'reset'):
            detector.reset()

        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            current_frame = start_frame

            while current_frame <= end_frame:
                ret, frame = cap.read()
                if not ret:
                    break

                # Downscale for detection if needed
                if scale_factor != 1.0:
                    proc_frame = cv2.resize(
                        frame, (process_width, process_height),
                        interpolation=cv2.INTER_AREA,
                    )
                else:
                    proc_frame = frame

                detections = detector.detect(proc_frame)
                if detections:
                    best: BallDetection = detections[0]
                    # Map detection coordinates back to original pixel space
                    inv_scale = 1.0 / scale_factor if scale_factor != 1.0 else 1.0
                    point = BallTrajectoryPoint(
                        frame=current_frame,
                        t_sec=current_frame / fps,
                        x=best.x * inv_scale,
                        y=best.y * inv_scale,
                        confidence=best.confidence,
                    )
                else:
                    point = BallTrajectoryPoint(
                        frame=current_frame,
                        t_sec=current_frame / fps,
                        x=None,
                        y=None,
                        confidence=0.0,
                    )

                trajectory.append(point)
                current_frame += 1
        finally:
            cap.release()

        if not trajectory:
            return [], {"status": "no_frames"}

        # Smooth and interpolate
        smoothed = self._smooth_and_interpolate(trajectory)
        quality = self._compute_quality_metrics(smoothed)

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

        # Apply gentle smoothing
        if len(xs_filled) > 3:
            xs_smooth = gaussian_filter1d(xs_filled, sigma=1.0)
            ys_smooth = gaussian_filter1d(ys_filled, sigma=1.0)
        else:
            xs_smooth = xs_filled
            ys_smooth = ys_filled

        smoothed: List[BallTrajectoryPoint] = []
        for i, p in enumerate(points):
            x_val = float(xs_smooth[i]) if not np.isnan(xs_smooth[i]) else None
            y_val = float(ys_smooth[i]) if not np.isnan(ys_smooth[i]) else None
            conf = p.confidence
            if conf < self.min_confidence:
                # If we interpolated this point but original confidence was low,
                # treat it as inferred rather than strongly detected.
                conf = float(conf)

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

        # Identify contiguous NaN runs
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

            # Need valid values before and after the gap
            left_idx = start - 1
            right_idx = end + 1
            if left_idx < 0 or right_idx >= len(arr):
                continue
            if np.isnan(arr[left_idx]) or np.isnan(arr[right_idx]):
                continue

            # Linear interpolation in index space
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

        # Longest consecutive gap without a detection
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

