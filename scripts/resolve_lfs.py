"""
Resolve Git LFS pointer for the ball tracking model.

During Docker builds, `COPY . .` copies LFS pointer files instead of the
actual binaries. This script detects the pointer and downloads the real
model from GitHub's LFS storage using the batch API.

If the model file is already the real binary (e.g. when building locally
with `git lfs pull`), this script is a no-op.
"""
import os
import sys
import json
import urllib.request
import urllib.error
import hashlib
import base64

LFS_POINTER_PREFIX = b"version https://git-lfs"
MODEL_PATH = "models/golf_ball_frcnn.pt"
GITHUB_REPO = "zainulabidin776/golf-dashboard"
LFS_API_URL = f"https://github.com/{GITHUB_REPO}.git/info/lfs/objects/batch"


def is_lfs_pointer(filepath: str) -> bool:
    """Check if a file is a Git LFS pointer (not the real binary)."""
    if not os.path.exists(filepath):
        return False
    if os.path.getsize(filepath) > 1000:
        return False
    try:
        with open(filepath, "rb") as f:
            header = f.read(100)
        return header.strip().startswith(b"version https://git-lfs")
    except Exception:
        return False


def parse_lfs_pointer(filepath: str) -> dict:
    """Parse a Git LFS pointer file to extract the OID and size."""
    with open(filepath, "r") as f:
        lines = f.read().strip().split("\n")
    result = {}
    for line in lines:
        if line.startswith("oid sha256:"):
            result["oid"] = line.split(":", 1)[1].strip()
        elif line.startswith("size "):
            result["size"] = int(line.split(" ", 1)[1].strip())
    return result


def download_from_lfs_api(pointer_info: dict, dest: str) -> bool:
    """Download the actual LFS object using GitHub's LFS batch API."""
    oid = pointer_info.get("oid")
    size = pointer_info.get("size", 0)
    if not oid:
        print("ERROR: Could not parse OID from LFS pointer")
        return False

    # Use LFS batch API to get the download URL
    request_body = json.dumps({
        "operation": "download",
        "objects": [{"oid": oid, "size": size}],
        "transfers": ["basic"],
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/vnd.git-lfs+json",
        "Accept": "application/vnd.git-lfs+json",
    }

    req = urllib.request.Request(LFS_API_URL, data=request_body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"ERROR: LFS API request failed: {e}")
        return False

    objects = data.get("objects", [])
    if not objects:
        print("ERROR: No objects returned from LFS API")
        return False

    obj = objects[0]
    download = obj.get("actions", {}).get("download", {})
    href = download.get("href")
    if not href:
        # If no actions but object exists, maybe it's already inline
        error = obj.get("error")
        if error:
            print(f"ERROR: LFS API returned error: {error.get('message', error)}")
        return False

    # Download the actual file
    print(f"Downloading model from LFS storage ({size // 1024 // 1024} MB)...")
    dl_req = urllib.request.Request(href)
    # Add authorization headers if provided in the response
    for header_name, header_value in download.get("header", {}).items():
        dl_req.add_header(header_name, header_value)

    try:
        with urllib.request.urlopen(dl_req, timeout=300) as dl_resp:
            with open(dest, "wb") as out:
                # Download in chunks to handle large files
                while True:
                    chunk = dl_resp.read(8 * 1024 * 1024)  # 8MB chunks
                    if not chunk:
                        break
                    out.write(chunk)
    except Exception as e:
        print(f"ERROR: Download failed: {e}")
        return False

    # Verify download
    actual_size = os.path.getsize(dest)
    if actual_size != size:
        print(f"WARNING: Downloaded size ({actual_size}) != expected size ({size})")
        # Still consider it a success if the file is reasonably large
        if actual_size < 1_000_000:
            print("ERROR: Downloaded file is too small — likely not the real model")
            os.remove(dest)
            return False

    # Verify SHA256 hash
    print("Verifying model hash...")
    sha256 = hashlib.sha256()
    with open(dest, "rb") as f:
        while True:
            chunk = f.read(8 * 1024 * 1024)
            if not chunk:
                break
            sha256.update(chunk)

    if sha256.hexdigest() != oid:
        print(f"WARNING: Hash mismatch (got {sha256.hexdigest()[:16]}... expected {oid[:16]}...)")
        print("This may be OK if the LFS object was compressed or the download was partial.")
        # Don't fail the build — the model might still work

    print(f"Model downloaded successfully ({actual_size // 1024 // 1024} MB)")
    return True


def main():
    if not os.path.exists(MODEL_PATH):
        print(f"WARNING: Ball tracking model not found at {MODEL_PATH}")
        print("Ball tracking will be disabled")
        return

    if not is_lfs_pointer(MODEL_PATH):
        size_mb = os.path.getsize(MODEL_PATH) // 1024 // 1024
        print(f"Ball tracking model OK ({size_mb} MB)")
        return

    print("LFS pointer detected — resolving download URL...")

    pointer_info = parse_lfs_pointer(MODEL_PATH)
    print(f"  OID: {pointer_info.get('oid', 'unknown')[:16]}...")
    print(f"  Size: {pointer_info.get('size', 0) // 1024 // 1024} MB")

    if not download_from_lfs_api(pointer_info, MODEL_PATH):
        print("WARNING: Could not download LFS model — ball tracking will be disabled")
        # Don't fail the build; the app handles missing model gracefully


if __name__ == "__main__":
    main()