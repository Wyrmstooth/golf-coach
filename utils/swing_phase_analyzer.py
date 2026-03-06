"""
Golf swing phase detection and analysis
"""

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter
from typing import Dict, List, Tuple


class SwingPhaseAnalyzer:
    """Detect golf swing phases using multi-metric biomechanical analysis"""
    
    def __init__(self):
        pass
    
    def detect_phases(
        self,
        frame_data: List[Dict],
        smoothing_window: int = 5,
        precheck_window: int = 30,
        threshold_percentile: int = 90
    ) -> Tuple[Dict[str, Tuple[int, int]], int, int, np.ndarray, np.ndarray]:
        """
        Detect golf swing phases from trajectory data
        
        Uses multi-metric analysis: wrist trajectory, hip rotation, shoulder alignment
        
        Args:
            frame_data: List of dicts with frame_idx, wrist_y, hip_rotation, shoulder_rotation
            smoothing_window: Window size for smoothing
            precheck_window: Frames to check for static ADDRESS
            threshold_percentile: Percentile for motion threshold
        
        Returns:
            phase_ranges: Dict mapping phase names to (start_frame, end_frame)
            swing_start: Frame where swing motion begins
            swing_end: Frame where swing motion ends
            wrist_y: Raw wrist Y coordinates
            smoothed: Smoothed wrist Y coordinates
        """
        # Extract primary signals
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

        # Preprocess / smooth signals for robustness
        smoothed_wrist = self._prepare_signal(wrist_y, smoothing_window)
        smoothed_hip = self._prepare_signal(hip_rot, smoothing_window)
        smoothed_shoulder = self._prepare_signal(shoulder_rot, smoothing_window)

        # Motion energy combines wrist + hip + shoulder dynamics
        motion_energy = self._compute_motion_profile(
            smoothed_wrist,
            smoothed_hip,
            smoothed_shoulder
        )

        # Detect swing window using hysteresis on motion energy
        swing_start, swing_end = self._detect_swing_window(
            motion_energy,
            smoothed_wrist,
            precheck_window,
            threshold_percentile
        )
        
        # Find ADDRESS position (flat region before swing)
        address_start, address_end = self._find_address_phase(
            smoothed_wrist, swing_start, flat_std_thresh=1.0, min_flat_frames=10
        )
        
        # Find TOP position (lowest wrist point in backswing)
        top_range = self._find_top_phase(smoothed_wrist, swing_start, swing_end, wrist_y)
        
        # Find IMPACT position (highest wrist point after top)
        impact_range = self._find_impact_phase(smoothed_wrist, top_range, swing_end)
        
        # Define all phase ranges with proper ordering
        backswing_end = max(swing_start + 1, top_range[0])  # Ensure positive duration
        downswing_end = max(top_range[1] + 1, impact_range[0])
        
        phase_ranges = {
            "ADDRESS": (address_start, address_end),
            "BACKSWING": (swing_start, backswing_end),
            "TOP": (backswing_end, max(backswing_end + 1, top_range[1])),
            "DOWNSWING": (max(backswing_end + 1, top_range[1]), downswing_end),
            "IMPACT": (downswing_end, max(downswing_end + 1, impact_range[1])),
            "FOLLOW_THROUGH": (max(downswing_end + 1, impact_range[1]), swing_end)
        }
        
        return phase_ranges, swing_start, swing_end, wrist_y, smoothed_wrist

    def _prepare_signal(self, signal: np.ndarray, smoothing_window: int) -> np.ndarray:
        """Fill gaps and apply combined smoothing for stable detection"""
        if len(signal) == 0:
            return signal

        processed = signal.copy()
        processed = self._fill_nans(processed)

        # First pass: gaussian smoothing to remove jitter
        processed = gaussian_filter1d(processed, sigma=max(1, smoothing_window // 2), mode='nearest')

        # Second pass: Savitzky-Golay for trend preservation (if enough frames)
        window_length = min(len(processed) // 2 * 2 + 1, max(5, smoothing_window * 2 + 1))
        if window_length >= 5 and len(processed) >= window_length:
            processed = savgol_filter(processed, window_length, polyorder=2, mode='interp')

        return processed

    def _fill_nans(self, signal: np.ndarray) -> np.ndarray:
        """Forward/backward fill NaNs to keep trajectories continuous"""
        if np.all(np.isnan(signal)):
            return np.zeros_like(signal)

        # Forward fill
        mask = np.isnan(signal)
        if mask.any():
            signal[mask] = np.interp(
                np.flatnonzero(mask),
                np.flatnonzero(~mask),
                signal[~mask]
            )
        return signal

    def _compute_motion_profile(self, wrist: np.ndarray, hip: np.ndarray, shoulder: np.ndarray) -> np.ndarray:
        """Combine multi-signal velocities into a single motion energy curve"""
        def _normalize_derivative(arr: np.ndarray) -> np.ndarray:
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
        threshold_percentile: int
    ) -> Tuple[int, int]:
        """Locate swing start/end using motion energy with hysteresis fallback"""
        valid_motion = motion_energy[precheck_window:]
        median = np.nanmedian(valid_motion)
        std = np.nanstd(valid_motion) + 1e-3
        high_thresh = median + std * 2.0
        low_thresh = median + std * 0.6

        active = np.where(motion_energy > high_thresh)[0]
        if len(active) > 0:
            start = active[0]
            while start > 0 and motion_energy[start - 1] > low_thresh:
                start -= 1
            end = active[-1]
            while end < len(motion_energy) - 1 and motion_energy[end + 1] > low_thresh:
                end += 1
            return start, min(len(smoothed_wrist) - 1, end + 2)

        # Fallback to percentile-based wrist heuristic
        velocity = np.gradient(smoothed_wrist)
        velocity_mag = np.abs(velocity)
        threshold = np.nanpercentile(velocity_mag[precheck_window:], threshold_percentile)
        motion_indices = np.where(velocity_mag > threshold)[0]
        motion_indices = motion_indices[motion_indices > precheck_window]

        if len(motion_indices) > 0:
            swing_start = int(motion_indices[0])
            swing_end = int(motion_indices[-1])
        else:
            swing_start = 0
            swing_end = len(smoothed_wrist) - 1

        return swing_start, swing_end
    
    def _find_address_phase(
        self,
        smoothed: np.ndarray,
        swing_start: int,
        flat_std_thresh: float = 1.0,
        min_flat_frames: int = 10
    ) -> Tuple[int, int]:
        """Find ADDRESS phase (static position before swing)"""
        address_start = 0
        
        for i in range(swing_start - min_flat_frames, 0, -1):
            window = smoothed[i:swing_start]
            if np.count_nonzero(~np.isnan(window)) < min_flat_frames:
                continue
            if np.nanstd(window) < flat_std_thresh:
                address_start = i
            else:
                break
        
        return address_start, swing_start
    
    def _find_top_phase(
        self,
        smoothed: np.ndarray,
        swing_start: int,
        swing_end: int,
        wrist_y: np.ndarray
    ) -> Tuple[int, int]:
        """Find TOP phase (backswing peak)"""
        search_end = swing_start + max(5, int((swing_end - swing_start) * 0.6))
        search_end = min(search_end, swing_end)
        search_slice = smoothed[swing_start:search_end]
        
        if len(search_slice) == 0 or np.all(np.isnan(search_slice)):
            top_idx = (swing_start + search_end) // 2
        else:
            rel_idx = int(np.nanargmin(search_slice))
            top_idx = swing_start + rel_idx
        
        top_range = (max(0, top_idx - 5), min(len(wrist_y) - 1, top_idx + 5))
        
        return top_range
    
    def _find_impact_phase(
        self,
        smoothed: np.ndarray,
        top_range: Tuple[int, int],
        swing_end: int
    ) -> Tuple[int, int]:
        """Find IMPACT phase (ball contact zone)"""
        post_top = smoothed[top_range[1]:swing_end]
        
        if len(post_top) == 0 or np.all(np.isnan(post_top)):
            return (top_range[1], top_range[1] + 1)
        
        # Impact roughly corresponds to local maxima after top
        local_max_idx = int(np.nanargmax(post_top))
        max_val = post_top[local_max_idx]
        local_min = np.nanmin(post_top)
        dynamic_tol = 0.05 * max(1e-3, (np.nanmax(post_top) - local_min))
        
        # Find impact window
        left = local_max_idx
        right = local_max_idx
        
        while left > 0 and abs(post_top[left - 1] - max_val) < dynamic_tol:
            left -= 1
        while right < len(post_top) - 1 and abs(post_top[right + 1] - max_val) < dynamic_tol:
            right += 1
        
        impact_range = (top_range[1] + left, top_range[1] + right)
        return impact_range
    
    def get_phase_at_frame(self, frame_idx: int, phase_ranges: Dict[str, Tuple[int, int]]) -> str:
        """
        Get phase name for a specific frame
        
        Args:
            frame_idx: Frame number
            phase_ranges: Phase ranges dictionary
        
        Returns:
            Phase name or "UNKNOWN"
        """
        for phase_name, (start, end) in phase_ranges.items():
            if start <= frame_idx <= end:
                return phase_name
        return "UNKNOWN"