"""
Ball tracking and trajectory construction for Module 3.

This module uses a BallDetector to track the golf ball across a short
time window around the IMPACT phase and produces a smoothed 2D
trajectory plus basic quality metrics.

Robustness layers applied per frame:
  1. Proximity gate — rejects detections >threshold px from expected position
     (searches through lower-confidence candidates for a closer match)
  2. EMA smoothing — exponential moving average of accepted (x,y)
     (eliminates frame-to-frame jitter)
  3. Median filter → Gaussian smoothing in post-processing
     (removes spike outliers after the full pass)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from scipy.ndimage import gaussian_filter1d, median_filter

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
    Applies temporal consistency filters to reject noisy false positives.
    """

    def __init__(
        self,
        window_before_impact: int = 5,
        window_after_impact: int = 70,
        min_confidence: float = 0.3,
        max_interpolation_gap: int = 5,
    ) -> None:
        self.window_before_impact = int(window_before_impact)
        self.window_after_impact = int(window_after_impact)
        self.min_confidence = float(min_confidence)
        self.max_interpolation_gap = int(max_interpolation_gap)

        # Production safety limits
        self.max_total_frames = 150
        self.frame_timeout_sec = 8.0
        self.total_time_budget_sec = 180.0
        self.max_consecutive_misses = 25

        # Temporal consistency (adaptive — scaled to frame width in track())
        self._prox_threshold_base = 0.20    # 20% of frame width — ball can move fast
        self._ema_alpha = 0.30              # smoothing: 0=no change, 1=raw
        self._ema_warmup_frames = 3         # frames before EMA kicks in
        self._reacquire_boost = 5.0         # multiplier on prox threshold when recovering from gap
        self._median_filter_size = 3        # window for post-hoc median filter

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

        num_to_process = end_frame - start_frame + 1
        if num_to_process > self.max_total_frames:
            end_frame = start_frame + self.max_total_frames - 1
            end_frame = min(end_frame, total_frames - 1)
            num_to_process = end_frame - start_frame + 1

        print(f"   Ball tracking: frames {start_frame}-{end_frame} ({num_to_process} frames) @ {fps:.0f} fps")

        # ── Adaptive thresholds ──
        # Proximity gate: ball shouldn't jump more than ~6% of frame width
        # (scaled for FPS — faster videos have smaller inter-frame motion)
        prox_threshold = max(30, min(200, int(original_width * self._prox_threshold_base / max(1, fps / 30.0))))
        reacquire_threshold = prox_threshold * self._reacquire_boost

        # Downscale >1280px for detection speed
        max_process_dim = 1280
        scale_factor = 1.0
        if max(original_width, original_height) > max_process_dim:
            scale_factor = max_process_dim / max(original_width, original_height)

        if scale_factor != 1.0:
            print(f"   Downscaling to {int(original_width*scale_factor)}x{int(original_height*scale_factor)}")

        # Reset detector for fresh video
        if hasattr(detector, 'reset'):
            detector.reset()

        # Adaptive crop for detector
        effective_width = int(original_width * scale_factor) if scale_factor < 1.0 else original_width
        adaptive_crop = max(200, min(500, effective_width // 4))
        if hasattr(detector, 'set_adaptive_crop'):
            detector.set_adaptive_crop(adaptive_crop)

        trajectory: List[BallTrajectoryPoint] = []
        tracker_start_time = _time.time()
        consecutive_misses = 0

        # EMA state and previous accepted position
        ema_x: Optional[float] = None
        ema_y: Optional[float] = None
        prev_accepted_x: Optional[float] = None
        prev_accepted_y: Optional[float] = None

        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            current_frame = start_frame

            while current_frame <= end_frame:
                elapsed = _time.time() - tracker_start_time
                if elapsed > self.total_time_budget_sec:
                    print(f"   ⚠️  Time budget exceeded at frame {current_frame}")
                    break
                if consecutive_misses >= self.max_consecutive_misses:
                    print(f"   ⚠️  Ball lost for {consecutive_misses}+ frames — stopping")
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                if scale_factor < 1.0:
                    proc_frame = cv2.resize(
                        frame,
                        (int(original_width * scale_factor), int(original_height * scale_factor)),
                        interpolation=cv2.INTER_AREA,
                    )
                else:
                    proc_frame = frame

                # Detect
                detections: List[BallDetection] = []
                try:
                    detections = detector.detect(proc_frame)
                except Exception as e:
                    print(f"   ⚠️  Detection error at frame {current_frame}: {e}")

                # ── Temporal consistency: prefer detection near expected position ──
                accepted_det: Optional[BallDetection] = None
                inv_scale = 1.0 / scale_factor if scale_factor < 1.0 else 1.0
                is_jump = False  # track if we accepted a far-away detection

                # Scale all candidates to original pixel space
                for d in detections:
                    d.x *= inv_scale
                    d.y *= inv_scale

                # Filter to candidates above min confidence
                candidates = [d for d in detections if d.confidence >= self.min_confidence]

                if candidates and prev_accepted_x is not None and consecutive_misses < 3:
                    # ── Proximity-aware selection: prefer near, but don't reject far ──
                    candidates.sort(key=lambda d: d.confidence, reverse=True)

                    # Adjust threshold: larger when recovering from a gap
                    use_thresh = reacquire_threshold if consecutive_misses > 0 else prox_threshold

                    # Find the closest candidate
                    closest = min(candidates, key=lambda d: np.hypot(d.x - prev_accepted_x, d.y - prev_accepted_y))
                    closest_dist = np.hypot(closest.x - prev_accepted_x, closest.y - prev_accepted_y)

                    if closest_dist <= use_thresh:
                        # Close candidate — use it
                        accepted_det = closest
                    else:
                        # All candidates are far — still accept the closest (ball moved fast)
                        # but flag it so we don't EMA-smooth this jump
                        accepted_det = closest
                        is_jump = True

                elif candidates:
                    # No previous position (or been lost for a while) — accept highest confidence
                    accepted_det = candidates[0]
                # else: no candidates above threshold — leave as None (gap)

                # If NO high-confidence candidates at all, accept any detection above 0.2
                if accepted_det is None and detections:
                    fallback = max(detections, key=lambda d: d.confidence)
                    if fallback.confidence >= 0.2:
                        accepted_det = fallback

                # ── Build trajectory point ──
                if accepted_det is not None:
                    frames_since_start = current_frame - start_frame

                    # EMA smoothing (skip on jumps and during warmup)
                    if (not is_jump and ema_x is not None
                            and frames_since_start >= self._ema_warmup_frames):
                        ema_x = ema_x * (1.0 - self._ema_alpha) + accepted_det.x * self._ema_alpha
                        ema_y = ema_y * (1.0 - self._ema_alpha) + accepted_det.y * self._ema_alpha
                    else:
                        ema_x, ema_y = accepted_det.x, accepted_det.y

                    point = BallTrajectoryPoint(
                        frame=current_frame,
                        t_sec=current_frame / fps,
                        x=ema_x,
                        y=ema_y,
                        confidence=accepted_det.confidence,
                    )
                    prev_accepted_x, prev_accepted_y = ema_x, ema_y
                    consecutive_misses = 0
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

        # Post-process: median filter + gaussian smooth + interpolate
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
        """Median filter → gap interpolation → gaussian smooth."""
        frames = np.array([p.frame for p in points], dtype=np.int32)
        xs = np.array([np.nan if p.x is None else p.x for p in points], dtype=np.float32)
        ys = np.array([np.nan if p.y is None else p.y for p in points], dtype=np.float32)

        # ── Median filter to remove spike outliers ──
        if self._median_filter_size >= 3 and len(xs) > self._median_filter_size:
            mask = ~np.isnan(xs)
            if mask.sum() > self._median_filter_size:
                xs_valid = np.where(mask, xs, 0)
                xs_med = median_filter(xs_valid, size=self._median_filter_size, mode='nearest')
                xs = np.where(mask, xs_med, np.nan)
            mask_y = ~np.isnan(ys)
            if mask_y.sum() > self._median_filter_size:
                ys_valid = np.where(mask_y, ys, 0)
                ys_med = median_filter(ys_valid, size=self._median_filter_size, mode='nearest')
                ys = np.where(mask_y, ys_med, np.nan)

        # ── Gap interpolation ──
        xs_filled = self._interpolate_short_gaps(frames, xs)
        ys_filled = self._interpolate_short_gaps(frames, ys)

        # ── Gaussian smoothing ──
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
            smoothed.append(BallTrajectoryPoint(
                frame=p.frame, t_sec=p.t_sec,
                x=x_val, y=y_val, confidence=p.confidence,
            ))

        return smoothed

    def _interpolate_short_gaps(
        self, frames: np.ndarray, values: np.ndarray,
    ) -> np.ndarray:
        """Interpolate through gaps up to max_interpolation_gap frames."""
        arr = values.copy()
        isnan = np.isnan(arr)
        if not isnan.any():
            return arr

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
        self, points: List[BallTrajectoryPoint],
    ) -> Dict[str, float]:
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

        avg_conf = float(np.mean([p.confidence for p in points if p.confidence > 0.0])) if detected > 0 else 0.0

        return {
            "status": "ok" if detected > 0 else "no_detections",
            "detection_rate": float(detection_rate),
            "longest_gap_frames": float(longest_gap),
            "avg_confidence": avg_conf,
            "num_frames": float(total),
        }
