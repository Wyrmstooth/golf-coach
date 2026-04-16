"""Debug phase detection - dump wrist trajectory + detected phases"""
import sys, os, json
sys.path.insert(0, '.')
import numpy as np
import mediapipe_compat  # patch mp.solutions

from utils.trajectory_extractor import TrajectoryExtractor
from utils.swing_phase_analyzer import SwingPhaseAnalyzer

videos = [
    'test_videos/bad_swings/bad-10.mp4',
    'test_videos/good_swings/3.mp4',
]

for video in videos:
    if not os.path.exists(video):
        continue
    name = os.path.basename(video)
    print(f'\n{"="*70}')
    print(f'  {name}')
    print(f'{"="*70}')
    
    extractor = TrajectoryExtractor()
    frame_data = extractor.extract_from_video(video, verbose=False)
    
    analyzer = SwingPhaseAnalyzer()
    phase_ranges, swing_start, swing_end, wrist_y, smoothed = analyzer.detect_phases(frame_data)
    
    print(f'  Total frames: {len(frame_data)}')
    print(f'  Swing window: {swing_start} -> {swing_end}')
    print()
    
    # Show phases with frame counts
    for phase, (s, e) in phase_ranges.items():
        dur = e - s
        print(f'  {phase:20s}: {s:4d} - {e:4d}  ({dur:3d} frames)')
    
    # Print wrist_y around key transitions to understand the trajectory
    print(f'\n  Wrist Y around swing_start ({swing_start}):')
    for i in range(max(0, swing_start-5), min(len(smoothed), swing_start+10)):
        marker = ' <-- swing_start' if i == swing_start else ''
        print(f'    frame {i:4d}: wrist_y={smoothed[i]:.1f}{marker}')
    
    top_s, top_e = phase_ranges['TOP']
    top_mid = (top_s + top_e) // 2
    print(f'\n  Wrist Y around TOP ({top_s}-{top_e}):')
    for i in range(max(0, top_s-3), min(len(smoothed), top_e+5)):
        marker = ' <-- TOP' if top_s <= i <= top_e else ''
        print(f'    frame {i:4d}: wrist_y={smoothed[i]:.1f}{marker}')
    
    imp_s, imp_e = phase_ranges['IMPACT']
    print(f'\n  Wrist Y around IMPACT ({imp_s}-{imp_e}):')
    for i in range(max(0, imp_s-5), min(len(smoothed), imp_e+5)):
        marker = ' <-- IMPACT' if imp_s <= i <= imp_e else ''
        print(f'    frame {i:4d}: wrist_y={smoothed[i]:.1f}{marker}')
    
    # Show the full wrist trajectory in the swing region
    print(f'\n  Full swing trajectory (smoothed wrist_y):')
    for i in range(max(0, swing_start - 5), min(len(smoothed), swing_end + 5)):
        phase = 'ADDRESS'
        for pname, (ps, pe) in phase_ranges.items():
            if ps <= i <= pe:
                phase = pname
                break
        vel = np.gradient(smoothed)[i] if i < len(smoothed) else 0
        print(f'    {i:4d}: y={smoothed[i]:7.1f}  vel={vel:7.2f}  [{phase}]')
