"""Verify the ball tracking model is a real file, not a Git LFS pointer."""
import os
import sys

model = "models/golf_ball_frcnn.pt"

if not os.path.exists(model):
    print("WARNING: Ball tracking model not found — ball tracking will be unavailable")
    sys.exit(0)

size = os.path.getsize(model)
if size < 1000:
    print(f"WARNING: Ball tracking model is a Git LFS pointer ({size} bytes) — run 'git lfs pull' before building")
    sys.exit(0)

print(f"Ball tracking model OK ({size // 1024 // 1024} MB)")
