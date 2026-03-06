# 🏌️ Golf Coach Pro - AI-Powered Golf Swing Analyzer

**Professional golf swing analysis using MediaPipe pose estimation, ML fault detection, and performance prediction.**

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.21-green.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🎯 Features

### 📹 Video Analysis

- **6-Phase Detection**: ADDRESS → BACKSWING → TOP → DOWNSWING → IMPACT → FOLLOW-THROUGH
- **CaddieSet-Compatible Features**: 126 biomechanical features from professional golf research
- **Detailed Fault Analysis**: Phase-specific feedback with severity levels (🔴🟠🟡)
- **Performance Prediction**: ML model estimating ball speed, distance, and carry
- **Multi-Metric Phase Detection**: Advanced analysis using wrist trajectory, hip rotation, and shoulder alignment
- **Pose Skeleton Overlay**: MediaPipe 33-point pose estimation
- **Video Enhancement**: CLAHE contrast enhancement, bilateral filtering, sharpening
- **4x Upscaling**: Low-res videos automatically upscaled for better analysis
- **Slow Motion**: Videos slowed to 50% speed for detailed analysis
- **Trajectory Plots**: Visual graphs showing wrist movement through phases

### 🤖 Machine Learning

- **Supervised Fault Detection**: 92% CV accuracy classification of good vs bad swings using PyTorch neural networks
- **Performance Prediction**: Neural network regression trained on CaddieSet data (R²=0.67)
- **126 Biomechanical Features**: Professional-grade swing mechanics analysis
- **Professional Training Data**: Trained on CaddieSet professional swings + amateur data
- **GPU Acceleration**: CUDA support for faster training and inference

### 🌐 Streamlit Web App

- **Interactive UI**: Beautiful, professional interface
- **Upload Videos**: Analyze your own golf swings
- **Sample Videos**: Pre-loaded test videos
- **Download Results**: Export annotated videos and JSON reports
- **Live Webcam**: Real-time pose checking

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
cd /home/umer/Desktop/goldf

# Create conda environment
conda create -n golfpose python=3.8 -y
conda activate golfpose

# Install dependencies
pip install -r requirements.txt
```

### Training ML Models (Required First)

```bash
# Train supervised ML models (fault detection + performance prediction)
python training/train_pytorch_models.py
```

### Usage

#### 1. **Streamlit Web App** (Recommended)

```bash
streamlit run golf_coach_app.py
```

Then open http://localhost:8501 in your browser.

#### 2. **Command Line - Analyze Single Video**

```bash
# Standard analysis (generates annotated video)
python analyze_video.py --video 167.mp4

# Fast mode (3-5x faster - skips video rendering)
python analyze_video.py --video 167.mp4 --fast

# Skip video rendering (same as --fast)
python analyze_video.py --video 167.mp4 --skip-video

# Analyze with verbose output
python analyze_video.py --video Untitled00000487.mp4 --verbose
```

**Performance Tips:**

- Use `--fast` or `--skip-video` for 3-5x faster analysis (skips video rendering)
- Video rendering is the slowest part - skip if you only need the analysis report
- 4K videos are automatically downscaled to 1080p for faster processing
- Model complexity reduced to 1 for 3x faster pose detection with minimal accuracy loss

#### 3. **Batch Analysis - All Videos**

```bash
# Fast batch processing (recommended)
for video in *.mp4; do
    echo "Processing $video..."
    python analyze_video.py --video "$video" --fast
done

# With video rendering
for video in *.mp4; do
    echo "Processing $video..."
    python analyze_video.py --video "$video"
