import sys; sys.path.insert(0, ".")
from models.golf_ball_detector import GolfBallDetector
import cv2, numpy as np
from pathlib import Path

out = max(Path("output").glob("*"), key=lambda p: p.stat().st_mtime)
vid = next(out.glob("input.*"))
print(f"Video: {vid}")

detector = GolfBallDetector("models/golf_ball_frcnn.pt", conf_threshold=0.2,
                            enable_kalman=False)

cap = cv2.VideoCapture(str(vid))
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Size: {w}x{h}, Frames: {total}")

hits = 0
for i in range(0, total, 2):
    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
    ret, frame = cap.read()
    if not ret: break
    dets = detector.detect(frame)
    if dets:
        hits += 1
        b = dets[0]
        if hits <= 8:
            print(f"  Frame {i}: conf={b.confidence:.3f} @ ({b.x:.0f},{b.y:.0f}) {b.width:.0f}x{b.height:.0f}")
    else:
        if hits > 0 and hits <= 8:
            print(f"  Frame {i}: MISS")
cap.release()

tested = total // 2
print(f"Rate: {hits}/{tested} ({100*hits/max(tested,1):.0f}%)")
