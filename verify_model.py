"""Check if the ball tracking model is available.

Exits with 0 always (never fails the build).
If the model is missing or is an LFS pointer, prints a warning about
setting MODEL_URL to download at runtime.
"""
import os
import sys

MODEL = "models/golf_ball_frcnn.pt"

if not os.path.exists(MODEL):
    print("WARNING: Ball tracking model not found")
    print("Set MODEL_URL env var to download at runtime, or ball tracking will be disabled")
    sys.exit(0)

size = os.path.getsize(MODEL)
if size < 1000:
    print(f"WARNING: Ball tracking model is a Git LFS pointer ({size} bytes)")
    print("Set MODEL_URL env var to download the real model at runtime")
    sys.exit(0)

with open(MODEL, "rb") as f:
    header = f.read(50)
if header.strip().startswith(b"version https://git-lfs"):
    print("WARNING: Ball tracking model is a Git LFS pointer file")
    print("Set MODEL_URL env var to download the real model at runtime")
    sys.exit(0)

print(f"Ball tracking model OK ({size // 1024 // 1024} MB)")