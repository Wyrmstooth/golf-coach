"""
🏌️ Golf Swing Phase Detection - Main Module
Clean orchestrator using modular components for swing analysis
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Import our custom modules
from utils.trajectory_extractor import TrajectoryExtractor
from utils.swing_phase_analyzer import SwingPhaseAnalyzer
from utils.visualizer import SwingVisualizer
from utils.video_processor import VideoProcessor


def analyze_video(video_path: str, output_dir: str = "output") -> Tuple[Dict, List[Dict]]:
    """
    Complete analysis pipeline for a golf swing video
    
    Args:
        video_path: Path to video file
        output_dir: Directory for output files
    
    Returns:
        (phase_ranges, frame_data)
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    video_name = Path(video_path).stem
    
    print(f"\n{'='*60}")
    print(f"🏌️ ANALYZING: {video_name}")
    print(f"{'='*60}\n")
    
    # Step 1: Extract trajectories
    extractor = TrajectoryExtractor()
    frame_data = extractor.extract_from_video(video_path, verbose=True)
    
    # Step 2: Detect phases
    print("\n🔍 Detecting swing phases...")
    analyzer = SwingPhaseAnalyzer()
    phase_ranges, swing_start, swing_end, wrist_y, smoothed = analyzer.detect_phases(frame_data)
    
    print("\n📊 Phase Ranges:")
    for phase, (start, end) in phase_ranges.items():
        duration = end - start + 1
        print(f"   {phase:15s}: frames {start:4d}-{end:4d} ({duration:3d} frames)")
    
    # Step 3: Plot trajectory
    visualizer = SwingVisualizer()
    plot_path = output_path / f"{video_name}_trajectory.png"
    visualizer.plot_trajectory(frame_data, phase_ranges, str(plot_path))
    
    # Step 4: Generate annotated video
    processor = VideoProcessor()
    annotated_path = output_path / f"{video_name}_annotated.mp4"
    processor.create_annotated_video(
        video_path,
        str(annotated_path),
        phase_ranges,
        show_pose=True,
        slow_motion=0.5
    )
    
    print(f"\n{'='*60}")
    print(f"✅ ANALYSIS COMPLETE: {video_name}")
    print(f"{'='*60}\n")
    
    return phase_ranges, frame_data


def analyze_image_sequence(
    image_dir: str,
    output_dir: str = "output",
    fps: int = 30
) -> Tuple[Dict, List[Dict]]:
    """
    Analyze golf swing from image sequence (like golfswing dataset)
    
    Args:
        image_dir: Directory containing sequential images
        output_dir: Output directory for results
        fps: Frame rate for output video
    
    Returns:
        (phase_ranges, frame_data)
    """
    # Get all images
    image_path = Path(image_dir)
    image_files = sorted(image_path.glob("*.jpg")) + sorted(image_path.glob("*.png"))
    
    if len(image_files) == 0:
        print(f"❌ No images found in {image_dir}")
        return {}, []
    
    sequence_name = image_path.name
    
    print(f"\n{'='*60}")
    print(f"🏌️ ANALYZING IMAGE SEQUENCE: {sequence_name}")
    print(f"{'='*60}")
    print(f"   Found {len(image_files)} images\n")
    
    # Step 1: Extract trajectories from images
    extractor = TrajectoryExtractor()
    frame_data = extractor.extract_from_images(image_files, verbose=True)
    
    # Step 2: Detect phases
    print("\n🔍 Detecting swing phases...")
    analyzer = SwingPhaseAnalyzer()
    phase_ranges, swing_start, swing_end, wrist_y, smoothed = analyzer.detect_phases(frame_data)
    
    print("\n📊 Phase Ranges:")
    for phase, (start, end) in phase_ranges.items():
        duration = end - start + 1
        print(f"   {phase:15s}: frames {start:4d}-{end:4d} ({duration:3d} frames)")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Step 3: Plot trajectory
    visualizer = SwingVisualizer()
    plot_path = output_path / f"{sequence_name}_trajectory.png"
    visualizer.plot_trajectory(frame_data, phase_ranges, str(plot_path))
    
    # Step 4: Generate video from images
    processor = VideoProcessor()
    video_path = output_path / f"{sequence_name}_annotated.mp4"
    processor.create_video_from_images(
        image_files,
        str(video_path),
        phase_ranges,
        fps=fps,
        show_pose=True
    )
    
    print(f"\n{'='*60}")
    print(f"✅ ANALYSIS COMPLETE: {sequence_name}")
    print(f"{'='*60}\n")
    
    return phase_ranges, frame_data


