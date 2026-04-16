"""
CaddieSet-Compatible Feature Extractor

Extracts biomechanical features matching CaddieSet.csv format:
- 6 golf swing phases (ADDRESS, BACKSWING, TOP, DOWNSWING, IMPACT, FOLLOW_THROUGH)
- 21 biomechanical features per phase

Based on the CaddieSet research paper feature definitions.
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, List, Tuple, Optional
from scipy.signal import savgol_filter
from scipy.ndimage import gaussian_filter1d
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')


@dataclass
class SwingPhaseConfig:
    """Configuration for swing phase detection"""
    min_frames: int = 3
    smoothing_window: int = 7
    velocity_threshold: float = 0.02


class CaddieSetFeatureExtractor:
    """
    Extract CaddieSet-compatible biomechanical features from golf swing videos
    
    Features extracted per phase:
    - SHOULDER-ANGLE: Shoulder angle relative to horizontal
    - UPPER-TILT: Lower body to upper body ratio
    - STANCE-RATIO: Shoulder width to stride length ratio
    - HEAD-LOC: Movement of head relative to Address
    - SHOULDER-LOC: Left shoulder position within the width of the stride
    - LEFT-ARM-ANGLE: Angle formed by left shoulder, elbow, and wrist
    - RIGHT-ARM-ANGLE: Angle formed by right shoulder, elbow, and wrist
    - HIP-ROTATION: Rotation degree of pelvis relative to Address
    - HIP-SHIFTED: Movement of hip relative to Address
    - RIGHT-LEG-ANGLE: Angle formed by right hip, knee, and ankle
    - LEFT-LEG-ANGLE: Angle formed by left hip, knee, and ankle
    - SPINE-ANGLE: Spine angle relative to horizontal
    - LOWER-ANGLE: Angle formed by right pelvis, knee, and ankle
    - HIP-LINE: Movement of hip relative to Address
    - HIP-ANGLE: Rotation degree of pelvis relative to Address
    - RIGHT-DISTANCE: Gap between right elbow and the torso
    - SHOULDER-HANGING-BACK: Relative distance between left ankle and left shoulder
    - HIP-HANGING-BACK: Relative distance between left ankle and left hip
    - RIGHT-ARMPIT-ANGLE: Angle formed by right elbow, shoulder, and pelvis
    - WEIGHT-SHIFT: Angle formed by a line connecting left ankle to left pelvis
    - FINISH-ANGLE: Angle formed by a line connecting left ankle to right hip
    """
    
    # MediaPipe landmark indices
    LANDMARKS = {
        'NOSE': 0,
        'LEFT_EYE': 2,
        'RIGHT_EYE': 5,
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
    
    # Phase indices matching SwingPhaseAnalyzer output
    PHASES = {
        0: 'ADDRESS',
        1: 'BACKSWING',
        2: 'TOP',
        3: 'DOWNSWING',
        4: 'IMPACT',
        5: 'FOLLOW_THROUGH'
    }
    
    def __init__(self, config: Optional[SwingPhaseConfig] = None):
        """Initialize the feature extractor"""
        self.config = config or SwingPhaseConfig()
        self.mp_pose = mp.solutions.pose
        self.pose = None
        self._address_reference = None
        
    def _init_pose(self, model_complexity: int = 1):
        """Initialize MediaPipe Pose model"""
        if self.pose is not None:
            self.pose.close()
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,  # Use 1 for 3x speed
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            smooth_landmarks=True
        )
        
    def preprocess_frame(self, frame: np.ndarray, target_size: int = 640) -> np.ndarray:
        """
        Preprocess frame for better pose detection on low-quality videos
        
        Applies:
        1. Upscaling with cubic interpolation
        2. CLAHE contrast enhancement
        3. Bilateral filtering for noise reduction
        4. Unsharp masking for edge enhancement
        """
        h, w = frame.shape[:2]
        
        # 1. Upscale if needed
        if max(h, w) < target_size:
            scale = target_size / max(h, w)
            new_size = (int(w * scale), int(h * scale))
            frame = cv2.resize(frame, new_size, interpolation=cv2.INTER_CUBIC)
        
        # 2. CLAHE contrast enhancement
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        frame = cv2.merge([l, a, b])
        frame = cv2.cvtColor(frame, cv2.COLOR_LAB2BGR)
        
        # 3. Bilateral filter for noise reduction (preserves edges)
        frame = cv2.bilateralFilter(frame, 9, 75, 75)
        
        # 4. Unsharp masking for edge enhancement
        gaussian = cv2.GaussianBlur(frame, (0, 0), 2.0)
        frame = cv2.addWeighted(frame, 1.5, gaussian, -0.5, 0)
        frame = np.clip(frame, 0, 255).astype(np.uint8)
        
        return frame
    
    def smooth_landmarks_sequence(
        self, 
        landmarks_sequence: List[np.ndarray],
        window_size: int = 7
    ) -> List[np.ndarray]:
        """
        Apply temporal smoothing to landmark sequence using Savitzky-Golay filter
        
        This reduces jitter while preserving sharp movements
        """
        if len(landmarks_sequence) < window_size:
            return landmarks_sequence
            
        # Stack landmarks for vectorized smoothing
        stacked = np.array(landmarks_sequence)  # [T, 33, 3]
        smoothed = np.zeros_like(stacked)
        
        # Apply Savitzky-Golay filter along time axis for each landmark coordinate
        for lm_idx in range(stacked.shape[1]):
            for coord_idx in range(stacked.shape[2]):
                signal = stacked[:, lm_idx, coord_idx]
                # Handle NaN values
                valid_mask = ~np.isnan(signal)
                if valid_mask.sum() >= window_size:
                    # Interpolate NaN values
                    signal_interp = np.interp(
                        np.arange(len(signal)),
                        np.where(valid_mask)[0],
                        signal[valid_mask]
                    )
                    try:
                        smoothed[:, lm_idx, coord_idx] = savgol_filter(
                            signal_interp, 
                            window_size, 
                            polyorder=3
                        )
                    except:
                        smoothed[:, lm_idx, coord_idx] = signal
                else:
                    smoothed[:, lm_idx, coord_idx] = signal
                    
        return [smoothed[i] for i in range(len(smoothed))]
    
    def _calculate_angle(self, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
        """Calculate angle at p2 formed by p1-p2-p3"""
        v1 = p1 - p2
        v2 = p3 - p2
        
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
        angle = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
        return angle
    
    def _calculate_line_angle(self, p1: np.ndarray, p2: np.ndarray) -> float:
        """Calculate angle of line p1->p2 relative to horizontal"""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return np.degrees(np.arctan2(dy, dx))
    
    def _get_landmark_coords(self, landmarks: np.ndarray, name: str) -> np.ndarray:
        """Get coordinates for a named landmark"""
        idx = self.LANDMARKS[name]
        return landmarks[idx][:2]  # x, y only
    
    def extract_frame_features(
        self, 
        landmarks: np.ndarray,
        frame_height: int,
        frame_width: int
    ) -> Dict[str, float]:
        """
        Extract all biomechanical features from a single frame's landmarks
        
        Returns dictionary with feature names matching CaddieSet format
        """
        features = {}
        
        # Denormalize coordinates
        coords = landmarks.copy()
        coords[:, 0] *= frame_width
        coords[:, 1] *= frame_height
        
        # Get key landmark positions
        left_shoulder = self._get_landmark_coords(coords, 'LEFT_SHOULDER')
        right_shoulder = self._get_landmark_coords(coords, 'RIGHT_SHOULDER')
        left_elbow = self._get_landmark_coords(coords, 'LEFT_ELBOW')
        right_elbow = self._get_landmark_coords(coords, 'RIGHT_ELBOW')
        left_wrist = self._get_landmark_coords(coords, 'LEFT_WRIST')
        right_wrist = self._get_landmark_coords(coords, 'RIGHT_WRIST')
        left_hip = self._get_landmark_coords(coords, 'LEFT_HIP')
        right_hip = self._get_landmark_coords(coords, 'RIGHT_HIP')
        left_knee = self._get_landmark_coords(coords, 'LEFT_KNEE')
        right_knee = self._get_landmark_coords(coords, 'RIGHT_KNEE')
        left_ankle = self._get_landmark_coords(coords, 'LEFT_ANKLE')
        right_ankle = self._get_landmark_coords(coords, 'RIGHT_ANKLE')
        nose = self._get_landmark_coords(coords, 'NOSE')
        
        # Mid-points
        mid_shoulder = (left_shoulder + right_shoulder) / 2
        mid_hip = (left_hip + right_hip) / 2
        
        # Stride length (distance between ankles)
        stride_length = np.linalg.norm(left_ankle - right_ankle) + 1e-8
        
        # Shoulder width
        shoulder_width = np.linalg.norm(left_shoulder - right_shoulder) + 1e-8
        
        # ========================
        # ANGLE FEATURES
        # ========================
        
        # SHOULDER-ANGLE: Shoulder line angle relative to horizontal
        features['SHOULDER-ANGLE'] = self._calculate_line_angle(left_shoulder, right_shoulder)
        
        # SPINE-ANGLE: Spine angle relative to horizontal
        spine_vector = mid_shoulder - mid_hip
        features['SPINE-ANGLE'] = np.degrees(np.arctan2(spine_vector[1], spine_vector[0]))
        
        # LEFT-ARM-ANGLE: Angle at elbow (shoulder-elbow-wrist)
        features['LEFT-ARM-ANGLE'] = self._calculate_angle(left_shoulder, left_elbow, left_wrist)
        
        # RIGHT-ARM-ANGLE: Angle at elbow (shoulder-elbow-wrist)
        features['RIGHT-ARM-ANGLE'] = self._calculate_angle(right_shoulder, right_elbow, right_wrist)
        
        # LEFT-LEG-ANGLE: Angle at knee (hip-knee-ankle)
        features['LEFT-LEG-ANGLE'] = self._calculate_angle(left_hip, left_knee, left_ankle)
        
        # RIGHT-LEG-ANGLE: Angle at knee (hip-knee-ankle)
        features['RIGHT-LEG-ANGLE'] = self._calculate_angle(right_hip, right_knee, right_ankle)
        
        # LOWER-ANGLE: Angle formed by right pelvis, knee, and ankle
        features['LOWER-ANGLE'] = self._calculate_angle(right_hip, right_knee, right_ankle)
        
        # HIP-ANGLE: Hip line rotation relative to horizontal
        features['HIP-ANGLE'] = self._calculate_line_angle(left_hip, right_hip)
        
        # RIGHT-ARMPIT-ANGLE: Angle at shoulder (elbow-shoulder-hip)
        features['RIGHT-ARMPIT-ANGLE'] = self._calculate_angle(right_elbow, right_shoulder, right_hip)
        
        # WEIGHT-SHIFT: Angle of line from left ankle to left hip
        features['WEIGHT-SHIFT'] = self._calculate_line_angle(left_ankle, left_hip)
        
        # FINISH-ANGLE: Angle of line from left ankle to right hip
        features['FINISH-ANGLE'] = self._calculate_line_angle(left_ankle, right_hip)
        
        # ========================
        # RATIO FEATURES
        # ========================
        
        # STANCE-RATIO: Shoulder width to stride length ratio
        features['STANCE-RATIO'] = shoulder_width / stride_length
        
        # UPPER-TILT: Lower body to upper body ratio
        lower_body_height = (left_hip[1] + right_hip[1]) / 2 - (left_ankle[1] + right_ankle[1]) / 2
        upper_body_height = (left_shoulder[1] + right_shoulder[1]) / 2 - (left_hip[1] + right_hip[1]) / 2
        features['UPPER-TILT'] = lower_body_height / (abs(upper_body_height) + 1e-8)
        
        # ========================
        # POSITION FEATURES (relative to stride/width)
        # ========================
        
        # HEAD-LOC: Head position normalized by stride (will compute delta from address)
        features['HEAD-LOC'] = (nose[0] - left_ankle[0]) / stride_length
        
        # SHOULDER-LOC: Left shoulder position within stride
        features['SHOULDER-LOC'] = (left_shoulder[0] - left_ankle[0]) / stride_length
        
        # HIP-LINE: Hip center position (will compute delta from address)
        features['HIP-LINE'] = (mid_hip[0] - left_ankle[0]) / stride_length
        
        # HIP-SHIFTED: Hip shift normalized by stride (will compute delta from address)
        features['HIP-SHIFTED'] = (mid_hip[0] - (left_ankle[0] + right_ankle[0]) / 2) / stride_length
        
        # HIP-ROTATION: Hip rotation relative to horizontal
        features['HIP-ROTATION'] = self._calculate_line_angle(left_hip, right_hip)
        
        # ========================
        # DISTANCE FEATURES
        # ========================
        
        # RIGHT-DISTANCE: Gap between right elbow and torso (normalized)
        torso_center = mid_hip
        features['RIGHT-DISTANCE'] = np.linalg.norm(right_elbow - torso_center) / shoulder_width
        
        # SHOULDER-HANGING-BACK: Distance from left ankle to left shoulder / stride
        features['SHOULDER-HANGING-BACK'] = np.linalg.norm(left_shoulder - left_ankle) / stride_length
        
        # HIP-HANGING-BACK: Distance from left ankle to left hip / stride
        features['HIP-HANGING-BACK'] = np.linalg.norm(left_hip - left_ankle) / stride_length
        
        return features
    
    def detect_swing_phases(
        self,
        landmarks_sequence: List[np.ndarray],
        frame_height: int,
        frame_width: int
    ) -> Dict[int, Tuple[int, int]]:
        """
        Detect 6 swing phases from landmark sequence (matching SwingPhaseAnalyzer)
        
        Uses wrist trajectory velocity and position to segment swing:
        0: ADDRESS - static position before swing
        1: BACKSWING - club moving back
        2: TOP - peak of backswing
        3: DOWNSWING - club coming down
        4: IMPACT - ball strike
        5: FOLLOW_THROUGH - after impact
        """
        if len(landmarks_sequence) < 10:
            # Too short, return equal divisions
            n = len(landmarks_sequence)
            phase_len = n // 6
            return {i: (i * phase_len, (i + 1) * phase_len - 1) for i in range(6)}
        
        # Extract wrist y-trajectory (primary indicator)
        wrist_y = []
        wrist_x = []
        for lm in landmarks_sequence:
            if lm is not None:
                left_wrist = lm[self.LANDMARKS['LEFT_WRIST']]
                right_wrist = lm[self.LANDMARKS['RIGHT_WRIST']]
                # Use left wrist for right-handed golfers (dominant hand)
                wrist_y.append(left_wrist[1] * frame_height)
                wrist_x.append(left_wrist[0] * frame_width)
            else:
                wrist_y.append(np.nan)
                wrist_x.append(np.nan)
        
        wrist_y = np.array(wrist_y)
        wrist_x = np.array(wrist_x)
        
        # Interpolate NaN values
        valid_mask = ~np.isnan(wrist_y)
        if valid_mask.sum() < 10:
            n = len(landmarks_sequence)
            phase_len = n // 6
            return {i: (i * phase_len, (i + 1) * phase_len - 1) for i in range(6)}
        
        wrist_y = np.interp(np.arange(len(wrist_y)), np.where(valid_mask)[0], wrist_y[valid_mask])
        wrist_x = np.interp(np.arange(len(wrist_x)), np.where(~np.isnan(wrist_x))[0], wrist_x[~np.isnan(wrist_x)])
        
        # Smooth trajectory
        window = min(self.config.smoothing_window, len(wrist_y) // 2)
        if window >= 3:
            wrist_y = savgol_filter(wrist_y, window if window % 2 == 1 else window + 1, 3)
        
        # Calculate velocity
        velocity = np.gradient(wrist_y)
        velocity_smooth = gaussian_filter1d(velocity, sigma=2)
        
        # Find key points
        n = len(wrist_y)
        
        # TOP: Minimum wrist Y (highest point in video coordinates)
        top_idx = np.argmin(wrist_y)
        
        # IMPACT: Maximum downward velocity after TOP
        post_top_vel = velocity_smooth[top_idx:]
        if len(post_top_vel) > 3:
            impact_offset = np.argmax(post_top_vel)
            impact_idx = top_idx + impact_offset
        else:
            impact_idx = min(top_idx + n // 10, n - 1)
        
        # ADDRESS: Find static region at start (low velocity)
        vel_threshold = np.std(velocity_smooth) * 0.3
        address_end = 0
        for i in range(min(n // 4, len(velocity_smooth))):
            if abs(velocity_smooth[i]) < vel_threshold:
                address_end = i
            else:
                break
        address_end = max(1, address_end)
        
        # Divide phases
        swing_start = address_end + 1
        
        # BACKSWING: from address end to top
        backswing_end = max(swing_start + 1, top_idx - 1)
        
        # TOP: around the peak
        top_end = min(top_idx + 2, impact_idx - 1)
        
        # DOWNSWING: from top to impact
        downswing_end = max(top_end + 1, impact_idx - 1)
        
        # IMPACT: short window around impact
        impact_end = min(impact_idx + 2, n - 2)
        
        # FOLLOW_THROUGH: rest of the swing
        phases = {
            0: (0, address_end),
            1: (address_end + 1, backswing_end),
            2: (backswing_end + 1, top_end),
            3: (top_end + 1, downswing_end),
            4: (downswing_end + 1, impact_end),
            5: (impact_end + 1, n - 1)
        }
        
        # Ensure no empty or invalid phases
        for phase_idx in range(6):
            start, end = phases[phase_idx]
            if end <= start:
                # Adjust to ensure at least 1 frame
                phases[phase_idx] = (start, start + 1)
            if start >= n:
                phases[phase_idx] = (n - 2, n - 1)
            if end >= n:
                phases[phase_idx] = (phases[phase_idx][0], n - 1)
        
        return phases
    
    def extract_from_video(
        self,
        video_path: str,
        preprocess: bool = True,
        verbose: bool = True
    ) -> Dict[str, float]:
        """
        Extract CaddieSet-compatible features from a video
        
        Returns dictionary with phase-prefixed features:
        e.g., '0-SHOULDER-ANGLE', '1-HEAD-LOC', '7-FINISH-ANGLE'
        """
        from tqdm import tqdm
        
        # Initialize pose model
        self._init_pose()
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        
        if verbose:
            print(f"  Processing video: {frame_width}x{frame_height}, {frame_count} frames")
        
        # Extract landmarks from all frames
        landmarks_sequence = []
        iterator = tqdm(range(frame_count), desc="  Extracting poses") if verbose else range(frame_count)
        
        for _ in iterator:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Preprocess for low-quality videos
            if preprocess and max(frame_height, frame_width) < 400:
                frame = self.preprocess_frame(frame)
                # Update dimensions after preprocessing
                frame_height, frame_width = frame.shape[:2]
            
            # Convert to RGB for MediaPipe
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb)
            
            if results.pose_landmarks:
                landmarks = np.array([
                    [lm.x, lm.y, lm.z]
                    for lm in results.pose_landmarks.landmark
                ])
                landmarks_sequence.append(landmarks)
            else:
                landmarks_sequence.append(None)
        
        cap.release()
        
        if verbose:
            valid_count = sum(1 for lm in landmarks_sequence if lm is not None)
            print(f"  Valid poses: {valid_count}/{frame_count}")
        
        # Smooth landmarks sequence
        valid_landmarks = [lm for lm in landmarks_sequence if lm is not None]
        if len(valid_landmarks) >= self.config.smoothing_window:
            smoothed_valid = self.smooth_landmarks_sequence(valid_landmarks, self.config.smoothing_window)
            # Reconstruct sequence with smoothed values
            j = 0
            for i in range(len(landmarks_sequence)):
                if landmarks_sequence[i] is not None:
                    landmarks_sequence[i] = smoothed_valid[j]
                    j += 1
        
        # Detect swing phases
        phases = self.detect_swing_phases(landmarks_sequence, frame_height, frame_width)
        
        if verbose:
            print(f"  Detected phases: {[(self.PHASES[i], phases[i]) for i in range(6)]}")
        
        # Extract features for each phase (6 phases: 0-5)
        phase_features = {}
        
        for phase_idx in range(6):
            start_frame, end_frame = phases[phase_idx]
            
            # Get landmarks for this phase
            phase_landmarks = [
                landmarks_sequence[i] 
                for i in range(start_frame, min(end_frame + 1, len(landmarks_sequence)))
                if landmarks_sequence[i] is not None
            ]
            
            if not phase_landmarks:
                continue
            
            # Extract features for each frame in phase
            frame_features_list = [
                self.extract_frame_features(lm, frame_height, frame_width)
                for lm in phase_landmarks
            ]
            
            # Average features across frames in phase
            for feature_name in frame_features_list[0].keys():
                values = [ff[feature_name] for ff in frame_features_list if feature_name in ff]
                if values:
                    # Use median for robustness to outliers
                    avg_value = np.median(values)
                    phase_features[f"{phase_idx}-{feature_name}"] = avg_value
            
            # Store address reference for relative calculations
            if phase_idx == 0:
                self._address_reference = {
                    k: v for k, v in phase_features.items() 
                    if k.startswith('0-')
                }
        
        # Compute relative features (HEAD-LOC, HIP-SHIFTED, etc. relative to address)
        if self._address_reference:
            for phase_idx in range(1, 6):
                for feature in ['HEAD-LOC', 'HIP-SHIFTED', 'HIP-LINE', 'HIP-ROTATION']:
                    current_key = f"{phase_idx}-{feature}"
                    address_key = f"0-{feature}"
                    if current_key in phase_features and address_key in self._address_reference:
                        # Store as delta from address
                        delta = (
                            phase_features[current_key] - 
                            self._address_reference[address_key]
                        )
                        # Normalize angular deltas to avoid ±180° wrapping artifacts
                        if feature == 'HIP-ROTATION':
                            delta = ((delta + 180) % 360) - 180
                        phase_features[current_key] = delta
        
        return phase_features
    
    def close(self):
        """Clean up resources"""
        if self.pose is not None:
            self.pose.close()
            self.pose = None
    
    def extract_from_landmarks(
        self,
        landmarks_sequence: list,
        phase_ranges: dict,
        frame_height: int,
        frame_width: int,
        min_visibility: float = 0.4
    ) -> dict:
        """
        Extract CaddieSet-compatible features from pre-computed landmarks.
        
        This avoids re-processing the video through MediaPipe, using the
        already-cached (and smoothed) landmarks from TrajectoryExtractor
        along with phase ranges from SwingPhaseAnalyzer.
        
        Args:
            landmarks_sequence: List of [33, 4] arrays (x, y, z, visibility) or None
            phase_ranges: Dict mapping phase name str to (start, end) frame indices
            frame_height: Video frame height
            frame_width: Video frame width
            min_visibility: Minimum average key-landmark visibility to include a frame
        
        Returns:
            Dictionary with phase-prefixed features e.g. '0-SPINE-ANGLE'
        """
        PHASE_NAME_TO_INDEX = {
            'ADDRESS': 0, 'BACKSWING': 1, 'TOP': 2,
            'DOWNSWING': 3, 'IMPACT': 4, 'FOLLOW_THROUGH': 5
        }
        KEY_LANDMARKS = [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
        
        phase_features = {}
        
        for phase_name, (start, end) in phase_ranges.items():
            phase_idx = PHASE_NAME_TO_INDEX.get(phase_name, -1)
            if phase_idx < 0:
                continue
            
            # Collect valid, high-visibility landmarks for this phase
            phase_landmarks = []
            for i in range(start, min(end + 1, len(landmarks_sequence))):
                lm = landmarks_sequence[i]
                if lm is None:
                    continue
                # Filter by average visibility of key body landmarks
                if lm.shape[1] > 3:
                    avg_vis = np.mean([lm[idx, 3] for idx in KEY_LANDMARKS])
                    if avg_vis < min_visibility:
                        continue
                    phase_landmarks.append(lm[:, :3])  # x, y, z only
                else:
                    phase_landmarks.append(lm[:, :3])
            
            if not phase_landmarks:
                continue
            
            # Extract features for each valid frame in the phase
            frame_features_list = [
                self.extract_frame_features(lm, frame_height, frame_width)
                for lm in phase_landmarks
            ]
            
            # Aggregate using median (robust to remaining outliers)
            for feature_name in frame_features_list[0].keys():
                values = [
                    ff[feature_name] for ff in frame_features_list
                    if feature_name in ff and np.isfinite(ff[feature_name])
                ]
                if values:
                    phase_features[f"{phase_idx}-{feature_name}"] = float(np.median(values))
            
            # Store address reference for relative calculations
            if phase_idx == 0:
                self._address_reference = {
                    k: v for k, v in phase_features.items() if k.startswith('0-')
                }
        
        # Compute relative features (delta from address)
        if self._address_reference:
            for phase_idx in range(1, 6):
                for feature in ['HEAD-LOC', 'HIP-SHIFTED', 'HIP-LINE', 'HIP-ROTATION']:
                    current_key = f"{phase_idx}-{feature}"
                    address_key = f"0-{feature}"
                    if current_key in phase_features and address_key in self._address_reference:
                        delta = (
                            phase_features[current_key] -
                            self._address_reference[address_key]
                        )
                        # Normalize angular deltas to avoid ±180° wrapping artifacts
                        if feature == 'HIP-ROTATION':
                            delta = ((delta + 180) % 360) - 180
                        phase_features[current_key] = delta
        
        return phase_features
