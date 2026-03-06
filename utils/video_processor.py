"""
Video processing utilities for golf swing analysis
"""

import cv2
import numpy as np
import mediapipe as mp
import subprocess
from pathlib import Path
from typing import Tuple, Optional, Dict, List
from tqdm import tqdm
from utils.biomechanics import calculate_joint_angle, extract_landmarks_from_mediapipe
from utils.ball_tracker import BallTrajectoryPoint


class VideoProcessor:
    """Handle video input/output and frame processing"""
    
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_style = mp.solutions.drawing_styles
    
    def get_video_properties(self, video_path: str) -> Dict:
        """
        Get video properties
        
        Args:
            video_path: Path to video file
        
        Returns:
            Dict with width, height, fps, frame_count
        """
        cap = cv2.VideoCapture(video_path)
        props = {
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        }
        cap.release()
        return props
    
    def calculate_upscale_factor(self, width: int, min_width: int = 640) -> float:
        """Calculate upscale factor for small videos"""
        if width < min_width:
            return min_width / width
        return 1.0
    
    def create_annotated_video(
        self,
        video_path: str,
        output_path: str,
        phase_ranges: Dict[str, Tuple[int, int]],
        show_pose: bool = True,
        slow_motion: float = 0.5,
        max_resolution: int = 1080,
        ball_trajectory: Optional[List[BallTrajectoryPoint]] = None,
    ) -> str:
        """
        Create annotated video with phase labels and pose overlay
        
        Args:
            video_path: Input video path
            output_path: Output video path
            phase_ranges: Dict of phase ranges
            show_pose: Whether to show pose skeleton
            slow_motion: Speed multiplier (0.5 = half speed)
            max_resolution: Maximum output resolution (height)
        
        Returns:
            Path to output video
        """
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"🎬 Generating annotated video...")
        print(f"   Resolution: {width}x{height}, FPS: {fps:.1f}")
        
        # Calculate scale factor
        # For small videos: upscale to at least 640px width
        # For large videos (4K): downscale to max_resolution
        if width < 640:
            scale_factor = 640 / width
        elif height > max_resolution:
            scale_factor = max_resolution / height
            print(f"   ⚠️  Downscaling 4K video for faster processing")
        else:
            scale_factor = 1.0
        
        output_width = int(width * scale_factor)
        output_height = int(height * scale_factor)
        
        if scale_factor != 1.0:
            print(f"   Output resolution: {output_width}x{output_height}")
        
        # Setup output video with efficient codec
        output_fps = max(15, fps * slow_motion)
        print(f"   Output FPS: {output_fps:.1f}")
        
        # Try H.264 codec first, fallback to mp4v if not available
        out = None
        for codec in ['avc1', 'mp4v', 'XVID', 'MJPG']:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            out = cv2.VideoWriter(output_path, fourcc, output_fps, (output_width, output_height))
            if out.isOpened():
                if codec != 'mp4v' and codec != 'avc1':
                    print(f"   Using {codec} codec")
                break
            out.release()
        
        if not out or not out.isOpened():
            raise RuntimeError(f"Failed to create video writer for {output_path}")
        
        # Setup pose detector with lower complexity for 3x speed
        pose = self.mp_pose.Pose(
            static_image_mode=False, 
            model_complexity=1,  # Changed from 2 to 1 for 3x faster processing
            min_tracking_confidence=0.5
        ) if show_pose else None
        
        # Preindex ball trajectory by frame for quick lookup
        ball_by_frame: Dict[int, BallTrajectoryPoint] = {}
        if ball_trajectory:
            for pt in ball_trajectory:
                ball_by_frame[int(pt.frame)] = pt

        try:
            for frame_idx in tqdm(range(total_frames), desc="Rendering video"):
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Upscale or downscale if needed
                if scale_factor != 1.0:
                    frame = cv2.resize(frame, (output_width, output_height), 
                                     interpolation=cv2.INTER_CUBIC)
                
                # Add pose overlay
                if show_pose and pose:
                    frame = self._add_pose_overlay(frame, pose)
                
                # Get current phase
                phase = self._get_phase_at_frame(frame_idx, phase_ranges)
                
                # Add annotations
                frame = self._add_annotations(frame, phase, frame_idx, output_width, output_height)

                # Add ball overlay (Module 3)
                if ball_by_frame:
                    frame = self._add_ball_overlay(frame, frame_idx, ball_by_frame)
                
                out.write(frame)
        finally:
            cap.release()
            out.release()
            if pose:
                pose.close()
        
        print(f"✅ Saved annotated video: {output_path}")
        
        # Return directly without re-encoding (saves significant time)
        return output_path
    
    def _add_pose_overlay(self, frame: np.ndarray, pose) -> np.ndarray:
        """Add pose skeleton overlay to frame"""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)
        
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_style.get_default_pose_landmarks_style()
            )
            
            # Calculate and store angles
            landmarks = extract_landmarks_from_mediapipe(results.pose_landmarks, self.mp_pose)
            self._current_angles = self._calculate_angles(landmarks)
        
        return frame
    
    def _calculate_angles(self, landmarks: np.ndarray) -> Dict[str, float]:
        """Calculate joint angles from landmarks"""
        angles = {}
        
        try:
            # Elbow angles: shoulder - elbow - wrist
            angles['L Elbow'] = calculate_joint_angle(landmarks, (11, 13, 15))
            angles['R Elbow'] = calculate_joint_angle(landmarks, (12, 14, 16))
            
            # Knee angles: hip - knee - ankle
            angles['L Knee'] = calculate_joint_angle(landmarks, (23, 25, 27))
            angles['R Knee'] = calculate_joint_angle(landmarks, (24, 26, 28))
        except:
            pass
        
        return angles
    
    def _add_annotations(
        self,
        frame: np.ndarray,
        phase: str,
        frame_idx: int,
        width: int,
        height: int
    ) -> np.ndarray:
        """Add phase label, angles, and frame counter"""
        scale = min(width, height) / 160.0
        
        # Phase label
        label_h = int(35 * scale)
        font_s = 0.4 * scale
        thick = max(1, int(2 * scale))
        
        cv2.rectangle(frame, (3, 3), (width-3, label_h), (0, 0, 0), -1)
        cv2.rectangle(frame, (3, 3), (width-3, label_h), (0, 255, 0), 2)
        cv2.putText(frame, phase, (int(5*scale), int(25*scale)),
                   cv2.FONT_HERSHEY_DUPLEX, font_s, (0, 255, 0), thick)
        
        # Angles (if available)
        if hasattr(self, '_current_angles'):
            y_pos = height - int(45 * scale)
            line_h = int(10 * scale)
            small_f = 0.25 * scale
            small_t = max(1, int(1 * scale))
            
            for idx, (name, angle) in enumerate(self._current_angles.items()):
                color = (0, 255, 0) if 'Elbow' in name else (0, 255, 255)
                cv2.putText(frame, f"{name}:{angle:.0f}",
                           (3, y_pos + line_h * idx),
                           cv2.FONT_HERSHEY_SIMPLEX, small_f, color, small_t)
        
        # Frame counter
        cv2.putText(frame, f"#{frame_idx}",
                   (width - int(30*scale), height - int(3*scale)),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.25*scale, (150,150,150),
                   max(1, int(1*scale)))
        
        return frame

    def _add_ball_overlay(
        self,
        frame: np.ndarray,
        frame_idx: int,
        ball_by_frame: Dict[int, BallTrajectoryPoint],
        tail_length: int = 10,
    ) -> np.ndarray:
        """
        Draw ball position and a short tail of previous positions.
        """
        height, width = frame.shape[:2]

        # Current point
        pt = ball_by_frame.get(frame_idx)
        if not pt or pt.x is None or pt.y is None:
            return frame

        # Convert from float pixel coords
        x = int(np.clip(pt.x, 0, width - 1))
        y = int(np.clip(pt.y, 0, height - 1))

        # Draw current ball position (bright yellow)
        cv2.circle(frame, (x, y), 6, (0, 255, 255), -1)

        # Draw tail of previous positions
        for offset in range(1, tail_length + 1):
            prev_idx = frame_idx - offset
            prev_pt = ball_by_frame.get(prev_idx)
            if not prev_pt or prev_pt.x is None or prev_pt.y is None:
                continue

            px = int(np.clip(prev_pt.x, 0, width - 1))
            py = int(np.clip(prev_pt.y, 0, height - 1))

            # Fade color with age
            alpha = max(0.2, 1.0 - offset / float(tail_length + 1))
            color = (0, int(255 * alpha), int(255 * alpha))
            cv2.circle(frame, (px, py), 4, color, -1)

        return frame
    
    def _get_phase_at_frame(self, frame_idx: int, phase_ranges: Dict) -> str:
        """Get phase name for a specific frame"""
        for phase_name, (start, end) in phase_ranges.items():
            if start <= frame_idx <= end:
                return phase_name
        return "UNKNOWN"
    
    def _reencode_video(self, video_path: str) -> str:
        """Re-encode video for better compatibility"""
        try:
            import shutil
            if shutil.which("ffmpeg"):
                reencoded_path = video_path.replace(".mp4", "_final.mp4")
                cmd = [
                    "ffmpeg", "-y", "-i", video_path,
                    "-vcodec", "libx264", "-crf", "23", "-preset", "fast",
                    "-pix_fmt", "yuv420p",
                    reencoded_path
                ]
                
                print("🔄 Re-encoding for compatibility...")
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    print(f"✅ Final video: {reencoded_path}")
                    return reencoded_path
                else:
                    print("⚠️  Re-encoding failed, using original video")
            else:
                print("⚠️  ffmpeg not found, skipping re-encoding")
        except Exception as e:
            print(f"⚠️  Re-encoding error: {e}")
        
        return video_path
    
    def create_video_from_images(
        self,
        image_files: list,
        output_path: str,
        phase_ranges: Dict[str, Tuple[int, int]],
        fps: int = 30,
        show_pose: bool = True
    ) -> str:
        """
        Create annotated video from image sequence
        
        Args:
            image_files: List of image file paths
            output_path: Output video path
            phase_ranges: Dict of phase ranges
            fps: Frame rate for output video
            show_pose: Whether to show pose skeleton
        
        Returns:
            Path to output video
        """
        print(f"\n🎬 Creating annotated video from images...")
        
        # Get frame size from first image
        first_frame = cv2.imread(str(image_files[0]))
        height, width = first_frame.shape[:2]
        
        # Upscale if needed
        scale_factor = self.calculate_upscale_factor(width)
        output_width = int(width * scale_factor)
        output_height = int(height * scale_factor)
        
        if scale_factor > 1.0:
            print(f"   Upscaling from {width}x{height} to {output_width}x{output_height}")
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (output_width, output_height))
        
        pose = self.mp_pose.Pose(static_image_mode=True, model_complexity=2) if show_pose else None
        
        try:
            for idx, img_file in enumerate(tqdm(image_files, desc="Rendering video")):
                frame = cv2.imread(str(img_file))
                if frame is None:
                    continue
                
                # Upscale if needed
                if scale_factor != 1.0:
                    frame = cv2.resize(frame, (output_width, output_height),
                                     interpolation=cv2.INTER_CUBIC)
                
                # Add pose overlay
                if show_pose and pose:
                    frame = self._add_pose_overlay(frame, pose)
                
                # Get current phase
                phase = self._get_phase_at_frame(idx, phase_ranges)
                
                # Add annotations
                frame = self._add_annotations(frame, phase, idx, output_width, output_height)
                
                out.write(frame)
        finally:
            out.release()
            if pose:
                pose.close()
        
        print(f"\n💾 Saved: {output_path}")
        return str(output_path)