def live_mode():
    """
    🎥 LIVE MODE: Real-time golf swing phase detection from webcam
    
    Press 'q' to quit
    Press 'r' to reset wrist history
    """
    import mediapipe as mp
    
    print("\n" + "="*60)
    print("🎥 LIVE GOLF SWING ANALYZER")
    print("="*60)
    print("📹 Starting webcam...")
    print("   Press 'q' to quit")
    print("   Press 'r' to reset\n")
    
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    mp_style = mp.solutions.drawing_styles
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    if not cap.isOpened():
        print("❌ Error: Could not open webcam")
        return
    
    # Phase colors
    PHASE_COLORS = {
        "ADDRESS": (128, 128, 128),
        "BACKSWING": (255, 0, 0),
        "TOP": (0, 165, 255),
        "DOWNSWING": (0, 255, 0),
        "IMPACT": (0, 0, 255),
        "FOLLOW_THROUGH": (128, 0, 128),
        "READY": (255, 255, 255)
    }
    
    wrist_history = []
    frame_count = 0
    current_phase = "READY"
    
    pose = mp_pose.Pose(static_image_mode=False, model_complexity=2)
    analyzer = SwingPhaseAnalyzer()
    
    print("✅ Camera ready! Start your swing...\n")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to grab frame")
                break
            
            # Mirror for natural view
            frame = cv2.flip(frame, 1)
            height, width = frame.shape[:2]
            
            # Detect pose
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)
            
            if results.pose_landmarks:
                # Draw pose skeleton
                mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_style.get_default_pose_landmarks_style()
                )
                
                # Get wrist Y position
                lm = results.pose_landmarks.landmark
                lw = lm[mp_pose.PoseLandmark.LEFT_WRIST]
                rw = lm[mp_pose.PoseLandmark.RIGHT_WRIST]
                
                visible_wrists = [p for p in (lw, rw) if p.visibility > 0.4]
                
                if visible_wrists:
                    wrist_y = np.mean([p.y for p in visible_wrists]) * height
                    wrist_history.append({"frame_idx": frame_count, "wrist_y": wrist_y})
                    
                    # Keep last 300 frames (10 seconds at 30fps)
                    if len(wrist_history) > 300:
                        wrist_history = wrist_history[-300:]
                    
                    # Detect phase if we have enough data
                    if len(wrist_history) > 50:
                        try:
                            phases, _, _, _, _ = analyzer.detect_phases(wrist_history)
                            # Get current phase (last frame)
                            current_phase = analyzer.get_phase_at_frame(len(wrist_history) - 1, phases)
                        except:
                            pass
            
            # Draw phase label (BIG AND BOLD)
            color = PHASE_COLORS.get(current_phase, (255, 255, 255))
            
            # Background rectangle
            cv2.rectangle(frame, (20, 20), (width-20, 120), (0, 0, 0), -1)
            cv2.rectangle(frame, (20, 20), (width-20, 120), color, 5)
            
            # Phase text
            cv2.putText(frame, current_phase, (40, 85),
                       cv2.FONT_HERSHEY_DUPLEX, 2.5, color, 6)
            
            # Instructions at bottom
            cv2.putText(frame, "Press 'q' to quit  |  'r' to reset",
                       (20, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            # Frame counter
            cv2.putText(frame, f"Frames: {len(wrist_history)}",
                       (width - 200, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
            
            # Display
            cv2.imshow('🏌️ Golf Swing Analyzer - LIVE MODE', frame)
            
            # Handle keys
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n👋 Quitting...")
                break
            elif key == ord('r'):
                wrist_history = []
                current_phase = "READY"
                print("🔄 Reset! Ready for new swing...")
            
            frame_count += 1
    finally:
        cap.release()
        pose.close()
        cv2.destroyAllWindows()
    
    print("✅ Live mode ended\n")


if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == "--live" or arg == "-l":
            # LIVE MODE
            live_mode()
        elif arg == "--sequence" or arg == "-s":
            # Image sequence mode
            if len(sys.argv) > 2:
                analyze_image_sequence(sys.argv[2])
            else:
                print("❌ Please provide image sequence directory")
                print("Usage: python phase_detector.py --sequence <directory>")
        elif arg == "--all":
            # Process all videos
            videos = ["0.mp4", "1.mp4", "2.mp4", "3.mp4"]
            for video in videos:
                if Path(video).exists():
                    try:
                        analyze_video(video)
                    except Exception as e:
                        print(f"❌ Error processing {video}: {e}")
                else:
                    print(f"⚠️  Video not found: {video}")
        else:
            # Single video
            video_path = sys.argv[1]
            if Path(video_path).exists():
                analyze_video(video_path)
            else:
                print(f"❌ Error: Video not found: {video_path}")
    else:
        # No arguments - show usage
        print("🏌️ Golf Swing Phase Detector")
        print("\nUsage:")
        print("  python phase_detector.py VIDEO.mp4          # Analyze single video")
        print("  python phase_detector.py --all              # Analyze all videos")
        print("  python phase_detector.py --live             # Live webcam mode")
        print("  python phase_detector.py --sequence DIR     # Analyze image sequence")