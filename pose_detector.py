"""
Real-time pose estimation using MediaPipe
"""

import cv2
import mediapipe as mp
import mediapipe_compat  # patches mp.solutions for MediaPipe 0.10.x  # noqa: F401
import numpy as np
from typing import Optional, Tuple, List
import yaml


class PoseDetector:
    """
    Real-time pose estimation using MediaPipe Pose
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize pose detector
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        pose_config = self.config['pose_detection']
        
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.pose = self.mp_pose.Pose(
            model_complexity=pose_config['model_complexity'],
            min_detection_confidence=pose_config['min_detection_confidence'],
            min_tracking_confidence=pose_config['min_tracking_confidence'],
            enable_segmentation=pose_config['enable_segmentation'],
            smooth_landmarks=pose_config['smooth_landmarks']
        )
        
        # Store previous landmarks for smoothing
        self.prev_landmarks = None
        
    def process_frame(self, frame: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[object]]:
        """
        Process a single frame to detect pose
        
        Args:
            frame: Input image (BGR format)
        
        Returns:
            (landmarks_array, pose_results)
            landmarks_array: [33, 3] array of (x, y, z) coordinates
            pose_results: MediaPipe pose results object
        """
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        
        # Detect pose
        results = self.pose.process(image_rgb)
        
        image_rgb.flags.writeable = True
        
        if results.pose_landmarks:
            # Extract landmarks as numpy array
            landmarks = self._extract_landmarks(results.pose_landmarks)
            return landmarks, results
        
        return None, results
    
    def _extract_landmarks(self, pose_landmarks) -> np.ndarray:
        """
        Extract landmarks as numpy array
        
        Args:
            pose_landmarks: MediaPipe pose landmarks
        
        Returns:
            Array of shape [33, 3] with (x, y, z) coordinates
        """
        landmarks = []
        for landmark in pose_landmarks.landmark:
            landmarks.append([landmark.x, landmark.y, landmark.z])
        
        return np.array(landmarks)
    
    def draw_pose(self,
                  frame: np.ndarray,
                  results,
                  draw_landmarks: bool = True,
                  draw_connections: bool = True) -> np.ndarray:
        """
        Draw pose on frame
        
        Args:
            frame: Input frame
            results: MediaPipe pose results
            draw_landmarks: Whether to draw landmark points
            draw_connections: Whether to draw skeleton connections
        
        Returns:
            Frame with pose drawn
        """
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS if draw_connections else None,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
            )
        
        return frame
    
    def draw_custom_skeleton(self, 
                            frame: np.ndarray,
                            landmarks: np.ndarray,
                            color: Tuple[int, int, int] = (0, 255, 0),
                            thickness: int = 2) -> np.ndarray:
        """
        Draw custom skeleton with specific style
        
        Args:
            frame: Input frame
            landmarks: Landmark array [33, 3]
            color: Line color (BGR)
            thickness: Line thickness
        
        Returns:
            Frame with skeleton drawn
        """
        h, w, _ = frame.shape
        
        # Define connections
        connections = [
            # Torso
            (11, 12), (11, 23), (12, 24), (23, 24),
            # Left arm
            (11, 13), (13, 15),
            # Right arm
            (12, 14), (14, 16),
            # Left leg
            (23, 25), (25, 27),
            # Right leg
            (24, 26), (26, 28)
        ]
        
        # Draw connections
        for connection in connections:
            start_idx, end_idx = connection
            
            start_point = (int(landmarks[start_idx][0] * w), 
                          int(landmarks[start_idx][1] * h))
            end_point = (int(landmarks[end_idx][0] * w),
                        int(landmarks[end_idx][1] * h))
            
            cv2.line(frame, start_point, end_point, color, thickness)
        
        # Draw joints
        for landmark in landmarks:
            point = (int(landmark[0] * w), int(landmark[1] * h))
            cv2.circle(frame, point, 4, (0, 0, 255), -1)
        
        return frame
    
    def denormalize_landmarks(self, landmarks: np.ndarray, frame_shape: Tuple[int, int]) -> np.ndarray:
        """
        Convert normalized landmarks to pixel coordinates
        
        Args:
            landmarks: Normalized landmarks [33, 3]
            frame_shape: (height, width) of frame
        
        Returns:
            Landmarks in pixel coordinates
        """
        h, w = frame_shape[:2]
        pixel_landmarks = landmarks.copy()
        pixel_landmarks[:, 0] *= w
        pixel_landmarks[:, 1] *= h
        
        return pixel_landmarks
    
    def close(self):
        """Release resources"""
        self.pose.close()
    
    def __del__(self):
        """Destructor"""
        try:
            self.close()
        except:
            pass
