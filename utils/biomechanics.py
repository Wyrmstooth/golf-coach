"""
Biomechanical calculations for golf swing analysis
"""

import numpy as np
from typing import Tuple


def calculate_angle(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
    """
    Calculate angle between three points (p1-p2-p3)
    
    Args:
        p1: First point [x, y]
        p2: Vertex point [x, y]
        p3: Third point [x, y]
    
    Returns:
        Angle in degrees
    """
    a = np.array(p1)
    b = np.array(p2)
    c = np.array(p3)
    
    ba = a - b
    bc = c - b
    
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
    
    return angle


def calculate_joint_angle(landmarks: np.ndarray, joint_indices: Tuple[int, int, int]) -> float:
    """
    Calculate angle at a joint given landmark indices
    
    Args:
        landmarks: Array of landmarks [N, 2] or [N, 3]
        joint_indices: Tuple of (point1, vertex, point3) indices
    
    Returns:
        Angle in degrees
    """
    p1_idx, p2_idx, p3_idx = joint_indices
    
    p1 = landmarks[p1_idx][:2]
    p2 = landmarks[p2_idx][:2]
    p3 = landmarks[p3_idx][:2]
    
    return calculate_angle(p1, p2, p3)


def get_elbow_angles(landmarks: np.ndarray) -> Tuple[float, float]:
    """
    Calculate left and right elbow angles
    
    Args:
        landmarks: MediaPipe pose landmarks array
    
    Returns:
        (left_elbow_angle, right_elbow_angle)
    """
    # Left elbow: shoulder(11) - elbow(13) - wrist(15)
    left_elbow = calculate_joint_angle(landmarks, (11, 13, 15))
    
    # Right elbow: shoulder(12) - elbow(14) - wrist(16)
    right_elbow = calculate_joint_angle(landmarks, (12, 14, 16))
    
    return left_elbow, right_elbow


def get_knee_angles(landmarks: np.ndarray) -> Tuple[float, float]:
    """
    Calculate left and right knee angles
    
    Args:
        landmarks: MediaPipe pose landmarks array
    
    Returns:
        (left_knee_angle, right_knee_angle)
    """
    # Left knee: hip(23) - knee(25) - ankle(27)
    left_knee = calculate_joint_angle(landmarks, (23, 25, 27))
    
    # Right knee: hip(24) - knee(26) - ankle(28)
    right_knee = calculate_joint_angle(landmarks, (24, 26, 28))
    
    return left_knee, right_knee


def get_hip_rotation(landmarks: np.ndarray) -> float:
    """
    Calculate hip rotation angle
    
    Args:
        landmarks: MediaPipe pose landmarks array
    
    Returns:
        Hip rotation angle in degrees
    """
    # Get hip landmarks
    left_hip = landmarks[23][:2]
    right_hip = landmarks[24][:2]
    
    # Calculate hip line angle relative to horizontal
    hip_vector = right_hip - left_hip
    angle = np.degrees(np.arctan2(hip_vector[1], hip_vector[0]))
    
    return angle


def get_shoulder_rotation(landmarks: np.ndarray) -> float:
    """
    Calculate shoulder rotation angle
    
    Args:
        landmarks: MediaPipe pose landmarks array
    
    Returns:
        Shoulder rotation angle in degrees
    """
    # Get shoulder landmarks
    left_shoulder = landmarks[11][:2]
    right_shoulder = landmarks[12][:2]
    
    # Calculate shoulder line angle relative to horizontal
    shoulder_vector = right_shoulder - left_shoulder
    angle = np.degrees(np.arctan2(shoulder_vector[1], shoulder_vector[0]))
    
    return angle


def get_spine_angle(landmarks: np.ndarray) -> float:
    """
    Calculate spine angle (forward lean)
    
    Args:
        landmarks: MediaPipe pose landmarks array
    
    Returns:
        Spine angle in degrees
    """
    # Mid shoulder point
    mid_shoulder = (landmarks[11][:2] + landmarks[12][:2]) / 2
    
    # Mid hip point
    mid_hip = (landmarks[23][:2] + landmarks[24][:2]) / 2
    
    # Calculate angle from vertical
    spine_vector = mid_shoulder - mid_hip
    vertical = np.array([0, -1])
    
    cosine = np.dot(spine_vector, vertical) / (np.linalg.norm(spine_vector) + 1e-6)
    angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
    
    return angle


def extract_landmarks_from_mediapipe(pose_landmarks, mp_pose) -> np.ndarray:
    """
    Extract landmarks array from MediaPipe pose landmarks
    
    Args:
        pose_landmarks: MediaPipe pose landmarks object
        mp_pose: MediaPipe pose solution
    
    Returns:
        Array of shape [33, 3] with (x, y, visibility)
    """
    landmarks = []
    for landmark in pose_landmarks.landmark:
        landmarks.append([landmark.x, landmark.y, landmark.visibility])
    
    return np.array(landmarks)
