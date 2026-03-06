"""
Trajectory extraction from videos and image sequences
"""

import cv2
import numpy as np
import mediapipe as mp
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm


class TrajectoryExtractor:
    """Extract wrist and body trajectories from videos or image sequences"""
    
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.cached_landmarks = []  # Cache full landmarks to avoid reprocessing
        
    def extract_from_video(self, video_path: str, verbose: bool = True, preprocess: bool = False, max_resolution: int = 1080) -> List[Dict]:
        """
        Extract wrist and body trajectories from video file
        
        Args:
            video_path: Path to video file
            verbose: Show progress bars and info
            preprocess: Apply preprocessing for low-quality videos (ignored for performance)
            max_resolution: Maximum resolution for processing (downscale 4K)
        
        Returns:
            List of dicts with frame_idx, wrist_y, hip_rotation, shoulder_rotation
        """
        cap = cv2.VideoCapture(video_path)
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Only downscale 4K videos for faster processing
        downscale_4k = original_height > max_resolution
        if downscale_4k:
            scale_factor = max_resolution / original_height
            process_width = int(original_width * scale_factor)
            process_height = max_resolution
            if verbose:
                print(f"   ⚠️  4K video detected - downscaling to {process_width}x{process_height} for faster processing")
        else:
            process_width = original_width
            process_height = original_height
            scale_factor = 1.0
        
        if verbose:
            print(f"📹 Video: {Path(video_path).name}")
            print(f"   Resolution: {original_width}x{original_height}, Frames: {num_frames}")
        
        # Use model_complexity=1 for 3x faster processing with minimal accuracy loss
        pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,  # Changed from 2 to 1 for 3x speed boost
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        frame_data = []
        iterator = tqdm(range(num_frames), desc="Extracting trajectories") if verbose else range(num_frames)
        
        try:
            for i in iterator:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Downscale 4K videos only (fast INTER_AREA for downsampling)
                if downscale_4k:
                    frame = cv2.resize(frame, (process_width, process_height), interpolation=cv2.INTER_AREA)
                
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(rgb)
                
                data = {"frame_idx": i}
                
                # Cache full landmarks for later use
                if results.pose_landmarks:
                    # Extract landmarks as numpy array
                    lm = results.pose_landmarks.landmark
                    landmarks_array = np.array([[lm[j].x, lm[j].y, lm[j].z, lm[j].visibility] 
                                               for j in range(len(lm))])
                    self.cached_landmarks.append(landmarks_array)
                else:
                    self.cached_landmarks.append(None)
                
                if results.pose_landmarks:
                    lm = results.pose_landmarks.landmark
                    
                    # Extract wrist position
                    lw = lm[self.mp_pose.PoseLandmark.LEFT_WRIST]
                    rw = lm[self.mp_pose.PoseLandmark.RIGHT_WRIST]
                    visible_wrists = [p for p in (lw, rw) if p.visibility > 0.4]
                    
                    if visible_wrists:
                        data["wrist_y"] = np.mean([p.y for p in visible_wrists]) * original_height
                    else:
                        data["wrist_y"] = None
                    
                    # Extract hip rotation
                    left_hip = lm[self.mp_pose.PoseLandmark.LEFT_HIP]
                    right_hip = lm[self.mp_pose.PoseLandmark.RIGHT_HIP]
                    if left_hip.visibility > 0.4 and right_hip.visibility > 0.4:
                        hip_angle = np.degrees(np.arctan2(
                            right_hip.y - left_hip.y,
                            right_hip.x - left_hip.x
                        ))
                        data["hip_rotation"] = hip_angle
                    else:
                        data["hip_rotation"] = None
                    
                    # Extract shoulder rotation
                    left_shoulder = lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
                    right_shoulder = lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
                    if left_shoulder.visibility > 0.4 and right_shoulder.visibility > 0.4:
                        shoulder_angle = np.degrees(np.arctan2(
                            right_shoulder.y - left_shoulder.y,
                            right_shoulder.x - left_shoulder.x
                        ))
                        data["shoulder_rotation"] = shoulder_angle
                    else:
                        data["shoulder_rotation"] = None
                else:
                    data["wrist_y"] = None
                    data["hip_rotation"] = None
                    data["shoulder_rotation"] = None
                    
                frame_data.append(data)
        finally:
            cap.release()
            pose.close()
        
        return frame_data
    
    def _smooth_trajectories(self, frame_data: List[Dict]) -> List[Dict]:
        """Apply Gaussian smoothing to trajectory data"""
        from scipy.ndimage import gaussian_filter1d
        
        # Extract time series
        wrist_y = np.array([d.get('wrist_y') if d.get('wrist_y') is not None else np.nan 
                           for d in frame_data])
        hip_rot = np.array([d.get('hip_rotation') if d.get('hip_rotation') is not None else np.nan 
                           for d in frame_data])
        shoulder_rot = np.array([d.get('shoulder_rotation') if d.get('shoulder_rotation') is not None else np.nan 
                                for d in frame_data])
        
        # Handle NaN values by forward fill
        def fill_nans(arr):
            mask = np.isnan(arr)
            if not mask.all():
                arr[mask] = np.interp(np.flatnonzero(mask), np.flatnonzero(~mask), arr[~mask])
            return arr
        
        wrist_y = fill_nans(wrist_y)
        hip_rot = fill_nans(hip_rot)
        shoulder_rot = fill_nans(shoulder_rot)
        
        # Apply Gaussian smoothing
        sigma = 2.0
        wrist_y_smooth = gaussian_filter1d(wrist_y, sigma=sigma)
        hip_rot_smooth = gaussian_filter1d(hip_rot, sigma=sigma)
        shoulder_rot_smooth = gaussian_filter1d(shoulder_rot, sigma=sigma)
        
        # Update frame_data with smoothed values
        for i, d in enumerate(frame_data):
            d['wrist_y'] = float(wrist_y_smooth[i])
            d['hip_rotation'] = float(hip_rot_smooth[i])
            d['shoulder_rotation'] = float(shoulder_rot_smooth[i])
        
        return frame_data
    
    def extract_from_images(self, image_files: List[Path], verbose: bool = True) -> List[Dict]:
        """
        Extract trajectories from image sequence
        
        Args:
            image_files: List of image file paths (sorted)
            verbose: Show progress bars
        
        Returns:
            List of dicts with frame_idx, wrist_y, hip_rotation, shoulder_rotation
        """
        pose = self.mp_pose.Pose(static_image_mode=True, model_complexity=2)
        frame_data = []
        
        iterator = tqdm(enumerate(image_files), total=len(image_files), 
                       desc="Processing images") if verbose else enumerate(image_files)
        
        try:
            for idx, img_file in iterator:
                frame = cv2.imread(str(img_file))
                if frame is None:
                    continue
                
                height = frame.shape[0]
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(rgb)
                
                data = {"frame_idx": idx}
                
                if results.pose_landmarks:
                    lm = results.pose_landmarks.landmark
                    
                    # Extract wrist position
                    lw = lm[self.mp_pose.PoseLandmark.LEFT_WRIST]
                    rw = lm[self.mp_pose.PoseLandmark.RIGHT_WRIST]
                    visible_wrists = [p for p in (lw, rw) if p.visibility > 0.4]
                    
                    if visible_wrists:
                        data["wrist_y"] = np.mean([p.y for p in visible_wrists]) * height
                    else:
                        data["wrist_y"] = None
                    
                    # Extract hip rotation
                    left_hip = lm[self.mp_pose.PoseLandmark.LEFT_HIP]
                    right_hip = lm[self.mp_pose.PoseLandmark.RIGHT_HIP]
                    if left_hip.visibility > 0.4 and right_hip.visibility > 0.4:
                        hip_angle = np.degrees(np.arctan2(
                            right_hip.y - left_hip.y,
                            right_hip.x - left_hip.x
                        ))
                        data["hip_rotation"] = hip_angle
                    else:
                        data["hip_rotation"] = None
                    
                    # Extract shoulder rotation
                    left_shoulder = lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
                    right_shoulder = lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
                    if left_shoulder.visibility > 0.4 and right_shoulder.visibility > 0.4:
                        shoulder_angle = np.degrees(np.arctan2(
                            right_shoulder.y - left_shoulder.y,
                            right_shoulder.x - left_shoulder.x
                        ))
                        data["shoulder_rotation"] = shoulder_angle
                    else:
                        data["shoulder_rotation"] = None
                else:
                    data["wrist_y"] = None
                    data["hip_rotation"] = None
                    data["shoulder_rotation"] = None
                
                frame_data.append(data)
        finally:
            pose.close()
        
        return frame_data