done
```

---

## 📁 Project Structure

```
goldf/
├── analyze_video.py               # Main video analysis script
├── golf_coach_app.py              # Streamlit web application
├── phase_detector.py              # Swing phase detection module
├── pose_detector.py               # Pose estimation utilities
├── config.yaml                    # Configuration parameters
├── requirements.txt               # Python dependencies
├── setup.sh                       # Environment setup script
├── launch_app.sh                  # Quick launch script
├── README.md                      # This file
│
├── models/                        # Trained ML models
│   ├── fault_detector.pt          # PyTorch swing quality classifier
│   ├── fault_detector.py          # Model loading utilities
│   ├── performance_predictor.pt   # PyTorch ball flight prediction model
│   ├── performance_predictor.py   # Model loading utilities
│   ├── swing_quality_classifier.pt # Additional classifier model
│   ├── training_report.json       # Training metrics and results
│   └── __pycache__/
│
├── training/                      # ML training scripts and data
│   ├── caddieset_feature_extractor.py     # CaddieSet-compatible feature extraction
│   ├── create_caddieset_dataset_split.py  # Dataset creation and splitting
│   ├── prepare_train_test_split.py        # Train/test data preparation
│   ├── run_pytorch_training_pipeline.py   # Full training pipeline
│   └── train_pytorch_models.py            # Train PyTorch models
│
├── training_data/                 # Extracted features and datasets
│   ├── dataset_statistics.csv     # Dataset statistics
│   ├── golf_swings_dataset.csv    # Combined swing dataset
│   ├── test_videos.txt            # Test video list
│   └── train_videos.txt           # Train video list
│
├── utils/                         # Core analysis modules
│   ├── __init__.py
│   ├── biomechanics.py            # Golf-specific calculations
│   ├── feature_extractor.py       # Biomechanical feature calculation
│   ├── swing_phase_analyzer.py    # Phase detection algorithms
│   ├── trajectory_extractor.py    # Pose estimation and tracking
│   ├── video_preprocessor.py      # Video preprocessing utilities
│   ├── video_processor.py         # Video I/O and annotation
│   └── visualizer.py              # Plotting and visualization
│
├── output/                        # Analysis results
│   ├── bad-10_report.json         # Example analysis report
│   └── ...                        # Other reports and outputs
│
├── test_videos/                   # Test video samples
│   ├── bad_swings/                # Bad swing examples
│   └── good_swings/               # Good swing examples
│
├── bad_swings/                    # Bad swing videos for training
├── good_swings/                   # Good swing videos for training
├── CaddieSet.csv                  # CaddieSet dataset metadata
└── __pycache__/
```

---

## 🧠 How It Works

### ML Pipeline

1. **Feature Extraction**: 126 CaddieSet-compatible biomechanical features from MediaPipe pose estimation
2. **Phase Detection**: Multi-metric analysis of wrist trajectory, hip rotation, shoulder alignment
3. **Fault Detection**: PyTorch neural network classifier with phase-specific feedback and severity levels
4. **Performance Prediction**: Neural network estimates ball speed, distance, carry (trained on CaddieSet data)
5. **Visualization**: Annotated videos, trajectory plots, JSON reports with detailed fault analysis

### Biomechanical Features

The system extracts 126 CaddieSet-compatible features across 6 swing phases:

- **Joint Angles**: Shoulder, elbow, hip, knee, ankle angles
- **Body Segment Orientations**: Spine, pelvis, upper/lower arm orientations
- **Joint Positions**: 3D coordinates of key joints relative to pelvis
- **Temporal Features**: Velocity and acceleration of key movements
- **Phase-Specific Metrics**: Unique features for each swing phase
- **Professional Standards**: Based on research from CaddieSet dataset (1757 professional swings)

### Swing Quality Scoring

- **0-25**: Professional-level technique (minimal faults)
- **25-50**: Good swing with minor issues requiring attention
- **50-75**: Moderate faults affecting consistency
- **75-100**: Significant faults requiring major corrections

**Fault Severity Levels:**

- 🔴 **Critical**: Major technique issues affecting ball flight
- 🟠 **Moderate**: Issues impacting swing efficiency
- 🟡 **Minor**: Small refinements for optimal performance

---

## ⚡ Performance Optimizations

The system has been heavily optimized for speed without sacrificing accuracy:

### Speed Improvements

- **3-5x Faster Analysis**: Use `--fast` mode to skip video rendering
- **No Redundant Processing**: Video processed only once, landmarks cached for all subsequent analysis
- **Efficient Codecs**: H.264 encoding instead of mp4v (eliminates re-encoding step)
- **Optimized Pose Detection**: Model complexity 1 instead of 2 (3x faster with <2% accuracy loss)
- **4K Auto-Downscaling**: High-resolution videos automatically downscaled to 1080p
- **Removed Preprocessing**: Unnecessary enhancement steps eliminated for high-quality videos
- **Parallel Processing Ready**: Frame-independent operations for future parallelization

### Processing Time Comparison

| Video Quality | Standard Mode | Fast Mode (--fast) | Speedup |
| ------------- | ------------- | ------------------ | ------- |
| 1080p (30s)   | ~45-60 sec    | ~10-15 sec         | 4-5x    |
| 4K (30s)      | ~90-120 sec   | ~20-30 sec         | 4-5x    |
| 720p (30s)    | ~30-40 sec    | ~8-12 sec          | 3-4x    |

**What Changed:**

1. **Single Video Pass**: Trajectory extraction now caches full pose landmarks
2. **Reused Landmarks**: Feature extraction and ML models use cached data
3. **No Re-encoding**: Direct H.264 output eliminates ffmpeg re-encoding
4. **Faster Pose Model**: Complexity 1 vs 2 (3x speed, minimal accuracy impact)
5. **Smart Preprocessing**: Only for truly low-quality videos, removed for HD content
6. **Optional Video Rendering**: Can skip entirely with `--fast` flag

### Usage for Maximum Speed

```bash
# Fastest - analysis only, no video rendering
python analyze_video.py --video my_swing.mp4 --fast

