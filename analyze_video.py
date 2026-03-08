"""
ML-Enhanced Golf Swing Video Analysis

Combines Module 1 (pose + phase detection) with Module 2 (ML models):
- Extract pose and trajectories
- Detect swing phases
- Extract biomechanical features
- Detect faults using ML anomaly detection
- Predict shot performance
- Generate comprehensive report

Usage:
    python analyze_video.py --video path/to/video.mp4
    python analyze_video.py --video 0.mp4 --output output/analysis_0
"""

import argparse
import sys
from pathlib import Path
import yaml
import json
import numpy as np
from typing import List, Dict, Tuple, Optional

sys.path.append(str(Path(__file__).parent))

from utils.trajectory_extractor import TrajectoryExtractor
from utils.swing_phase_analyzer import SwingPhaseAnalyzer
from utils.feature_extractor import FeatureExtractor
from utils.video_processor import VideoProcessor
from utils.visualizer import SwingVisualizer
from models.fault_detector import FaultDetector
from models.performance_predictor import PerformancePredictor
from models.ball_detector import BallDetector
from pose_detector import PoseDetector
from training.caddieset_feature_extractor import CaddieSetFeatureExtractor
from utils.ball_tracker import BallTracker, BallTrajectoryPoint
from utils.distance_estimator import DistanceEstimator


