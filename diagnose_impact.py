"""
Diagnose impact phase accuracy by checking wrist position at detected impact
relative to address position. A good impact should have wrist near address level.
Also shows velocity profile around impact.
"""
import sys, os, numpy as np
sys.path.insert(0, '.')
import mediapipe_compat  # noqa: F401 - patches mp.solutions

from utils.trajectory_extractor import TrajectoryExtractor
from utils.swing_phase_analyzer import SwingPhaseAnalyzer
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter

te = TrajectoryExtractor()
pa = SwingPhaseAnalyzer()

videos = (
    [('GOOD', f'good_swings/{f}') for f in sorted(os.listdir('good_swings')) if f.endswith('.mp4')]
    + [('BAD', f'bad_swings/{f}') for f in sorted(os.listdir('bad_swings')) if f.endswith('.mp4')]
)

print(f"{'Type':<6} {'Video':<16} {'Addr_Y':>8} {'Top_Y':>8} {'Imp_Y':>8} {'Return%':>8} "
      f"{'Imp_Vel':>8} {'MaxVel':>8} {'ImpFrame':>9} {'MaxVFrame':>10} {'Gap':>5} "
      f"{'DS_Len':>7} {'IMP_Len':>8}")
print('-' * 140)

for label, vpath in videos:
    if not os.path.exists(vpath):
        continue
    name = os.path.basename(vpath)
    
    te.cached_landmarks = []
    frame_data = te.extract_from_video(str(vpath), verbose=False, preprocess=False)
    
    wrist_y = np.array([d.get("wrist_y", np.nan) for d in frame_data], dtype=np.float32)
    
    # Smooth like the analyzer does
    processed = wrist_y.copy()
    mask = np.isnan(processed)
    if mask.any():
        processed[mask] = np.interp(np.flatnonzero(mask), np.flatnonzero(~mask), processed[~mask])
    processed = gaussian_filter1d(processed, sigma=2, mode='nearest')
    wl = min(len(processed) // 2 * 2 + 1, 11)
    if wl >= 5 and len(processed) >= wl:
        processed = savgol_filter(processed, wl, polyorder=2, mode='interp')
    
    phase_ranges, swing_start, swing_end, wy, smoothed = pa.detect_phases(frame_data)
    
    addr_range = phase_ranges.get('ADDRESS', (0, swing_start))
    top_range = phase_ranges.get('TOP', (0, 0))
    impact_range = phase_ranges.get('IMPACT', (0, 0))
    ds_range = phase_ranges.get('DOWNSWING', (0, 0))
    
    addr_y = float(np.nanmedian(smoothed[:max(1, swing_start)]))
    top_y = float(np.nanmin(smoothed[top_range[0]:top_range[1]+1]))
    
    imp_mid = (impact_range[0] + impact_range[1]) // 2
    imp_y = float(smoothed[imp_mid]) if imp_mid < len(smoothed) else np.nan
    
    # Return percentage (how close impact wrist is to address)
    excursion = abs(addr_y - top_y)
    if excursion > 1:
        return_pct = abs(imp_y - top_y) / excursion * 100
    else:
        return_pct = 0
    
    # Velocity at impact vs max velocity
    velocity = np.gradient(smoothed)
    imp_vel = float(velocity[imp_mid]) if imp_mid < len(velocity) else 0
    
    post_top = velocity[top_range[1]:swing_end]
    if len(post_top) > 0:
        max_vel_rel = int(np.nanargmax(post_top))
        max_vel = float(post_top[max_vel_rel])
        max_vel_frame = top_range[1] + max_vel_rel
    else:
        max_vel = 0
        max_vel_frame = 0
    
    gap = imp_mid - max_vel_frame  # Positive = impact after max vel
    ds_len = ds_range[1] - ds_range[0]
    imp_len = impact_range[1] - impact_range[0]
    
    print(f"{label:<6} {name:<16} {addr_y:8.1f} {top_y:8.1f} {imp_y:8.1f} {return_pct:7.1f}% "
          f"{imp_vel:8.1f} {max_vel:8.1f} {imp_mid:9d} {max_vel_frame:10d} {gap:5d} "
          f"{ds_len:7d} {imp_len:8d}")