# Still fast - includes annotated video with pose overlay
python analyze_video.py --video my_swing.mp4
```

---

## 🎬 Sample Videos & Expected Results

| Video                  | Type         | Fault Score | Notes                          |
| ---------------------- | ------------ | ----------- | ------------------------------ |
| `0.mp4`                | Professional | ~2.5/100    | Clean swing, minimal issues    |
| `167.mp4`              | Professional | ~3.2/100    | Excellent technique            |
| `1112.mp4`             | Professional | ~4.1/100    | Solid fundamentals             |
| `hoU4DIhRpCzTj4rG.mp4` | Normal       | ~15.8/100   | Average recreational swing     |
| `Untitled00000487.mp4` | Bad          | ~86.7/100   | Multiple critical faults       |
| `Untitled00000204.mp4` | Bad          | ~72.3/100   | Poor posture, alignment issues |

---

## 📊 Output Files

All analysis results saved to `output/`:

- **`VIDEO_report.json`**: Complete analysis report

  ```json
  {
    "video": "167.mp4",
    "phase_ranges": {...},
    "fault_analysis": {
      "overall_score": 26.9,
      "critical_faults": []
    },
    "performance_prediction": {
      "BallSpeed": 88.3,
      "Distance": 220.7,
      "Carry": 187.6
    }
  }
  ```

- **`VIDEO_analysis.png`**: Wrist trajectory plot with phase regions
- **`VIDEO_annotated.mp4`**: Video with pose overlay, phase labels, slow motion

---

## 🛠️ Training Your Own Models

### 1. Prepare Training Data

```bash
# Extract CaddieSet-compatible features from all videos
python training/create_caddieset_dataset.py
```

This creates training datasets from:

- **Good swings**: Videos in `good_swings/` folder
- **Bad swings**: Videos in `bad_swings/` folder

### 2. Train Models

```bash
# Train fault detector and performance predictor
python training/train_pytorch_models.py
```

**Expected Output:**

```
✅ Training complete
   Classifier CV Accuracy: 92.3%
   Predictor R² Score: 0.67
   Feature Importance: Top features identified
```

### 3. Train Ball Detector (Module 3)

1. **Prepare YOLO dataset for the golf ball**

   - Create a dataset folder, e.g. `datasets/golf_ball/`, with standard YOLO layout:
     - `datasets/golf_ball/images/train`, `datasets/golf_ball/images/val`
     - `datasets/golf_ball/labels/train`, `datasets/golf_ball/labels/val`
   - Label the ball in each frame using a tool like LabelImg/Roboflow and export in YOLO format.
   - Add `data.yaml`:

   ```yaml
   path: ./datasets/golf_ball
   train: images/train
   val: images/val
   names:
     0: ball
   ```

2. **Run YOLOv8 training**

   ```bash
   # From project root
   python training/train_ball_detector.py --data ./datasets/golf_ball/data.yaml
   ```

   This will train a YOLOv8 detector and copy the best weights to:

   ```text
   models/ball_detector.pt
   ```

   which is what Module 3 (ball tracking & trajectory) uses at runtime.

---

## 🧪 Testing & Validation

```bash
# Test feature extraction
python test_feature_extractor.py

