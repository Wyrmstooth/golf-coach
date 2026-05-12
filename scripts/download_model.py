"""
Download the ball tracking model at container startup if not present.

Set MODEL_URL env var to a direct download link for the model file.
Example: MODEL_URL=https://huggingface.co/your-user/golf-ball-detector/resolve/main/golf_ball_frcnn.pt

If MODEL_URL is not set, ball tracking will be disabled.
If the model file already exists and is >1MB, the download is skipped.
"""
import os
import sys
import urllib.request

MODEL_PATH = "models/golf_ball_frcnn.pt"
MIN_SIZE = 1_000_000  # 1 MB — real model is ~165 MB


def main():
    # Check if model already exists and is valid
    if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > MIN_SIZE:
        size_mb = os.path.getsize(MODEL_PATH) // 1024 // 1024
        print(f"Ball tracking model already present ({size_mb} MB)")
        return

    # Check for LFS pointer
    if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) < MIN_SIZE:
        with open(MODEL_PATH, "rb") as f:
            header = f.read(50)
        if header.strip().startswith(b"version https://git-lfs"):
            print("LFS pointer detected — removing and re-downloading...")
            os.remove(MODEL_PATH)

    model_url = os.environ.get("MODEL_URL", "").strip()
    if not model_url:
        print("WARNING: MODEL_URL not set — ball tracking model will not be available")
        print("Set MODEL_URL to a direct download link for the model file")
        print("Example: MODEL_URL=https://huggingface.co/user/repo/resolve/main/golf_ball_frcnn.pt")
        return

    print(f"Downloading ball tracking model from {model_url[:80]}...")
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    try:
        # Download with progress
        def report(block_num, block_size, total_size):
            if block_num % 50 == 0:
                downloaded = block_num * block_size
                if total_size > 0:
                    pct = min(100, downloaded * 100 // total_size)
                    print(f"  {pct}% ({downloaded // 1024 // 1024} MB / {total_size // 1024 // 1024} MB)")

        urllib.request.urlretrieve(model_url, MODEL_PATH, reporthook=report)
        actual_size = os.path.getsize(MODEL_PATH)
        if actual_size < MIN_SIZE:
            print(f"ERROR: Downloaded file is only {actual_size} bytes — likely not the real model")
            os.remove(MODEL_PATH)
            return
        print(f"Ball tracking model downloaded ({actual_size // 1024 // 1024} MB)")
    except Exception as e:
        print(f"ERROR: Model download failed: {e}")
        print("Ball tracking will be disabled")
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)


if __name__ == "__main__":
    main()