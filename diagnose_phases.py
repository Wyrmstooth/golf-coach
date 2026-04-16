"""Show phase ranges for all swing videos."""
import sys, os, numpy as np
sys.path.insert(0, '.')
import mediapipe_compat  # noqa
from utils.trajectory_extractor import TrajectoryExtractor
from utils.swing_phase_analyzer import SwingPhaseAnalyzer

te = TrajectoryExtractor()
pa = SwingPhaseAnalyzer()

videos = (
    [('GOOD', 'good_swings/' + f) for f in sorted(os.listdir('good_swings')) if f.endswith('.mp4')]
    + [('BAD', 'bad_swings/' + f) for f in sorted(os.listdir('bad_swings')) if f.endswith('.mp4')]
)

def fmt(r):
    return "%3d-%3d(%3df)" % (r[0], r[1], r[1] - r[0])

header = "%-5s %-16s %6s %14s %14s %12s %14s %12s %14s" % (
    'Type', 'Video', 'Frames', 'ADDR', 'BKSWING', 'TOP', 'DSWING', 'IMPACT', 'FOLLOW')
print(header)
print('-' * len(header))

for label, vpath in videos:
    if not os.path.exists(vpath):
        continue
    name = os.path.basename(vpath)
    te.cached_landmarks = []
    fd = te.extract_from_video(str(vpath), verbose=False, preprocess=False)
    pr, ss, se, wy, sm = pa.detect_phases(fd)
    n = len(fd)
    print("%-5s %-16s %6d %14s %14s %12s %14s %12s %14s" % (
        label, name, n,
        fmt(pr['ADDRESS']), fmt(pr['BACKSWING']), fmt(pr['TOP']),
        fmt(pr['DOWNSWING']), fmt(pr['IMPACT']), fmt(pr['FOLLOW_THROUGH'])))
