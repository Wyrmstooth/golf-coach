"""
Distance estimation from 2D ball trajectory for Module 3.

This module implements a simple, configuration-driven estimator that
converts pixel-space ball trajectory into approximate carry and total
distance in yards.

Assumptions (documented in FYP-2):
- Single fixed camera, roughly side-on to the shot.
- Ball motion is approximately planar in the image.
- A pixel-to-meter scale factor is provided via config (calibrated using
  known range markers / mat length).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from utils.ball_tracker import BallTrajectoryPoint


@dataclass
class DistanceEstimate:
    carry_yards: float
    distance_yards: float
    confidence: float
    method: str
    notes: str


class DistanceEstimator:
    """
    Lightweight distance estimator based on 2D pixel trajectories.

    This is intentionally approximate but deterministic and easy to
    explain in a thesis setting. For high accuracy, this can be replaced
    with a full camera calibration + 3D trajectory reconstruction.
    """

    def __init__(
        self,
        pixel_to_meter: float = 0.02,
        gravity: float = 9.81,
        min_points: int = 6,
    ) -> None:
        self.pixel_to_meter = float(pixel_to_meter)
        self.gravity = float(gravity)
        self.min_points = int(min_points)

    def estimate(
        self,
        trajectory: List[BallTrajectoryPoint],
        quality_metrics: Optional[Dict[str, float]] = None,
    ) -> Optional[Dict[str, float]]:
        """
        Estimate carry and total distance from pixel trajectory.

        Args:
            trajectory: Smoothed list of BallTrajectoryPoint.
            quality_metrics: Output from BallTracker for confidence calculation.

        Returns:
            Dict with carry/distance in yards + confidence, or None if
            insufficient data.
        """
        if not trajectory:
            return None

        # Extract valid points
        xs = np.array(
            [p.x for p in trajectory if p.x is not None], dtype=np.float32
        )
        ys = np.array(
            [p.y for p in trajectory if p.y is not None], dtype=np.float32
        )
        ts = np.array(
            [p.t_sec for p in trajectory if p.x is not None and p.y is not None],
            dtype=np.float32,
        )

        if len(xs) < self.min_points or len(ys) < self.min_points:
            return None

        # Use image x as horizontal axis; y is vertical (downwards).
        # Convert to meters using a simple scale; flip y so "up" is positive.
        x0 = xs[0]
        y0 = ys[0]

        dx_px = xs - x0
        dy_px = y0 - ys

        dx_m = dx_px * self.pixel_to_meter
        dy_m = dy_px * self.pixel_to_meter

        # Horizontal carry ≈ max horizontal displacement in meters
        carry_m = float(np.max(dx_m) - np.min(dx_m))

        # Total distance: for outdoor shots, rollout adds extra distance.
        # For FYP scope we can model total distance as a fixed multiplier.
        distance_m = carry_m * 1.1  # simple 10% rollout factor

        # Convert to yards
        m_to_yd = 1.09361
        carry_yd = carry_m * m_to_yd
        distance_yd = distance_m * m_to_yd

        # Confidence based on tracker quality + basic sanity checks
        confidence = 0.5
        if quality_metrics:
            det_rate = float(quality_metrics.get("detection_rate", 0.0))
            longest_gap = float(quality_metrics.get("longest_gap_frames", 0.0))
            num_frames = float(quality_metrics.get("num_frames", len(trajectory)))

            # Detection rate is the main driver (0.0–1.0 → 0–0.8)
            confidence = 0.1 + 0.8 * det_rate

            # Penalize very long gaps
            if num_frames > 0:
                gap_ratio = longest_gap / max(num_frames, 1.0)
                confidence *= max(0.3, 1.0 - gap_ratio)

        # Clip confidence to [0, 1] then scale to percentage
        confidence = float(np.clip(confidence, 0.1, 1.0) * 100.0)

        # Basic sanity: clamp unrealistic distances
        carry_yd = float(np.clip(carry_yd, 0.0, 400.0))
        distance_yd = float(np.clip(distance_yd, 0.0, 450.0))

        notes = (
            "vision_only"
            if (quality_metrics and quality_metrics.get("status") == "ok")
            else "vision_low_quality"
        )

        return {
            "carry_yards": carry_yd,
            "distance_yards": distance_yd,
            "confidence": confidence,
            "method": "vision",
            "notes": notes,
        }