class MLSwingAnalyzer:
    """
    ML-enhanced golf swing analyzer

    Integrates Module 1 and Module 2:
    - Pose detection + phase classification (Module 1)
    - Feature extraction + ML predictions (Module 2)
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize analyzer

        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Module 1 components
        self.pose_detector = PoseDetector(config_path)
        self.trajectory_extractor = TrajectoryExtractor()
        self.phase_analyzer = SwingPhaseAnalyzer()
        self.video_processor = VideoProcessor()
        self.visualizer = SwingVisualizer()

        # Module 2 components
        self.feature_extractor = FeatureExtractor(config_path)
        self.caddieset_extractor = CaddieSetFeatureExtractor()  # CaddieSet-compatible extractor
        self.fault_detector = None
        self.performance_predictor = None

        # Module 3 components (Ball tracking & trajectory)
        module3_cfg = (self.config or {}).get("module3", {}) or {}
        ball_det_cfg = module3_cfg.get("ball_detection", {}) or {}
        ball_track_cfg = module3_cfg.get("ball_tracking", {}) or {}
        dist_cfg = module3_cfg.get("distance_estimation", {}) or {}

        self.module3_enabled: bool = bool(module3_cfg.get("enabled", False))
        self.ball_detector: Optional[BallDetector] = None
        self.ball_tracker: Optional[BallTracker] = None
        self.distance_estimator: Optional[DistanceEstimator] = None

        # Try to load trained models
        self._load_models()

    def _load_models(self):
        """Load trained ML models if available (supports .pt PyTorch and .pkl pickle formats)"""
        # Try PyTorch models first (.pt), then fall back to pickle (.pkl)
        fault_model_path = Path("models/fault_detector.pt")
        if not fault_model_path.exists():
            fault_model_path = Path("models/fault_detector.pkl")
        
        perf_model_path = Path("models/performance_predictor.pt")
        if not perf_model_path.exists():
            perf_model_path = Path("models/performance_predictor.pkl")

        if fault_model_path.exists():
            try:
                self.fault_detector = FaultDetector()
                self.fault_detector.load(str(fault_model_path))
                print("✅ Loaded fault detection model")
            except Exception as e:
                print(f"⚠️  Could not load fault detector: {e}")

        if perf_model_path.exists():
            try:
                self.performance_predictor = PerformancePredictor()
                self.performance_predictor.load(str(perf_model_path))
                print("✅ Loaded performance prediction model")
            except Exception as e:
                print(f"⚠️  Could not load performance predictor: {e}")

        # Module 3: Ball detector, tracker, and distance estimator
        module3_cfg = (self.config or {}).get("module3", {}) or {}
        if module3_cfg.get("enabled", False):
            ball_det_cfg = module3_cfg.get("ball_detection", {}) or {}
            ball_track_cfg = module3_cfg.get("ball_tracking", {}) or {}
            dist_cfg = module3_cfg.get("distance_estimation", {}) or {}

            try:
                self.ball_detector = BallDetector(
                    model_path=ball_det_cfg.get("model_path", "models/ball_detector.pt"),
                    conf_threshold=ball_det_cfg.get("conf_threshold", 0.4),
                    iou_threshold=ball_det_cfg.get("iou_threshold", 0.45),
                    device=ball_det_cfg.get("device", "auto"),
                )
                self.ball_tracker = BallTracker(
                    window_before_impact=ball_track_cfg.get("window_before_impact", 5),
                    window_after_impact=ball_track_cfg.get("window_after_impact", 70),
                    min_confidence=ball_track_cfg.get("min_confidence", 0.4),
                    max_interpolation_gap=ball_track_cfg.get("max_interpolation_gap", 5),
                )
                self.distance_estimator = DistanceEstimator(
                    pixel_to_meter=dist_cfg.get("pixel_to_meter", 0.02),
                    gravity=dist_cfg.get("gravity", 9.81),
                    min_points=dist_cfg.get("min_points", 6),
                )
                self.module3_enabled = True
                print("✅ Module 3 (ball tracking) enabled")
            except Exception as e:
                # If anything fails, gracefully disable Module 3
                print(f"⚠️  Could not initialize Module 3 (ball tracking): {e}")
                self.ball_detector = None
                self.ball_tracker = None
                self.distance_estimator = None
                self.module3_enabled = False

    def analyze_video(
        self,
        video_path: str,
        output_dir: str = "output",
        verbose: bool = True,
        skip_video_render: bool = False
    ) -> dict:
        """
        Comprehensive video analysis with ML enhancements

        Args:
            video_path: Path to video file
            output_dir: Output directory
            verbose: Show progress
            skip_video_render: Skip creating annotated video (much faster)

        Returns:
            Complete analysis results
        """
        video_path = Path(video_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if verbose:
            print("\n" + "=" * 70)
            print(f"Analyzing: {video_path.name}")
            print("=" * 70)

        # =====================================================================
        # STEP 1: Extract trajectories and pose data (Module 1)
        # =====================================================================
        if verbose:
            print("\n[1/6] Extracting trajectories and pose data...")

        # Clear cached landmarks from previous runs
        self.trajectory_extractor.cached_landmarks = []
        
        frame_data = self.trajectory_extractor.extract_from_video(
            str(video_path),
            verbose=verbose,
            preprocess=False  # Disabled preprocessing for speed
        )

        # =====================================================================
        # STEP 2: Detect swing phases (Module 1)
        # =====================================================================
        if verbose:
            print("\n[2/6] Detecting swing phases...")

        phase_ranges, swing_start, swing_end, wrist_y, smoothed = \
            self.phase_analyzer.detect_phases(frame_data)

        if verbose:
            print("\n📊 Detected phases:")
            for phase, (start, end) in phase_ranges.items():
                duration = end - start + 1
                print(f"   {phase:20s}: frames {start:4d}-{end:4d} ({duration:3d} frames)")

        # =====================================================================
        # STEP 3: Extract biomechanical features (Module 2)
        # =====================================================================
        if verbose:
            print("\n[3/6] Extracting biomechanical features...")

        # Use cached landmarks from trajectory extraction (no reprocessing!)
        import cv2
        cap = cv2.VideoCapture(str(video_path))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        cap.release()

        features_sequence = []
        landmarks_sequence = self.trajectory_extractor.cached_landmarks

        for i, landmarks in enumerate(landmarks_sequence):
            if landmarks is not None:
                features = self.feature_extractor.extract_features(
                    landmarks,
                    frame_height=frame_height,
                    frame_width=frame_width
                )
                features_sequence.append(features)
            else:
                features_sequence.append(self.feature_extractor._get_empty_features())

        if verbose:
            valid_features = sum(1 for f in features_sequence if f.get('SPINE_ANGLE') is not None)
            print(f"   Extracted features from {valid_features}/{len(frame_data)} frames")

        # =====================================================================
        # STEP 4: ML Fault Detection (Module 2)
        # =====================================================================
        if verbose:
            print("\n[4/6] Detecting faults using ML...")

        fault_results = None
        if self.fault_detector:
            # Use CaddieSet feature extractor (proper feature extraction)
            caddieset_features = self.caddieset_extractor.extract_from_video(
                str(video_path), verbose=False, preprocess=False
            )
            
            # Predict using CaddieSet-compatible features
            score, messages, details = self.fault_detector.predict(caddieset_features)
            
            fault_results = {
                'overall_score': score,
                'details': details,
                'messages': messages
            }

            if verbose:
                print(f"\n⚠️  Fault Analysis:")
                print(f"   Overall Fault Score: {fault_results['overall_score']:.1f}/100")
                print(f"   (Higher score = more faults detected)")
                
                # Interpret the score
                if score >= 70:
                    print("   ❌ Significant technique issues detected!")
                    swing_quality = "Poor"
                elif score >= 50:
                    print("   ⚠️ Several technique issues found - needs improvement")
                    swing_quality = "Needs Work"
                elif score >= 30:
                    print("   ✓ Minor form variations - acceptable technique")
                    swing_quality = "Good"
                else:
                    print("   ✅ Professional-level technique!")
                    swing_quality = "Excellent"
                
                fault_results['swing_quality'] = swing_quality
                
                # Show fault summary by severity
                if details.get('summary', {}).get('total_faults', 0) > 0:
                    summary = details['summary']
                    print(f"\n   📊 Fault Summary:")
                    print(f"      Total: {summary['total_faults']} issues found")
                    if summary['critical_count'] > 0:
                        print(f"      🔴 Critical: {summary['critical_count']}")
                    if summary['major_count'] > 0:
                        print(f"      🟠 Major: {summary['major_count']}")
                    if summary['minor_count'] > 0:
                        print(f"      🟡 Minor: {summary['minor_count']}")
                    
                    # Show faults grouped by phase
                    print(f"\n   📍 Issues by Phase:")
                    phase_order = ['ADDRESS', 'BACKSWING', 'TOP', 'DOWNSWING', 'IMPACT', 'FOLLOW_THROUGH']
                    for phase in phase_order:
                        phase_faults = details.get('by_phase', {}).get(phase, [])
                        if phase_faults:
                            print(f"\n      {phase}:")
                            for fault in phase_faults:
                                severity_emoji = {'critical': '🔴', 'major': '🟠', 'minor': '🟡'}
                                emoji = severity_emoji.get(fault['severity'], '⚠️')
                                print(f"         {emoji} {fault['title']}")
                                print(f"            Issue: {fault['description']}")
                                print(f"            Fix: {fault['fix']}")
        else:
            if verbose:
                print("   ⚠️  Fault detector not loaded - skipping")

        # =====================================================================
        # STEP 5: ML Performance Prediction (Module 2)
        # =====================================================================
        if verbose:
            print("\n[5/6] Predicting shot performance...")

        performance_results = None
        if self.performance_predictor:
            # Reuse CaddieSet features from fault detection
            if not fault_results:
                # Extract if fault detection was skipped
                caddieset_features = self.caddieset_extractor.extract_from_video(
                    str(video_path), verbose=False, preprocess=False
                )
            
            # Predict performance using CaddieSet-compatible features
            performance_results = self.performance_predictor.predict(caddieset_features)

            if verbose:
                print(f"\n🎯 Estimated Performance:")
                print(f"   Ball Speed:  {performance_results['BallSpeed']:.1f} mph")
                print(f"   Distance:    {performance_results['Distance']:.1f} yards")
                print(f"   Carry:       {performance_results['Carry']:.1f} yards")
                print(f"   Confidence:  {performance_results['confidence']:.1f}%")
        else:
            if verbose:
                print("   ⚠️  Performance predictor not loaded - using heuristics")
            
            # Use heuristics even without ML model
            phase_aggregated = self._aggregate_features_by_phase(
                features_sequence, phase_ranges
            )
            performance_results = self._estimate_performance(phase_aggregated)
            
            if verbose:
                print(f"\n🎯 Estimated Performance (Heuristic):")
                print(f"   Ball Speed:  {performance_results['BallSpeed']:.1f} mph")
                print(f"   Distance:    {performance_results['Distance']:.1f} yards")
                print(f"   Carry:       {performance_results['Carry']:.1f} yards")

        # =====================================================================
        # STEP 6: Module 3 - Ball Tracking & Distance Estimation (optional)
        # =====================================================================
        ball_trajectory: Optional[List[BallTrajectoryPoint]] = None
        ball_quality: Optional[Dict[str, float]] = None
        ball_distance: Optional[Dict[str, float]] = None

        if self.module3_enabled and self.ball_detector and self.ball_tracker:
            if verbose:
                print("\n[6/6] Tracking ball trajectory (Module 3)...")

            impact_range = phase_ranges.get("IMPACT")
            if impact_range is not None:
                try:
                    ball_trajectory, ball_quality = self.ball_tracker.track(
                        str(video_path),
                        impact_range=tuple(impact_range),
                        fps=float(fps),
                        detector=self.ball_detector,
                    )
                    if ball_trajectory and self.distance_estimator:
                        ball_distance = self.distance_estimator.estimate(
                            ball_trajectory,
                            quality_metrics=ball_quality,
                        )
                except Exception as e:
                    if verbose:
                        print(f"   ⚠️  Ball tracking failed: {e}")
                    ball_trajectory = None
                    ball_quality = {"status": "error"}
                    ball_distance = None
            else:
                if verbose:
                    print("   ⚠️  No IMPACT phase detected - skipping ball tracking")

        # If Module 3 vision distance is unavailable or low quality, fall back
        # to Module 2 performance prediction for FR-3.4
        ball_tracking_section = self._build_ball_tracking_section(
            ball_trajectory=ball_trajectory,
            ball_quality=ball_quality,
            ball_distance=ball_distance,
            performance_results=performance_results,
        )

        # =====================================================================
        # STEP 7: Generate visualizations and report
        # =====================================================================
        if verbose:
            print("\n[7/7] Generating visualizations...")

        # Create plots
        plot_path = output_dir / f"{video_path.stem}_analysis.png"
        self.visualizer.plot_swing_analysis(
            wrist_y, smoothed, phase_ranges,
            swing_start, swing_end,
            str(plot_path)
        )

        ball_plot_path = None
        if ball_trajectory:
            ball_plot_path = output_dir / f"{video_path.stem}_ball_trajectory.png"
            try:
                self.visualizer.plot_ball_trajectory(
                    ball_trajectory,
                    phase_ranges,
                    str(ball_plot_path),
                )
            except Exception as e:
                if verbose:
                    print(f"   ⚠️  Could not create ball trajectory plot: {e}")
                ball_plot_path = None

        # Create annotated video (optional - can be skipped for speed)
        annotated_video_path = None
        if not skip_video_render:
            annotated_video_path = output_dir / f"{video_path.stem}_annotated.mp4"
            self.video_processor.create_annotated_video(
                str(video_path),
                str(annotated_video_path),
                phase_ranges,
                show_pose=True,
                slow_motion=0.5,
                ball_trajectory=ball_trajectory,
                faults_by_phase=fault_results.get('details', {}).get('by_phase') if fault_results else None,
            )
        elif verbose:
            print("   Skipping video rendering (use skip_video_render=False to enable)")

        # =====================================================================
        # Create comprehensive JSON report
        # =====================================================================

        # Helper function to convert numpy types to native Python types
        def convert_to_serializable(obj):
            """Convert numpy types to JSON serializable types"""
            import numpy as np
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            elif isinstance(obj, tuple):
                return [convert_to_serializable(item) for item in obj]
            else:
                return obj

        # Optional CSV/JSON export of ball trajectory
        if ball_trajectory:
            import csv
            ball_csv_path = output_dir / f"{video_path.stem}_ball_traj.csv"
            ball_json_path = output_dir / f"{video_path.stem}_ball_traj.json"

            try:
                with open(ball_csv_path, "w", newline="") as f_csv:
                    writer = csv.writer(f_csv)
                    writer.writerow(["frame", "t_sec", "x_px", "y_px", "confidence"])
                    for pt in ball_trajectory:
                        writer.writerow(
                            [
                                int(pt.frame),
                                float(pt.t_sec),
                                float(pt.x) if pt.x is not None else "",
                                float(pt.y) if pt.y is not None else "",
                                float(pt.confidence),
                            ]
                        )
            except Exception as e:
                if verbose:
                    print(f"   ⚠️  Could not write ball trajectory CSV: {e}")
                ball_csv_path = None

            try:
                with open(ball_json_path, "w") as f_json:
                    json.dump(
                        [
                            {
                                "frame": int(pt.frame),
                                "t_sec": float(pt.t_sec),
                                "x_px": float(pt.x) if pt.x is not None else None,
                                "y_px": float(pt.y) if pt.y is not None else None,
                                "confidence": float(pt.confidence),
                            }
                            for pt in ball_trajectory
                        ],
                        f_json,
                        indent=2,
                    )
            except Exception as e:
                if verbose:
                    print(f"   ⚠️  Could not write ball trajectory JSON: {e}")
                ball_json_path = None
        else:
            ball_csv_path = None
            ball_json_path = None

        # Attach file paths into ball_tracking section
        if ball_tracking_section:
            files = ball_tracking_section.get("files", {}) or {}
            files.update(
                {
                    "csv": str(ball_csv_path) if ball_csv_path else None,
                    "json": str(ball_json_path) if ball_json_path else None,
                    "plot": str(ball_plot_path) if ball_plot_path else None,
                }
            )
            ball_tracking_section["files"] = files

        # ---------------------------------------------------------------------
        # Build per-phase fault summary for easy UI consumption
        # ---------------------------------------------------------------------
        phase_fault_summary = {}
        if fault_results:
            details = fault_results.get("details") or {}
            by_phase = details.get("by_phase") or {}

            # Fixed order for 6-phase golf swing
            phase_order = [
                "ADDRESS",
                "BACKSWING",
                "TOP",
                "DOWNSWING",
                "IMPACT",
                "FOLLOW_THROUGH",
            ]
            severity_weights = {"minor": 1, "major": 2, "critical": 3}
            severity_rank = ["none", "minor", "major", "critical"]

            for phase_name in phase_order:
                faults = by_phase.get(phase_name) or []

                counts = {"critical": 0, "major": 0, "minor": 0}
                for fault in faults:
                    sev = (fault.get("severity") or "").lower()
                    if sev in counts:
                        counts[sev] += 1

                # Determine maximum severity present in this phase
                max_severity = "none"
                for sev in ("critical", "major", "minor"):
                    if counts[sev] > 0:
                        max_severity = sev
                        break

                # Simple phase score for visualization only (0–100)
                weighted_sum = sum(
                    counts[sev] * severity_weights[sev] for sev in counts
                )
                # Assume up to ~8 weighted units per phase → scale into 0–100
                phase_score = 0.0
                if weighted_sum > 0:
                    phase_score = float(min(100.0, (weighted_sum / 8.0) * 100.0))

                top_fault_titles = [
                    f.get("title", "") for f in faults if f.get("title")
                ][:3]

                phase_fault_summary[phase_name] = {
                    "max_severity": max_severity,
                    "counts": counts,
                    "score": phase_score,
                    "top_fault_titles": top_fault_titles,
                }

        report = {
            'video': str(video_path),
            'phase_ranges': {k: [int(v[0]), int(v[1])] for k, v in phase_ranges.items()},
            'swing_frames': {'start': int(swing_start), 'end': int(swing_end)},
            'fault_analysis': {
                'overall_score': float(fault_results['overall_score']) if fault_results else None,
                'swing_quality': fault_results.get('swing_quality', 'Unknown') if fault_results else 'Unknown',
                'fault_details': fault_results.get('details', {}) if fault_results else {},
                'messages': fault_results.get('messages', []) if fault_results else [],
                'critical_faults': [
                    msg for msg in fault_results.get('messages', []) 
                    if '🔴' in msg
                ] if fault_results else []
            },
            'phase_fault_summary': convert_to_serializable(phase_fault_summary),
            'performance_prediction': convert_to_serializable(performance_results) if performance_results else None,
            'ball_tracking': convert_to_serializable(ball_tracking_section),
            'outputs': {
                'plot': str(plot_path),
                'annotated_video': str(annotated_video_path) if annotated_video_path else None,
                'ball_plot': str(ball_plot_path) if ball_plot_path else None,
            }
        }

        # Save report
        report_path = output_dir / f"{video_path.stem}_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        if verbose:
            print(f"\n💾 Saved report: {report_path}")
            print(f"💾 Saved plot: {plot_path}")
            if annotated_video_path:
                print(f"💾 Saved video: {annotated_video_path}")

        print("\n" + "=" * 70)
        print("✅ ANALYSIS COMPLETE")
        print("=" * 70)

        return report

    def _extract_caddieset_features_from_cache(
        self,
        landmarks_sequence: List,
        phase_ranges: Dict[str, Tuple[int, int]],
        frame_height: int,
        frame_width: int
    ) -> Dict[str, float]:
        """
        Extract CaddieSet features from cached landmarks (avoids video reprocessing)
        
        Args:
            landmarks_sequence: Cached pose landmarks from trajectory extraction
            phase_ranges: Phase ranges dictionary
            frame_height: Original video height
            frame_width: Original video width
            
        Returns:
            Dictionary with phase-prefixed CaddieSet features
        """
        # Convert landmarks to CaddieSet format
        caddieset_landmarks = []
        for lm in landmarks_sequence:
            if lm is not None:
                # Convert from our format to CaddieSet format (x, y, z)
                caddieset_lm = lm[:, :3]  # Take only x, y, z (drop visibility)
                caddieset_landmarks.append(caddieset_lm)
            else:
                caddieset_landmarks.append(None)
        
        # Map phase names to indices
        PHASE_NAME_TO_INDEX = {
            'ADDRESS': 0,
            'BACKSWING': 1,
            'TOP': 2,
            'DOWNSWING': 3,
            'IMPACT': 4,
            'FOLLOW_THROUGH': 5
        }
        
        # Convert phase_ranges to phase indices format
        phases = {}
        for name, (start, end) in phase_ranges.items():
            if name in PHASE_NAME_TO_INDEX:
                phases[PHASE_NAME_TO_INDEX[name]] = (start, end)
        
        # Use caddieset_extractor's feature extraction on cached data
        phase_features = {}
        
        for phase_idx in range(6):
            if phase_idx not in phases:
                continue
                
            start_frame, end_frame = phases[phase_idx]
            
            # Get landmarks for this phase
            phase_landmarks = [
                caddieset_landmarks[i] 
                for i in range(start_frame, min(end_frame + 1, len(caddieset_landmarks)))
                if caddieset_landmarks[i] is not None
            ]
            
            if not phase_landmarks:
                continue
            
            # Aggregate landmarks (median across phase)
            aggregated_lm = np.median(phase_landmarks, axis=0)
            
            # Extract features for this phase
            features = self.caddieset_extractor.extract_frame_features(
                aggregated_lm,
                frame_height,
                frame_width
            )
            
            # Add phase prefix
            for feature_name, value in features.items():
                phase_features[f"{phase_idx}-{feature_name}"] = value
        
        return phase_features

    def _aggregate_features_by_phase(
        self,
        features_sequence: List[Dict],
        phase_ranges: Dict[str, Tuple[int, int]]
    ) -> Dict:
        """
        Aggregate features by phase to match CaddieSet format
        
        Args:
            features_sequence: List of per-frame features
            phase_ranges: Dict mapping phase names to (start, end) frame indices
            
        Returns:
            Single dict with CaddieSet-compatible phase-prefixed features
            e.g., '0-SHOULDER-ANGLE', '1-HEAD-LOC', etc.
        """
        import numpy as np
        
        # Map phase names to CaddieSet phase indices (6 phases)
        PHASE_NAME_TO_INDEX = {
            'ADDRESS': 0,
            'BACKSWING': 1,
            'TOP': 2,
            'DOWNSWING': 3,
            'IMPACT': 4,
            'FOLLOW_THROUGH': 5
        }
        
        # Aggregate features for each phase
        phase_features_map = {}
        global_values = {}
        global_counts = {}
        
        # Store address reference for relative calculations
        address_reference = {}
        
        for phase_name, (start_frame, end_frame) in phase_ranges.items():
            phase_idx = PHASE_NAME_TO_INDEX.get(phase_name, -1)
            if phase_idx < 0:
                continue
                
            # Extract features for this phase
            phase_frame_features = features_sequence[start_frame:min(end_frame+1, len(features_sequence))]
            
            # Skip if no frames in this phase
            if not phase_frame_features:
                continue
            
            # Aggregate (median for robustness) across frames in this phase
            for key in features_sequence[0].keys():
                values = [
                    f[key] for f in phase_frame_features
                    if f.get(key) is not None and not np.isnan(f.get(key, np.nan))
                ]
                if values:
                    # Use CaddieSet naming: PHASE_IDX-FEATURE-NAME (with dashes)
                    caddieset_key = key.replace('_', '-')
                    avg_value = np.median(values)
                    phase_features_map[f'{phase_idx}-{caddieset_key}'] = avg_value
                    
                    # Store address reference
                    if phase_idx == 0:
                        address_reference[key] = avg_value
                    
                    # Also add with underscore format for compatibility
                    phase_features_map[f'{phase_name}_{key}'] = avg_value

                # Track global aggregates (without phase prefix)
                global_values.setdefault(key, 0.0)
                global_counts.setdefault(key, 0)
                for v in values:
                    global_values[key] += v
                    global_counts[key] += 1
        
        # Add overall averages for ML models expecting phase-agnostic features
        for key, total in global_values.items():
            count = max(global_counts.get(key, 1), 1)
            phase_features_map[key] = total / count
        
        return phase_features_map

    def _estimate_performance(self, phase_features: Dict) -> Dict:
        """
        Heuristic-based performance estimation from biomechanics
        
        Estimates ball speed and distance based on:
        - Hip rotation speed (power generation)
        - X-factor (shoulder-hip separation)
        - Impact efficiency
        """
        import numpy as np
        
        # Default values
        base_speed = 50.0
        base_distance = 150.0
        
        # Get key biomechanical indicators
        hip_rotation_backswing = phase_features.get('BACKSWING_HIP_ROTATION', 0)
        hip_rotation_downswing = phase_features.get('DOWNSWING_HIP_ROTATION', 0)
        x_factor = phase_features.get('TOP_X_FACTOR', 0)
        spine_angle_impact = phase_features.get('IMPACT_SPINE_ANGLE', 30)
        
        # Hip rotation range (more rotation = more power)
        hip_range = abs(hip_rotation_downswing - hip_rotation_backswing)
        speed_from_rotation = (hip_range / 90.0) * 20  # Up to +20 mph
        
        # X-factor (shoulder-hip separation)
        speed_from_xfactor = (abs(x_factor) / 45.0) * 15  # Up to +15 mph
        
        # Spine angle at impact (30-40° is optimal)
        if 25 <= spine_angle_impact <= 45:
            speed_from_spine = 10
        else:
            speed_from_spine = 5
        
        # Calculate ball speed
        ball_speed = base_speed + speed_from_rotation + speed_from_xfactor + speed_from_spine
        ball_speed = np.clip(ball_speed, 30, 120)  # Realistic range
        
        # Distance estimation (rough formula)
        # Distance ≈ Ball Speed × 2.5 (for average conditions)
        distance = ball_speed * 2.5
        carry = distance * 0.85  # Carry is ~85% of total distance
        
        # Confidence based on feature availability
        available_features = sum(1 for v in phase_features.values() if v is not None and v != 0)
        total_possible = len(phase_features) if len(phase_features) > 0 else 1
        confidence = (available_features / total_possible) * 100
        
        return {
            'BallSpeed': float(ball_speed),
            'Distance': float(distance),
            'Carry': float(carry),
            'confidence': float(confidence)
        }

    def _build_ball_tracking_section(
        self,
        ball_trajectory: Optional[List[BallTrajectoryPoint]],
        ball_quality: Optional[Dict[str, float]],
        ball_distance: Optional[Dict[str, float]],
        performance_results: Optional[Dict],
    ) -> Dict:
        """
        Build the ball_tracking section for the analysis report, including
        FR-3.4 fallback to pose/ML-based distance when vision is unreliable.
        """
        if not self.module3_enabled or not ball_trajectory:
            # Module 3 disabled or no trajectory: fall back directly to Module 2
            fallback = None
            if performance_results:
                fallback = {
                    "carry_yards": performance_results.get("Carry"),
                    "distance_yards": performance_results.get("Distance"),
                    "confidence": performance_results.get("confidence"),
                    "method": "ml_pose_fallback",
                    "notes": "Module 3 disabled or no ball trajectory; using Module 2 performance prediction.",
                }

            return {
                "enabled": bool(self.module3_enabled),
                "status": "fallback" if fallback else "disabled",
                "quality": ball_quality or {},
                "distance_estimation": fallback,
                "trajectory_2d": [],
                "files": {},
            }

        # We have a trajectory; decide whether to trust the vision estimate
        quality = ball_quality or {}
        vision = ball_distance

        status = quality.get("status", "ok")
        detection_rate = float(quality.get("detection_rate", 0.0))
        longest_gap = float(quality.get("longest_gap_frames", 0.0))
        num_frames = float(quality.get("num_frames", len(ball_trajectory)))

        # Heuristics for "good enough" vision:
        # - detection_rate >= 0.6
        # - longest_gap <= 0.3 * num_frames
        good_vision = (
            status == "ok"
            and detection_rate >= 0.6
            and (num_frames == 0 or longest_gap <= 0.3 * num_frames)
            and vision is not None
        )

        if good_vision:
            distance_estimation = {
                "carry_yards": vision["carry_yards"],
                "distance_yards": vision["distance_yards"],
                "confidence": vision["confidence"],
                "method": "vision",
                "notes": vision.get("notes", "vision_only"),
            }
            final_status = "success"
        else:
            # Vision unreliable: fall back to Module 2 (FR-3.4)
            distance_estimation = None
            if performance_results:
                distance_estimation = {
                    "carry_yards": performance_results.get("Carry"),
                    "distance_yards": performance_results.get("Distance"),
                    "confidence": performance_results.get("confidence"),
                    "method": "ml_pose_fallback",
                    "notes": "Vision-based tracking unreliable; using Module 2 performance prediction.",
                }
            final_status = "partial" if vision is not None else "failed"

        traj_serialized = [
            {
                "frame": int(pt.frame),
                "t": float(pt.t_sec),
                "x": float(pt.x) if pt.x is not None else None,
                "y": float(pt.y) if pt.y is not None else None,
                "confidence": float(pt.confidence),
            }
            for pt in ball_trajectory
        ]

        return {
            "enabled": True,
            "status": final_status,
            "quality": quality,
            "distance_estimation": distance_estimation,
            "trajectory_2d": traj_serialized,
            "files": {},  # Filled by caller if CSV/JSON exports are added later
        }


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(description="ML-Enhanced Golf Swing Analysis")
    parser.add_argument('--video', type=str, required=True, help='Path to video file')
    parser.add_argument('--output', type=str, default='output', help='Output directory')
    parser.add_argument('--config', type=str, default='config.yaml', help='Config file')
    parser.add_argument('--skip-video', action='store_true', 
                       help='Skip video rendering for faster analysis (only generate plots and report)')
    parser.add_argument('--fast', action='store_true',
                       help='Fast mode: skip video rendering (alias for --skip-video)')

    args = parser.parse_args()

    # Check if video exists
    if not Path(args.video).exists():
        print(f"❌ Error: Video file not found: {args.video}")
        return

    # Check if models are trained (support both .pt and .pkl formats)
    fault_model_exists = Path("models/fault_detector.pt").exists() or Path("models/fault_detector.pkl").exists()
    perf_model_exists = Path("models/performance_predictor.pt").exists() or Path("models/performance_predictor.pkl").exists()
    
    if not fault_model_exists or not perf_model_exists:
        print("\n⚠️  WARNING: ML models not found!")
        print("   Please run: python training/run_pytorch_training_pipeline.py")
        print("   Continuing with Module 1 only (no ML enhancements)...\n")

    # Run analysis
    skip_video = args.skip_video or args.fast
    if skip_video:
        print("\n⚡ Fast mode enabled - skipping video rendering\n")
    
    analyzer = MLSwingAnalyzer(args.config)
    report = analyzer.analyze_video(args.video, args.output, skip_video_render=skip_video)

    # Print summary
    print("\n📊 Analysis Summary:")
    print(f"   Video: {args.video}")
    print(f"   Phases detected: {len(report['phase_ranges'])}")
    if report['fault_analysis']['overall_score']:
        print(f"   Fault score: {report['fault_analysis']['overall_score']:.1f}/100")
    if report['performance_prediction']:
        print(f"   Predicted distance: {report['performance_prediction']['Distance']:.1f} yards")


if __name__ == "__main__":
    main()
