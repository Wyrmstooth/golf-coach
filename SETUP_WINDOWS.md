## GolfCoach-2 – Windows Setup Guide

This document explains how to install dependencies and run the `golfCoach-2` project on **Windows** using a stable Python/MediaPipe combination.

---

## 1. Prerequisites

- **OS**: Windows 10/11 (64‑bit)
- **Python**: Installed via **Anaconda or Miniconda**
- **Conda**: Available in your terminal (`conda --version` works)
- (Optional) **GPU**: NVIDIA GPU with CUDA for faster Torch/YOLO; CPU is still supported.

Project root (adjust if different on your machine):

```bash
C:\Users\munib\Desktop\fyp_files\fyp2\golfCoach-2
```

---

## 2. Create the Conda environment

Use an **Anaconda Prompt** or any terminal where `conda` is available:

```bash
# 1) Go to the project directory
cd "C:\Users\munib\Desktop\fyp_files\fyp2\golfCoach-2"

# 2) Create environment with Python 3.10 (one‑time)
conda create -n golfpose python=3.10 -y

# 3) Activate the environment
conda activate golfpose
```

Why: the project relies on MediaPipe’s classic `mp.solutions` API, which is present in `mediapipe==0.10.21` and works reliably with Python 3.10 on Windows.

---

## 3. Install Python dependencies

With the `golfpose` environment **activated** and your working directory set to `golfCoach-2`:

```bash
cd "C:\Users\munib\Desktop\fyp_files\fyp2\golfCoach-2"

# Install all project requirements
pip install -r requirements.txt
```

Key entries from `requirements.txt`:

- `mediapipe==0.10.21` (pinned; provides `mp.solutions`)
- `opencv-python>=4.8.0`
- `numpy>=1.24.0`
- `scipy>=1.10.0`
- `matplotlib>=3.7.0`
- `tqdm>=4.65.0`
- `streamlit>=1.40.0`
- `pillow>=10.0.0`
- `pandas>=2.0.0`
- `scikit-learn>=1.3.0`
- `pyyaml>=6.0`
- `streamlit-webrtc>=0.47.0`
- `ultralytics>=8.0.0` (pulls in `torch` and `torchvision`)

### Verify MediaPipe is correctly installed

Still inside the `golfpose` environment:

```bash
python -c "import mediapipe as mp; print(mp.__version__); print(hasattr(mp, 'solutions'))"
```

Expected output:

```text
0.10.21
True
```

If `hasattr(..., 'solutions')` prints `False`, you are not using the right environment.

---

## 4. Run the Streamlit web app

With `golfpose` **activated** and from the project directory:

```bash
cd "C:\Users\munib\Desktop\fyp_files\fyp2\golfCoach-2"
streamlit run golf_coach_app.py
```

Then open the app in your browser:

- `http://localhost:8501`

This launches the Golf Coach UI with:

- Mode selector (Video Analysis, Live ADDRESS Pose Check, Live Swing Analysis)
- Video upload/sample video picker
- “Analyze Swing” button and detailed results.

To stop the app, press `Ctrl + C` in the terminal where Streamlit is running.

---

## 5. Command‑line video analysis (optional)

You can also run offline analysis from the command line:

```bash
conda activate golfpose
cd "C:\Users\munib\Desktop\fyp_files\fyp2\golfCoach-2"

# Full analysis with annotated video output
python analyze_video.py --video path\to\your_swing.mp4

# Faster mode (no annotated video rendering)
python analyze_video.py --video path\to\your_swing.mp4 --fast
```

Results are written under the `output` directory:

- `VIDEO_report.json` – detailed metrics and fault analysis
- `VIDEO_analysis.png` – trajectory plot
- `VIDEO_annotated.mp4` – annotated swing video (if not using `--fast`)

---

## 6. Common issues on Windows

- **Error**: `module 'mediapipe' has no attribute 'solutions'`
  - **Cause**: Streamlit is running with the wrong Python (e.g., system Python 3.13 where MediaPipe is in “tasks”–only mode).
  - **Fix**:
    1. Close any existing Streamlit terminal.
    2. In a new terminal:
       ```bash
       conda activate golfpose
       cd "C:\Users\munib\Desktop\fyp_files\fyp2\golfCoach-2"
       streamlit run golf_coach_app.py
       ```
    3. Re‑run the MediaPipe check from section 3.

- **Missing package errors** (e.g., `ModuleNotFoundError`)
  - Ensure the `golfpose` environment is active and re‑run:
    ```bash
    pip install -r requirements.txt
    ```

---

## 7. Quick reference

Most common commands you will use:

```bash
# Create env (one time)
conda create -n golfpose python=3.10 -y

# Each new session
conda activate golfpose
cd "C:\Users\munib\Desktop\fyp_files\fyp2\golfCoach-2"

# Install deps (after cloning or updating)
pip install -r requirements.txt

# Run web app
streamlit run golf_coach_app.py

# Optional: CLI analysis
python analyze_video.py --video path\to\your_swing.mp4 --fast
```

