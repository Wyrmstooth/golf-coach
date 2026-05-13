"""
Golf swing phase detection and analysis.

Detects 6-phase golf swing from trajectory data using multi-metric
biomechanical analysis. Adaptive thresholds handle varied video sizes
(720p-4K), frame rates (30-120fps), and swing styles.
"""
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter
from typing import Dict, List, Tuple


class SwingPhaseAnalyzer:
    """Detect golf swing phases using multi-metric biomechanical analysis."""

    def __init__(self):
        pass

    def detect_phases(
        self,
        frame_data: List[Dict],
        smoothing_window: int = 5,
        precheck_window: int = 30,
        threshold_percentile: int = 90,
        fps: float = 30.0,
    ) -> Tuple[Dict[str, Tuple[int, int]], int, int, np.ndarray, np.ndarray]:
        """
        Detect golf swing phases from trajectory data.

        Uses multi-metric analysis: wrist trajectory, hip rotation, shoulder alignment.
        All thresholds adapt to the actual data range — works across resolutions.
        Frame-based windows are scaled to FPS for consistent behavior at any speed.

        Args:
            frame_data: List of dicts with frame_idx, wrist_y, hip_rotation, shoulder_rotation
            smoothing_window: Base window size for smoothing
            precheck_window: Max frames to check for static ADDRESS
            threshold_percentile: Percentile for motion threshold
            fps: Video frame rate (scales frame-based windows)

        Returns:
            phase_ranges, swing_start, swing_end, wrist_y_raw, wrist_y_smoothed
        """
        n_frames = len(frame_data)
        if n_frames < 15:
            last = max(0, n_frames - 1)
            empty_phases = {
                "ADDRESS": (0, last),
                "BACKSWING": (0, last),
                "TOP": (0, last),
                "DOWNSWING": (0, last),
                "IMPACT": (0, last),
                "FOLLOW_THROUGH": (0, last),
            }
            return empty_phases, 0, last, np.array([]), np.array([])

        # Scale frame-based windows to a 30fps reference
        fps_scale = max(0.5, min(3.0, fps / 30.0))

        # ── Extract signals ──
        wrist_y = np.array([
            d.get("wrist_y", np.nan)
            for d in frame_data
        ], dtype=np.float32)
        hip_rot = np.array([
            d.get("hip_rotation", np.nan)
            for d in frame_data
        ], dtype=np.float32)
        shoulder_rot = np.array([
            d.get("shoulder_rotation", np.nan)
            for d in frame_data
        ], dtype=np.float32)

        # ── Adaptive smoothing ──
        # Scale window to video length AND FPS
        base_window = max(3, min(smoothing_window, n_frames // 15))
        adaptive_window = max(3, int(base_window * fps_scale))
        smoothed_wrist = self._prepare_signal(wrist_y, adaptive_window)
        smoothed_hip = self._prepare_signal(hip_rot, adaptive_window)
        smoothed_shoulder = self._prepare_signal(shoulder_rot, adaptive_window)

        # ── Motion energy ──
        motion_energy = self._compute_motion_profile(
            smoothed_wrist,
            smoothed_hip,
            smoothed_shoulder
        )

        # ── Adaptive precheck_window ──
        # Scale by both video length and FPS
        raw_precheck = min(precheck_window, max(5, n_frames // 5))
        adaptive_precheck = max(5, int(raw_precheck * fps_scale))

        # ── Swing window detection ──
        swing_start, swing_end = self._detect_swing_window(
            motion_energy,
            smoothed_wrist,
            adaptive_precheck,
        )

        # ── ADDRESS phase ──
        address_start, address_end = self._find_address_phase(
            smoothed_wrist, swing_start
        )

        # ── TOP phase (backswing peak) ──
        top_range = self._find_top_phase(smoothed_wrist, swing_start, swing_end, wrist_y)

        # ── Address wrist level ──
        address_y_level = float(np.nanmedian(
            smoothed_wrist[:max(1, swing_start)]
        ))

        # ── IMPACT phase ──
        impact_range = self._find_impact_phase(
            smoothed_wrist, top_range, swing_end, address_y_level
        )

        # ── Build phase ranges with ZERO gaps ──
        backswing_end = max(swing_start + 1, top_range[0])
        top_end = max(backswing_end + 1, top_range[1])

        # Downswing: TOP end → impact start
        downswing_start = top_end
        impact_start = impact_range[0]
        downswing_end = max(downswing_start + 1, impact_start)

        # Impact: downswing end → impact end
        impact_end = max(downswing_end + 1, impact_range[1])

        # Follow-through: impact end → swing end (ALWAYS covers to end, NO gaps)
        ft_start = impact_end

        def _safe(a: int, b: int) -> Tuple[int, int]:
            a = int(a)
            b = int(b)
            if b <= a:
                b = a + 1
            return (a, b)

        phase_ranges = {
            "ADDRESS":        _safe(address_start, address_end),
            "BACKSWING":      _safe(swing_start, backswing_end),
            "TOP":            _safe(backswing_end, top_end),
            "DOWNSWING":      _safe(downswing_start, downswing_end),
            "IMPACT":         _safe(downswing_end, impact_end),
            "FOLLOW_THROUGH": _safe(ft_start, swing_end),
        }

        return phase_ranges, swing_start, swing_end, wrist_y, smoothed_wrist

    # ── Signal preprocessing ────────────────────────────────────────────

    def _prepare_signal(self, signal: np.ndarray, smoothing_window: int) -> np.ndarray:
        """Fill gaps and apply combined smoothing for stable detection."""
        if len(signal) == 0:
            return signal
        if len(signal) < 5:
            return self._fill_nans(signal)

        processed = signal.copy()
        processed = self._fill_nans(processed)

        processed = gaussian_filter1d(
            processed, sigma=max(1, smoothing_window // 2), mode='nearest'
        )

        window_length = min(len(processed) // 2 * 2 + 1, max(5, smoothing_window * 2 + 1))
        if window_length >= 5 and len(processed) >= window_length:
            processed = savgol_filter(
                processed, window_length, polyorder=2, mode='interp'
            )

        return processed

    def _fill_nans(self, signal: np.ndarray) -> np.ndarray:
        """Forward/backward fill NaNs to keep trajectories continuous."""
        if np.all(np.isnan(signal)):
            return np.zeros_like(signal)

        mask = np.isnan(signal)
        if mask.any():
            signal[mask] = np.interp(
                np.flatnonzero(mask),
                np.flatnonzero(~mask),
                signal[~mask]
            )
        return signal

    # ── Motion detection ─────────────────────────────────────────────────

    def _compute_motion_profile(
        self,
        wrist: np.ndarray,
        hip: np.ndarray,
        shoulder: np.ndarray,
    ) -> np.ndarray:
        """Combine multi-signal velocities into a single motion energy curve."""
        def _normalize_derivative(arr: np.ndarray) -> np.ndarray:
            if len(arr) < 2:
                return np.zeros_like(arr)
            deriv = np.gradient(arr)
            mad = np.nanmedian(np.abs(deriv - np.nanmedian(deriv))) + 1e-3
            return np.abs(deriv) / mad

        wrist_term = _normalize_derivative(wrist)
        hip_term = _normalize_derivative(hip) if not np.all(np.isnan(hip)) else np.zeros_like(wrist_term)
        shoulder_term = _normalize_derivative(shoulder) if not np.all(np.isnan(shoulder)) else np.zeros_like(wrist_term)

        return wrist_term + 0.5 * hip_term + 0.3 * shoulder_term

    def _detect_swing_window(
        self,
        motion_energy: np.ndarray,
        smoothed_wrist: np.ndarray,
        precheck_window: int,
    ) -> Tuple[int, int]:
        """
        Locate swing start and end frames.

        - Swing START: where wrist first deviates from address by a significant
        fraction of the total motion range (adaptive).
        - Swing END: where motion energy decays below threshold.
        """
        n = len(smoothed_wrist)
        baseline_len = min(precheck_window, max(3, n // 8))

        # ── Swing END via motion energy decay ──
        valid_motion = motion_energy[baseline_len:]
        median = np.nanmedian(valid_motion) if len(valid_motion) > 0 else 0.0
        std = np.nanstd(valid_motion) + 1e-3 if len(valid_motion) > 0 else 1.0
        high_thresh = median + std * 1.0
        low_thresh = median + std * 0.15

        swing_end = n - 1
        active = np.where(motion_energy > high_thresh)[0]
        if len(active) > 0:
            end = active[-1]
            while end < len(motion_energy) - 1 and motion_energy[end + 1] > low_thresh:
                end += 1
            swing_end = min(n - 1, end + 2)

        # ── Swing START ──
        # Compute adaptive threshold based on WRIST MOTION RANGE
        address_y = np.nanmedian(smoothed_wrist[:baseline_len])
        address_noise = np.nanstd(smoothed_wrist[:baseline_len]) + 1e-3
        wrist_range = abs(np.nanmax(smoothed_wrist[:swing_end]) - np.nanmin(smoothed_wrist[:swing_end]))

        if wrist_range < 5:
            wrist_range = 30  # sensible default for low-motion videos

        # Deviation threshold: needs to exceed noise AND be meaningful relative to range
        noise_thresh = address_noise * 3.0
        range_thresh = wrist_range * 0.03
        dev_threshold = max(noise_thresh, range_thresh, 2.0)
        # Cap: never more than 8% of range (prevents over-delay on large ranges)
        dev_threshold = min(dev_threshold, wrist_range * 0.08 + 1.0)

        min_consecutive = 3
        forward_start = max(1, swing_end - 3)  # fallback

        for i in range(baseline_len, swing_end - min_consecutive):
            if abs(smoothed_wrist[i] - address_y) > dev_threshold:
                sustained = all(
                    abs(smoothed_wrist[i + j] - address_y) > dev_threshold * 0.5
                    for j in range(1, min_consecutive)
                )
                if sustained:
                    forward_start = i
                    break

        # ── Backward scan from wrist minimum (TOP approximation) ──
        wrist_min_idx = int(np.nanargmin(smoothed_wrist[:swing_end])) if swing_end > 0 else 0
        velocity = np.abs(np.gradient(smoothed_wrist))
        vel_med = np.nanmedian(velocity[:max(baseline_len, 1)])

        quiet_thresh = max(vel_med * 2.5, 1.0)
        backward_start = wrist_min_idx

        for i in range(wrist_min_idx, max(1, baseline_len // 2), -1):
            if velocity[i] < quiet_thresh:
                quiet_count = 0
                check_range = min(5, i)
                for j in range(i, max(0, i - check_range), -1):
                    if velocity[j] < quiet_thresh:
                        quiet_count += 1
                if quiet_count >= 3:
                    backward_start = i + 1
                    break

        # Use the EARLIER of forward and backward scans (conservative)
        swing_start = min(forward_start, backward_start)
        swing_start = max(baseline_len // 4, swing_start)

        return swing_start, swing_end

    # ── Phase-specific detectors ─────────────────────────────────────────

    def _find_address_phase(
        self,
        smoothed: np.ndarray,
        swing_start: int,
    ) -> Tuple[int, int]:
        """
        Find ADDRESS phase (static position before swing).

        Adaptive: flat region is relative to total wrist motion range,
        not a fixed pixel threshold.
        """
        address_start = 0
        n = len(smoothed)

        # Adaptive flatness threshold: scale by wrist motion range
        total_range = float(abs(
            np.nanmax(smoothed) - np.nanmin(smoothed)
        )) if n > 5 else 10.0
        flat_thresh = max(0.5, total_range * 0.02)  # 2% of total range

        # Minimum flat frames: scale with video length
        min_flat = max(3, min(20, n // 10))

        for i in range(swing_start - min_flat, -1, -1):
            window_end = min(i + min_flat, swing_start)
            window = smoothed[i:window_end]
            if len(window) < min_flat:
                continue
            nan_count = np.count_nonzero(np.isnan(window))
            if nan_count > len(window) // 3:
                continue
            if np.nanstd(window) < flat_thresh:
                address_start = i
            else:
                break

        return max(0, address_start), swing_start

    def _find_top_phase(
        self,
        smoothed: np.ndarray,
        swing_start: int,
        swing_end: int,
        wrist_y: np.ndarray,
    ) -> Tuple[int, int]:
        """
        Find TOP phase (backswing peak).

        Uses position minimum + velocity zero-crossing confirmation.
        Window adapts to swing duration.
        """
        search_end = swing_start + max(5, int((swing_end - swing_start) * 0.65))
        search_end = min(search_end, swing_end)
        search_slice = smoothed[swing_start:search_end]

        if len(search_slice) == 0 or np.all(np.isnan(search_slice)):
            top_idx = (swing_start + search_end) // 2
        else:
            # Primary: position minimum (highest wrist point)
            rel_idx = int(np.nanargmin(search_slice))

            # Secondary: velocity zero-crossing confirmation
            velocity = np.gradient(smoothed)
            # Adaptive search window based on swing length
            search_window = max(4, min(12, (swing_end - swing_start) // 8))
            v_start = max(swing_start, swing_start + rel_idx - search_window)
            v_end = min(search_end, swing_start + rel_idx + search_window)

            best_idx = rel_idx
            for k in range(v_start, v_end - 1):
                if velocity[k] < 0 and velocity[k + 1] >= 0:
                    candidate = k - swing_start
                    if abs(candidate - rel_idx) < search_window:
                        best_idx = candidate
                        break

            top_idx = swing_start + best_idx

        # Narrow TOP window: ±2 frames
        top_range = (max(0, top_idx - 2), min(len(wrist_y) - 1, top_idx + 2))
        return top_range

    def _find_impact_phase(
        self,
        smoothed: np.ndarray,
        top_range: Tuple[int, int],
        swing_end: int,
        address_y: float,
    ) -> Tuple[int, int]:
        """
        Find IMPACT phase (ball contact zone).

        Strategy:
          1. Position-based: wrist returns to 95% of the way back to address level.
          2. Velocity-based: the first frame AFTER the max downward velocity,
             since impact happens after the club whips through max acceleration.
          3. The LATER of the two estimates is used (conservative — avoids firing
             impact while the downswing is still ongoing).
        """
        post_top_start = top_range[1]
        post_top = smoothed[post_top_start:swing_end]

        if len(post_top) < 2 or np.all(np.isnan(post_top)):
            return (post_top_start, post_top_start + 1)

        top_y = float(np.nanmin(smoothed[top_range[0]:top_range[1] + 1]))
        wrist_excursion = abs(address_y - top_y)

        if wrist_excursion < 3:
            # Very little motion — use velocity peak
            velocity = np.gradient(post_top)
            impact_idx = int(np.nanargmax(np.abs(velocity)))
        else:
            # ── Position-based: 95% of the way back to address ──
            crossing_frac = 0.95
            crossing = top_y + wrist_excursion * crossing_frac

            position_idx = None
            for i in range(len(post_top)):
                if post_top[i] >= crossing:
                    position_idx = i
                    break

            if position_idx is None:
                position_idx = int(np.nanargmax(post_top))

            # ── Velocity-based: max velocity point (peak of downswing speed) ──
            velocity = np.gradient(post_top)
            velocity_idx = int(np.nanargmax(velocity))  # max forward velocity

            # Use the LATER of the two (more conservative — keeps impact at
            # the correct moment of peak club speed rather than early crossing).
            impact_idx = max(position_idx, velocity_idx)

            # Safety clamp: never more than 3 frames past the crossing index
            # in case velocity peak is an outlier far down the range
            impact_idx = min(impact_idx, position_idx + 3)

        left = max(0, int(impact_idx) - 2)
        right = min(len(post_top) - 1, int(impact_idx) + 2)
        return (post_top_start + left, post_top_start + right)

    # ── Frame lookup ─────────────────────────────────────────────────────

    def get_phase_at_frame(
        self,
        frame_idx: int,
        phase_ranges: Dict[str, Tuple[int, int]],
    ) -> str:
        """
        Get phase name for a specific frame.

        Returns "UNKNOWN" if frame is outside all phase ranges.
        """
        for phase_name, (start, end) in phase_ranges.items():
            if start <= frame_idx <= end:
                return phase_name
        return "UNKNOWN"
