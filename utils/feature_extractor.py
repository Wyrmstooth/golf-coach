"""
Feature extraction from pose landmarks to biomechanical features
Converts MediaPipe 33-keypoint pose data into golf-specific biomechanical measurements
Compatible with CaddieSet feature definitions
"""

import numpy as np
from typing import Dict, List, Optional
import yaml
from pathlib import Path


class FeatureExtractor:
    """
    Extract biomechanical features from pose landmarks

    Features extracted match CaddieSet.csv format:
    - Angles: shoulder, hip, spine, arms, legs
    - Positions: head location, hip shift, shoulder location
    - Rotations: hip rotation, shoulder rotation
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize feature extractor

        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # MediaPipe landmark indices
        self.LANDMARKS = {
            'NOSE': 0,
            'LEFT_SHOULDER': 11,
            'RIGHT_SHOULDER': 12,
            'LEFT_ELBOW': 13,
            'RIGHT_ELBOW': 14,
            'LEFT_WRIST': 15,
            'RIGHT_WRIST': 16,
            'LEFT_HIP': 23,
            'RIGHT_HIP': 24,
            'LEFT_KNEE': 25,
            'RIGHT_KNEE': 26,
            'LEFT_ANKLE': 27,
            'RIGHT_ANKLE': 28
        }

    def extract_features(
        self,
        landmarks: np.ndarray,
        frame_height: int = 720,
        frame_width: int = 1280
    ) -> Dict[str, float]:
        """
        Extract all biomechanical features from pose landmarks

        Args:
            landmarks: MediaPipe landmarks array [33, 3] (x, y, visibility)
            frame_height: Video frame height (for denormalization)
            frame_width: Video frame width (for denormalization)

        Returns:
            Dictionary of features matching CaddieSet format
        """
        features = {}

        # Check if landmarks are valid
        if landmarks is None or len(landmarks) < 33:
            return self._get_empty_features()

        # Denormalize coordinates
        coords = landmarks.copy()
        coords[:, 0] *= frame_width
        coords[:, 1] *= frame_height

        # Extract angle features
        features['SHOULDER_ANGLE'] = self._calculate_shoulder_angle(coords)
        features['HIP_ANGLE'] = self._calculate_hip_angle(coords)
        features['SPINE_ANGLE'] = self._calculate_spine_angle(coords)
        features['LEFT_ARM_ANGLE'] = self._calculate_arm_angle(coords, side='left')
        features['RIGHT_ARM_ANGLE'] = self._calculate_arm_angle(coords, side='right')
        features['LEFT_LEG_ANGLE'] = self._calculate_leg_angle(coords, side='left')
        features['RIGHT_LEG_ANGLE'] = self._calculate_leg_angle(coords, side='right')
        features['LOWER_ANGLE'] = self._calculate_lower_body_angle(coords)

        # Extract position features
        features['HEAD_LOC'] = self._calculate_head_location(coords, frame_width)
        features['HIP_LINE'] = self._calculate_hip_line(coords)
        features['HIP_SHIFTED'] = self._calculate_hip_shift(coords, frame_width)
        features['SHOULDER_LOC'] = self._calculate_shoulder_location(coords, frame_width)

        # Extract rotation features
        features['HIP_ROTATION'] = self._calculate_hip_rotation(coords)
        features['SHOULDER_ROTATION'] = self._calculate_shoulder_rotation(coords)

        # Additional golf-specific features
        features['X_FACTOR'] = features['SHOULDER_ROTATION'] - features['HIP_ROTATION']
        features['STANCE_RATIO'] = self._calculate_stance_ratio(coords)
        features['UPPER_TILT'] = self._calculate_upper_tilt(coords)

        return features

    def extract_features_sequence(
        self,
        landmarks_sequence: List[np.ndarray],
        frame_height: int = 720,
        frame_width: int = 1280
    ) -> List[Dict[str, float]]:
        """
        Extract features from a sequence of frames

        Args:
            landmarks_sequence: List of landmark arrays
            frame_height: Video frame height
            frame_width: Video frame width

        Returns:
            List of feature dictionaries
        """
        return [
            self.extract_features(lm, frame_height, frame_width)
            for lm in landmarks_sequence
        ]

    def _calculate_shoulder_angle(self, coords: np.ndarray) -> float:
        """Calculate shoulder line angle relative to horizontal"""
        left_shoulder = coords[self.LANDMARKS['LEFT_SHOULDER']][:2]
        right_shoulder = coords[self.LANDMARKS['RIGHT_SHOULDER']][:2]

        dx = right_shoulder[0] - left_shoulder[0]
        dy = right_shoulder[1] - left_shoulder[1]

        angle = np.degrees(np.arctan2(dy, dx))
        return angle

    def _calculate_hip_angle(self, coords: np.ndarray) -> float:
        """Calculate hip line angle relative to horizontal"""
        left_hip = coords[self.LANDMARKS['LEFT_HIP']][:2]
        right_hip = coords[self.LANDMARKS['RIGHT_HIP']][:2]

        dx = right_hip[0] - left_hip[0]
        dy = right_hip[1] - left_hip[1]

        angle = np.degrees(np.arctan2(dy, dx))
        return angle

    def _calculate_spine_angle(self, coords: np.ndarray) -> float:
        """Calculate spine tilt from vertical"""
        # Mid-shoulder point
        left_shoulder = coords[self.LANDMARKS['LEFT_SHOULDER']][:2]
        right_shoulder = coords[self.LANDMARKS['RIGHT_SHOULDER']][:2]
        mid_shoulder = (left_shoulder + right_shoulder) / 2

        # Mid-hip point
        left_hip = coords[self.LANDMARKS['LEFT_HIP']][:2]
        right_hip = coords[self.LANDMARKS['RIGHT_HIP']][:2]
        mid_hip = (left_hip + right_hip) / 2

        # Spine vector
        spine_vector = mid_shoulder - mid_hip
        vertical = np.array([0, -1])

        # Angle from vertical
        cosine = np.dot(spine_vector, vertical) / (np.linalg.norm(spine_vector) + 1e-6)
        angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))

        return angle

    def _calculate_arm_angle(self, coords: np.ndarray, side: str = 'left') -> float:
        """Calculate arm angle (shoulder-elbow-wrist)"""
        if side == 'left':
            shoulder = coords[self.LANDMARKS['LEFT_SHOULDER']][:2]
            elbow = coords[self.LANDMARKS['LEFT_ELBOW']][:2]
            wrist = coords[self.LANDMARKS['LEFT_WRIST']][:2]
        else:
            shoulder = coords[self.LANDMARKS['RIGHT_SHOULDER']][:2]
            elbow = coords[self.LANDMARKS['RIGHT_ELBOW']][:2]
            wrist = coords[self.LANDMARKS['RIGHT_WRIST']][:2]

        return self._angle_between_points(shoulder, elbow, wrist)

    def _calculate_leg_angle(self, coords: np.ndarray, side: str = 'left') -> float:
        """Calculate leg angle (hip-knee-ankle)"""
        if side == 'left':
            hip = coords[self.LANDMARKS['LEFT_HIP']][:2]
            knee = coords[self.LANDMARKS['LEFT_KNEE']][:2]
            ankle = coords[self.LANDMARKS['LEFT_ANKLE']][:2]
        else:
            hip = coords[self.LANDMARKS['RIGHT_HIP']][:2]
            knee = coords[self.LANDMARKS['RIGHT_KNEE']][:2]
            ankle = coords[self.LANDMARKS['RIGHT_ANKLE']][:2]

        return self._angle_between_points(hip, knee, ankle)

    def _calculate_lower_body_angle(self, coords: np.ndarray) -> float:
        """Calculate lower body angle (average of knee flexion)"""
        left_leg = self._calculate_leg_angle(coords, 'left')
        right_leg = self._calculate_leg_angle(coords, 'right')
        return (left_leg + right_leg) / 2

    def _calculate_head_location(self, coords: np.ndarray, frame_width: int) -> float:
        """Calculate normalized head X position"""
        nose = coords[self.LANDMARKS['NOSE']][:2]
        return nose[0] / frame_width

    def _calculate_hip_line(self, coords: np.ndarray) -> float:
        """Calculate hip line Y position (average)"""
        left_hip = coords[self.LANDMARKS['LEFT_HIP']][:2]
        right_hip = coords[self.LANDMARKS['RIGHT_HIP']][:2]
        return (left_hip[1] + right_hip[1]) / 2

    def _calculate_hip_shift(self, coords: np.ndarray, frame_width: int) -> float:
        """Calculate hip lateral shift (normalized)"""
        left_hip = coords[self.LANDMARKS['LEFT_HIP']][:2]
        right_hip = coords[self.LANDMARKS['RIGHT_HIP']][:2]
        mid_hip = (left_hip + right_hip) / 2

        # Normalized shift from center
        center = frame_width / 2
        shift = (mid_hip[0] - center) / frame_width

        return shift

    def _calculate_shoulder_location(self, coords: np.ndarray, frame_width: int) -> float:
        """Calculate normalized shoulder X position"""
        left_shoulder = coords[self.LANDMARKS['LEFT_SHOULDER']][:2]
        right_shoulder = coords[self.LANDMARKS['RIGHT_SHOULDER']][:2]
        mid_shoulder = (left_shoulder + right_shoulder) / 2

        return mid_shoulder[0] / frame_width

    def _calculate_hip_rotation(self, coords: np.ndarray) -> float:
        """Calculate hip rotation in degrees"""
        left_hip = coords[self.LANDMARKS['LEFT_HIP']][:2]
        right_hip = coords[self.LANDMARKS['RIGHT_HIP']][:2]

        dx = right_hip[0] - left_hip[0]
        dy = right_hip[1] - left_hip[1]

        return np.degrees(np.arctan2(dy, dx))

    def _calculate_shoulder_rotation(self, coords: np.ndarray) -> float:
        """Calculate shoulder rotation in degrees"""
        left_shoulder = coords[self.LANDMARKS['LEFT_SHOULDER']][:2]
        right_shoulder = coords[self.LANDMARKS['RIGHT_SHOULDER']][:2]

        dx = right_shoulder[0] - left_shoulder[0]
        dy = right_shoulder[1] - left_shoulder[1]

        return np.degrees(np.arctan2(dy, dx))

    def _calculate_stance_ratio(self, coords: np.ndarray) -> float:
        """Calculate stance width ratio"""
        left_ankle = coords[self.LANDMARKS['LEFT_ANKLE']][:2]
        right_ankle = coords[self.LANDMARKS['RIGHT_ANKLE']][:2]

        stance_width = np.linalg.norm(left_ankle - right_ankle)

        # Normalize by shoulder width
        left_shoulder = coords[self.LANDMARKS['LEFT_SHOULDER']][:2]
        right_shoulder = coords[self.LANDMARKS['RIGHT_SHOULDER']][:2]
        shoulder_width = np.linalg.norm(left_shoulder - right_shoulder)

        return stance_width / (shoulder_width + 1e-6)

    def _calculate_upper_tilt(self, coords: np.ndarray) -> float:
        """Calculate upper body lateral tilt"""
        # Shoulder tilt minus hip tilt
        shoulder_angle = self._calculate_shoulder_angle(coords)
        hip_angle = self._calculate_hip_angle(coords)

        return shoulder_angle - hip_angle

    def _angle_between_points(self, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
        """Calculate angle at p2 formed by p1-p2-p3"""
        v1 = p1 - p2
        v2 = p3 - p2

        cosine = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))

        return angle

    def _get_empty_features(self) -> Dict[str, float]:
        """Return dictionary of None values for missing features"""
        return {
            'SHOULDER_ANGLE': None,
            'HIP_ANGLE': None,
            'SPINE_ANGLE': None,
            'LEFT_ARM_ANGLE': None,
            'RIGHT_ARM_ANGLE': None,
            'LEFT_LEG_ANGLE': None,
            'RIGHT_LEG_ANGLE': None,
            'LOWER_ANGLE': None,
            'HEAD_LOC': None,
            'HIP_LINE': None,
            'HIP_SHIFTED': None,
            'SHOULDER_LOC': None,
            'HIP_ROTATION': None,
            'SHOULDER_ROTATION': None,
            'X_FACTOR': None,
            'STANCE_RATIO': None,
            'UPPER_TILT': None
        }