# Test video processing
python test_simple.py

# Test data loading
python test_data_loading.py

# Test image sequences
python test_image_sequence.py
```

---

## 📈 Performance

- **Processing Speed**: ~15-20 fps on GPU
- **ML Accuracy**: 92% cross-validation accuracy on swing classification
- **Performance Prediction**: R²=0.67 correlation with CaddieSet data
- **Phase Detection**: 6 distinct phases reliably detected
- **Video Quality**: CLAHE enhancement, bilateral filtering, sharpening
- **Memory Efficient**: Handles 1000+ frame videos
- **Features**: 126 CaddieSet-compatible biomechanical metrics extracted per frame

---

## 🎓 Example Output

```
======================================================================
Analyzing: Untitled00000487.mp4
======================================================================

[1/6] Extracting trajectories and pose data...
[2/6] Detecting swing phases...
[3/6] Extracting CaddieSet biomechanical features...
[4/6] Detecting faults using ML...

⚠️  Fault Analysis (86.7/100):
   🔴 Critical Issues:
      • BACKSWING: Shoulders tilted excessively left - level them
      • TOP: Stance too narrow - widen foot positioning
      • DOWNSWING: Early extension - maintain posture
   🟠 Moderate Issues:
      • IMPACT: Poor hip rotation sequence
      • FOLLOW_THROUGH: Incomplete finish

[5/6] Predicting shot performance...
🎯 Estimated Performance:
   Ball Speed:  88.3 mph
   Distance:    220.7 yards
   Carry:       187.6 yards

[6/6] Generating visualizations...

💾 Saved report: output/Untitled00000487_report.json
💾 Saved plot: output/Untitled00000487_analysis.png
💾 Saved video: output/Untitled00000487_annotated.mp4

======================================================================
✅ ANALYSIS COMPLETE
======================================================================
```

---

## 💡 Tips for Best Results

### Video Analysis

- **Resolution**: Any resolution works (CLAHE enhancement + upscaling for small videos)
- **Frame Rate**: 30+ fps recommended
- **Lighting**: Good lighting for better pose detection
- **Camera Angle**: Side view captures full swing motion
- **Background**: Plain background improves accuracy
- **Video Quality**: System applies CLAHE, bilateral filtering, and sharpening automatically

### Training Data

- **Labeling**: Videos starting with numbers = good, "Untitled" = bad
- **Quality**: Mix of professional and amateur swings for best results
- **Quantity**: More training data = better model performance

---

## 🚧 Troubleshooting

**"ModuleNotFoundError: No module named 'mediapipe'"**

```bash
# Install missing dependencies
pip install -r requirements.txt
```

**"Model not trained" errors**

```bash
# Train the ML models first
python training/train_golf_models.py
```

**"No pose detected"**

- Ensure full body is visible in frame
- Improve lighting conditions
- Check camera permissions

**"Phase detection incorrect"**

- Ensure side view of swing
- Check that wrists are visible throughout
- Try different video angles

---

## 🔮 Future Improvements

- [ ] Real-time swing analysis during practice
- [ ] Swing comparison (student vs pro)
- [ ] 3D pose estimation with depth
- [ ] Club head tracking
- [ ] Swing tempo and rhythm analysis
- [ ] Multi-angle video support
- [ ] Cloud deployment with API
- [ ] Mobile app integration

---

## 📜 License

MIT License - Feel free to use and modify!

---

## 🙏 Acknowledgments

- **MediaPipe** - Google's pose estimation framework
- **CaddieSet** - Professional golf swing dataset and biomechanical research (1757 swings, 69 features per phase)
- **PyTorch** - Deep learning framework with CUDA support
- **Scikit-learn** - Machine learning utilities
- **OpenCV** - Video processing and enhancement
- **Streamlit** - Web interface framework
- **NumPy/SciPy** - Scientific computing
