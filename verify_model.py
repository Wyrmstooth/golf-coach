"""Verify the ball tracking model is a real binary file, not a Git LFS pointer.

Exits with 0 if the model is valid or absent (ball tracking will be disabled).
Exits with 1 if the model is a Git LFS pointer (broken — would fail at runtime).
"""
import os
import sys

model = "models/golf_ball_frcnn.pt"

if not os.path.exists(model):
    print("WARNING: Ball tracking model not found — ball tracking will be unavailable")
    sys.exit(0)

size = os.path.getsize(model)
if size < 1000:
    print(f"ERROR: Ball tracking model is a Git LFS pointer ({size} bytes).")
    print("       Run 'git lfs pull' or set MODEL_DOWNLOAD_URL before building.")
    sys.exit(1)

# Check for LFS pointer header (starts with "version https://git-lfs...")
with open(model, "rb") as f:
    header = f.read(50)
if header.startswith(b"version https://git-lfs"):
    print(f"ERROR: Ball tracking model is a Git LFS pointer file. Download the real file first.")
    sys.exit(1)

print(f"Ball tracking model OK ({size // 1024 // 1024} MB)")