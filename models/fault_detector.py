"""
Fault Detection Model - Anomaly-based approach

Instead of supervised learning (requires labeled faults), uses:
- Isolation Forest: Detects outliers in biomechanical patterns
- One-Class SVM: Learns "normal" swing boundaries from CaddieSet

Provides:
1. Anomaly score (0-100, higher = more abnormal)
2. Specific fault identification based on feature deviations
3. Corrective feedback messages
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import pickle
from pathlib import Path
import yaml

from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler


class FaultDetector:
    """
    Detect swing faults using anomaly detection

    Common faults detected:
    1. Poor posture (ADDRESS phase)
    2. Excessive hip sway
    3. Early extension (standing up during swing)
    4. Loss of posture
    5. Inconsistent spine angle
    6. Poor weight transfer
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize fault detector

        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.model = None
        self.scaler = None
        self.imputer = None  # For handling missing values
        self.feature_names = None
        self.feature_stats = None  # Mean/std for each feature
        self.score_stats = None  # Score distribution stats
        self.model_type = None  # Track model type (classifier vs anomaly detector)
        self.metrics = {}  # Store model performance metrics

        # Fault thresholds (based on CaddieSet statistics)
        self.fault_thresholds = {
            'SPINE_ANGLE': {'min': 15, 'max': 50},  # degrees
            'HIP_SHIFTED': {'min': -0.15, 'max': 0.15},  # normalized
            'SHOULDER_ANGLE': {'min': -10, 'max': 10},  # degrees
            'HIP_ROTATION': {'min': -45, 'max': 45},  # degrees
            'STANCE_RATIO': {'min': 1.0, 'max': 2.5},  # ratio
            'X_FACTOR': {'min': 0, 'max': 60}  # degrees
        }

    def train(
        self,
        X: np.ndarray,
        feature_names: List[str],
        contamination: float = 0.1,
        method: str = 'isolation_forest'
    ):
        """
        Train anomaly detection model

        Args:
            X: Training features [n_samples, n_features]
            feature_names: List of feature names
            contamination: Expected proportion of outliers (0.05-0.15)
            method: 'isolation_forest' or 'one_class_svm'
        """
        print(f"\n🤖 Training fault detection model ({method})...")

        self.feature_names = feature_names

        # Compute feature statistics for fault identification
        self.feature_stats = {
            'mean': np.mean(X, axis=0),
            'std': np.std(X, axis=0),
            'min': np.min(X, axis=0),
            'max': np.max(X, axis=0)
        }

        # Train model
        if method == 'isolation_forest':
            self.model = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100,
                max_features=1.0
            )
        elif method == 'one_class_svm':
            self.model = OneClassSVM(
                nu=contamination,
                kernel='rbf',
                gamma='auto'
            )
        else:
            raise ValueError(f"Unknown method: {method}")

        self.model.fit(X)

        # Track score distribution for better normalization
        try:
            scores = self.model.score_samples(X)
            self.score_stats = {
                'mean': float(np.mean(scores)),
                'std': float(np.std(scores) + 1e-6),
                'min': float(np.min(scores)),
                'max': float(np.max(scores)),
                'p10': float(np.percentile(scores, 10)),
                'p90': float(np.percentile(scores, 90))
            }
        except Exception:
            self.score_stats = None

        print(f"   ✅ Model trained on {X.shape[0]} samples")

    def predict(self, features: Dict[str, float]) -> Tuple[float, List[str], Dict]:
        """
        Detect faults in a single swing frame

        Args:
            features: Dictionary of biomechanical features

        Returns:
            anomaly_score: 0-100 (0=normal, 100=highly abnormal)
            fault_messages: List of specific fault messages
            fault_details: Dict with detailed fault information
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        # Convert features dict to array
        X = self._features_to_array(features)
        
        # Check if using PyTorch model
        if hasattr(self, '_is_pytorch') and self._is_pytorch:
            return self._predict_pytorch(X, features)

        # Apply scaler if available
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X.reshape(1, -1))
        else:
            X_scaled = X.reshape(1, -1)

        # Check if this is a supervised classifier
        if hasattr(self.model, 'predict_proba'):
            # Supervised classifier (Random Forest, SVM, etc.)
            # Returns class probabilities: [P(good), P(bad)]
            proba = self.model.predict_proba(X_scaled)[0]
            
            # Class 0 = good, Class 1 = bad
            # Convert to anomaly score: higher bad probability = higher score
            anomaly_score = float(proba[1] * 100)  # Bad swing probability
            
        else:
            # Unsupervised anomaly detector (Isolation Forest)
            # Get anomaly score from model
            # In Isolation Forest: MORE NEGATIVE score = MORE ABNORMAL
            score = self.model.score_samples(X_scaled)[0]

            # Normalize score using training distribution
            if self.score_stats:
                mean = self.score_stats.get('mean', 0.0)
                std = max(self.score_stats.get('std', 1e-6), 1e-6)
                
                # Z-score: how many std deviations from professional mean
                # Professional mean ≈ -0.46, so z=0 means score ≈ -0.46
                z_score = (score - mean) / std
                
                # Isolation Forest: more negative = more abnormal
                # So NEGATIVE z-scores = MORE ABNORMAL (worse than pros)
                # POSITIVE z-scores = LESS ABNORMAL (better/similar to pros)
                
                # Map z-score to fault score:
                # z >= 0 (less abnormal than average pro) → fault score ≈ 0
                # z = -1 (1σ more abnormal) → fault score ≈ 40
                # z = -2 (2σ more abnormal) → fault score ≈ 80
                # z = -3 (3σ more abnormal) → fault score ≈ 100
                
                if z_score >= -0.5:
                    # Within half sigma of professional baseline or better
                    anomaly_score = 0.0
                else:
                    # More abnormal than professionals
                    # Scale negative z-scores: -0.5 → 0, -3.0 → 100
                    deviation = abs(z_score + 0.5)  # How far below -0.5σ
                    anomaly_score = min(100.0, deviation * 40.0)
            else:
                # Fallback linear scaling
                # Isolation Forest scores are typically in range [-0.5, 0.5]
                # More negative = more abnormal
                anomaly_score = max(0.0, (mean - score) * 100)

            anomaly_score = float(np.clip(anomaly_score, 0, 100))

        # Identify specific faults
        fault_messages, fault_details = self._identify_faults(features)

        return anomaly_score, fault_messages, fault_details
    
    def _predict_pytorch(self, X: np.ndarray, features: Dict[str, float]) -> Tuple[float, List[str], Dict]:
        """
        Predict using PyTorch model
        
        Args:
            X: Feature array
            features: Original features dict for fault identification
        
        Returns:
            anomaly_score: 0-100 (higher = more likely bad swing)
            fault_messages: List of specific fault messages
            fault_details: Dict with detailed fault information
        """
        import torch
        
        # Handle missing values with imputer
        if self.imputer is not None:
            X = self.imputer.transform(X.reshape(1, -1))
        else:
            X = X.reshape(1, -1)
        
        # Handle infinite values
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Scale features
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        
        # Convert to tensor and predict
        X_tensor = torch.FloatTensor(X_scaled).to(self._device)
        
        self.model.eval()
        with torch.no_grad():
            output = self.model(X_tensor)
            # Output is probability of bad swing (class 1)
            bad_probability = output.cpu().numpy()[0][0]
        
        # Convert probability to anomaly score (0-100)
        # Higher probability of bad swing = higher anomaly score
        anomaly_score = float(bad_probability * 100)
        
        # Identify specific faults based on features
        fault_messages, fault_details = self._identify_faults(features)
        
        return anomaly_score, fault_messages, fault_details

    def predict_sequence(
        self,
        features_sequence: List[Dict[str, float]],
        phase_ranges: Optional[Dict[str, Tuple[int, int]]] = None
    ) -> Dict:
        """
        Detect faults across entire swing sequence

        Args:
            features_sequence: List of feature dicts for each frame
            phase_ranges: Optional phase boundaries

        Returns:
            Dict with overall_score, phase_scores, faults_by_phase
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        results = {
            'overall_score': 0.0,
            'frame_scores': [],
            'faults_by_phase': {},
            'critical_faults': []
        }

        # Analyze each frame
        for idx, features in enumerate(features_sequence):
            score, messages, details = self.predict(features)
            results['frame_scores'].append(score)

            # Group by phase if provided
            if phase_ranges:
                phase = self._get_phase_at_frame(idx, phase_ranges)
                if phase not in results['faults_by_phase']:
                    results['faults_by_phase'][phase] = []
                if messages:
                    results['faults_by_phase'][phase].extend(messages)

        # Compute overall score
        results['overall_score'] = np.mean(results['frame_scores'])

        # Identify critical faults (present in >50% of frames)
        all_faults = []
        if phase_ranges:
            for phase_faults in results['faults_by_phase'].values():
                all_faults.extend(phase_faults)

        # Count fault occurrences
        from collections import Counter
        fault_counts = Counter(all_faults)
        threshold = len(features_sequence) * 0.3  # Present in >30% of frames

        results['critical_faults'] = [
            fault for fault, count in fault_counts.items()
            if count > threshold
        ]

        return results

    def _identify_faults(self, features: Dict[str, float]) -> Tuple[List[str], Dict]:
        """
        Identify specific faults based on CaddieSet phase-prefixed feature values
        
        Features are in format: "PHASE-FEATURE" e.g., "0-SPINE-ANGLE", "3-HIP-SHIFTED"
        Phases: 0=ADDRESS, 1=BACKSWING, 2=TOP, 3=DOWNSWING, 4=IMPACT, 5=FOLLOW_THROUGH
        
        Thresholds calibrated from actual good vs bad swing data:
        - Good swings: SPINE-ANGLE ~ -62, RIGHT-ARM-ANGLE(3) ~ 136
        - Bad swings: SPINE-ANGLE ~ -75, RIGHT-ARM-ANGLE(3) ~ 39

        Args:
            features: Biomechanical features (CaddieSet format)

        Returns:
            messages: List of formatted fault messages with phase and severity
            details: Dict with structured fault information
        """
        messages = []
        details = {
            'faults': [],  # List of fault dicts with full info
            'by_phase': {
                'ADDRESS': [],
                'BACKSWING': [],
                'TOP': [],
                'DOWNSWING': [],
                'IMPACT': [],
                'FOLLOW_THROUGH': []
            },
            'by_severity': {
                'critical': [],
                'major': [],
                'minor': []
            },
            'summary': {
                'total_faults': 0,
                'critical_count': 0,
                'major_count': 0,
                'minor_count': 0
            }
        }
        
        # Helper to get feature value with fallback
        def get_feature(phase: int, name: str) -> Optional[float]:
            key = f"{phase}-{name}"
            val = features.get(key)
            if val is not None and not (isinstance(val, float) and np.isnan(val)):
                return val
            return None
        
        def add_fault(phase: str, severity: str, title: str, description: str, 
                      fix: str, feature_name: str, actual_value: float, 
                      good_range: str):
            """Add a fault with full details"""
            fault = {
                'phase': phase,
                'severity': severity,
                'title': title,
                'description': description,
                'fix': fix,
                'feature': feature_name,
                'value': actual_value,
                'expected': good_range
            }
            details['faults'].append(fault)
            details['by_phase'][phase].append(fault)
            details['by_severity'][severity].append(fault)
            
            # Format message with emoji based on severity
            severity_emoji = {'critical': '🔴', 'major': '🟠', 'minor': '🟡'}
            emoji = severity_emoji.get(severity, '⚠️')
            
            msg = f"{emoji} [{phase}] {title}: {description} → {fix}"
            messages.append(msg)
        
        # =====================================================================
        # ADDRESS PHASE (0) - Setup position
        # =====================================================================
        spine_addr = get_feature(0, 'SPINE-ANGLE')
        if spine_addr is not None:
            # Good: ~-62°, Bad: ~-75° (more negative = more bent)
            if spine_addr < -72:
                add_fault(
                    phase='ADDRESS',
                    severity='major',
                    title='Excessive Forward Bend',
                    description=f'Spine angle is {spine_addr:.1f}° (too bent over)',
                    fix='Stand more upright, bend from hips not waist',
                    feature_name='0-SPINE-ANGLE',
                    actual_value=spine_addr,
                    good_range='-55° to -68°'
                )
            elif spine_addr > -52:
                add_fault(
                    phase='ADDRESS',
                    severity='minor',
                    title='Too Upright',
                    description=f'Spine angle is {spine_addr:.1f}° (too upright)',
                    fix='Bend forward more from the hips',
                    feature_name='0-SPINE-ANGLE',
                    actual_value=spine_addr,
                    good_range='-55° to -68°'
                )
        
        armpit_addr = get_feature(0, 'RIGHT-ARMPIT-ANGLE')
        if armpit_addr is not None:
            # Good: ~35°, Bad: ~18°
            if armpit_addr < 25:
                add_fault(
                    phase='ADDRESS',
                    severity='minor',
                    title='Arms Too Close',
                    description=f'Armpit angle is {armpit_addr:.1f}° (cramped)',
                    fix='Create more space between arms and body',
                    feature_name='0-RIGHT-ARMPIT-ANGLE',
                    actual_value=armpit_addr,
                    good_range='30° to 45°'
                )
        
        # =====================================================================
        # BACKSWING PHASE (1) - Turn and load
        # =====================================================================
        hip_shift_back = get_feature(1, 'HIP-SHIFTED')
        if hip_shift_back is not None:
            # Good: ~0.10, Bad: ~-0.05
            if hip_shift_back < -0.05:
                add_fault(
                    phase='BACKSWING',
                    severity='major',
                    title='Early Hip Slide',
                    description=f'Hips shifting toward target ({hip_shift_back:.2f})',
                    fix='Keep hips stable, rotate dont slide',
                    feature_name='1-HIP-SHIFTED',
                    actual_value=hip_shift_back,
                    good_range='0.0 to 0.15'
                )
        
        armpit_back = get_feature(1, 'RIGHT-ARMPIT-ANGLE')
        if armpit_back is not None:
            # Good: ~35°, Bad: ~13°
            if armpit_back < 20:
                add_fault(
                    phase='BACKSWING',
                    severity='minor',
                    title='Flying Elbow',
                    description=f'Right armpit angle is {armpit_back:.1f}° (disconnected)',
                    fix='Keep right elbow closer to body',
                    feature_name='1-RIGHT-ARMPIT-ANGLE',
                    actual_value=armpit_back,
                    good_range='25° to 45°'
                )
        
        # =====================================================================
        # TOP OF BACKSWING (2) - Position at the top
        # =====================================================================
        left_arm_top = get_feature(2, 'LEFT-ARM-ANGLE')
        if left_arm_top is not None:
            # Good: ~112°, Bad varies but check for severe breakdown
            if left_arm_top < 95:
                add_fault(
                    phase='TOP',
                    severity='major',
                    title='Left Arm Breakdown',
                    description=f'Left arm bent to {left_arm_top:.1f}° (should be straighter)',
                    fix='Maintain straighter left arm at top',
                    feature_name='2-LEFT-ARM-ANGLE',
                    actual_value=left_arm_top,
                    good_range='100° to 160°'
                )
        
        armpit_top = get_feature(2, 'RIGHT-ARMPIT-ANGLE')
        if armpit_top is not None:
            # Good: ~115°, Bad: ~51°
            if armpit_top < 70:
                add_fault(
                    phase='TOP',
                    severity='major',
                    title='Cramped Top Position',
                    description=f'Right armpit angle only {armpit_top:.1f}° (too tight)',
                    fix='Create more width at top of backswing',
                    feature_name='2-RIGHT-ARMPIT-ANGLE',
                    actual_value=armpit_top,
                    good_range='90° to 130°'
                )
        
        # =====================================================================
        # DOWNSWING PHASE (3) - Critical transition
        # =====================================================================
        right_arm_down = get_feature(3, 'RIGHT-ARM-ANGLE')
        if right_arm_down is not None:
            # Good: ~136°, Bad: ~39° - THIS IS THE KEY DIFFERENTIATOR
            if right_arm_down < 60:
                add_fault(
                    phase='DOWNSWING',
                    severity='critical',
                    title='Right Arm Collapse',
                    description=f'Right arm only {right_arm_down:.1f}° (severely collapsed)',
                    fix='Maintain width - dont let right arm fold too early',
                    feature_name='3-RIGHT-ARM-ANGLE',
                    actual_value=right_arm_down,
                    good_range='100° to 150°'
                )
            elif right_arm_down < 90:
                add_fault(
                    phase='DOWNSWING',
                    severity='major',
                    title='Right Arm Too Bent',
                    description=f'Right arm at {right_arm_down:.1f}° (losing power)',
                    fix='Create more lag while maintaining arm extension',
                    feature_name='3-RIGHT-ARM-ANGLE',
                    actual_value=right_arm_down,
                    good_range='100° to 150°'
                )
        
        hip_rot_down = get_feature(3, 'HIP-ROTATION')
        if hip_rot_down is not None:
            # Good: ~-118°, Bad: ~-248° (over-rotating)
            if hip_rot_down < -200:
                add_fault(
                    phase='DOWNSWING',
                    severity='major',
                    title='Hip Over-Rotation',
                    description=f'Hips rotated {hip_rot_down:.1f}° (over-rotating)',
                    fix='Control hip turn, lead with lower body smoothly',
                    feature_name='3-HIP-ROTATION',
                    actual_value=hip_rot_down,
                    good_range='-80° to -160°'
                )
        
        armpit_down = get_feature(3, 'RIGHT-ARMPIT-ANGLE')
        if armpit_down is not None:
            # Good: ~97°, Bad: ~23°
            if armpit_down < 50:
                add_fault(
                    phase='DOWNSWING',
                    severity='critical',
                    title='Arms Stuck Behind',
                    description=f'Right armpit only {armpit_down:.1f}° (arms trapped)',
                    fix='Create space for arms to swing through',
                    feature_name='3-RIGHT-ARMPIT-ANGLE',
                    actual_value=armpit_down,
                    good_range='70° to 120°'
                )
        
        # =====================================================================
        # IMPACT PHASE (4) - Ball contact
        # =====================================================================
        spine_impact = get_feature(4, 'SPINE-ANGLE')
        if spine_impact is not None:
            # Good: ~-70°, Bad: ~-79°
            if spine_impact < -76:
                add_fault(
                    phase='IMPACT',
                    severity='major',
                    title='Loss of Posture',
                    description=f'Spine at {spine_impact:.1f}° (lost posture through impact)',
                    fix='Maintain spine angle from address through impact',
                    feature_name='4-SPINE-ANGLE',
                    actual_value=spine_impact,
                    good_range='-65° to -74°'
                )
        
        armpit_impact = get_feature(4, 'RIGHT-ARMPIT-ANGLE')
        if armpit_impact is not None:
            # Good: ~77°, Bad: ~14°
            if armpit_impact < 35:
                add_fault(
                    phase='IMPACT',
                    severity='critical',
                    title='Cramped Impact Position',
                    description=f'Right armpit only {armpit_impact:.1f}° (no room to release)',
                    fix='Create space to extend arms through the ball',
                    feature_name='4-RIGHT-ARMPIT-ANGLE',
                    actual_value=armpit_impact,
                    good_range='50° to 100°'
                )
        
        leg_impact = get_feature(4, 'LEFT-LEG-ANGLE')
        if leg_impact is not None:
            # Good: ~174°, Bad: ~160°
            if leg_impact < 165:
                add_fault(
                    phase='IMPACT',
                    severity='minor',
                    title='Bent Front Leg',
                    description=f'Left leg at {leg_impact:.1f}° (not fully posted)',
                    fix='Straighten front leg to brace and rotate',
                    feature_name='4-LEFT-LEG-ANGLE',
                    actual_value=leg_impact,
                    good_range='170° to 180°'
                )
        
        # =====================================================================
        # FOLLOW THROUGH (5) - Finish position  
        # =====================================================================
        finish_angle = get_feature(5, 'FINISH-ANGLE')
        if finish_angle is not None:
            # Good: ~-84°, Bad: ~-83° (similar, not a great discriminator)
            # Only flag extreme cases
            if finish_angle > -60:
                add_fault(
                    phase='FOLLOW_THROUGH',
                    severity='minor',
                    title='Incomplete Finish',
                    description=f'Finish angle at {finish_angle:.1f}° (didnt rotate through)',
                    fix='Complete the swing, finish facing target',
                    feature_name='5-FINISH-ANGLE',
                    actual_value=finish_angle,
                    good_range='-75° to -95°'
                )
        
        # Update summary counts
        details['summary']['total_faults'] = len(details['faults'])
        details['summary']['critical_count'] = len(details['by_severity']['critical'])
        details['summary']['major_count'] = len(details['by_severity']['major'])
        details['summary']['minor_count'] = len(details['by_severity']['minor'])

        return messages, details

    def _features_to_array(self, features: Dict[str, float]) -> np.ndarray:
        """Convert feature dict to numpy array matching training features"""
        if self.feature_names is None:
            raise ValueError("Feature names not set")

        X = []
        for name in self.feature_names:
            # Try multiple matching strategies for CaddieSet format features
            # e.g., "0-SPINE-ANGLE", "0-SHOULDER-ANGLE", etc.
            value = None
            
            # Strategy 1: Exact match
            if name in features:
                value = features[name]
            
            # Strategy 2: Match with underscore instead of dash
            if value is None:
                underscore_name = name.replace('-', '_')
                if underscore_name in features:
                    value = features[underscore_name]
            
            # Strategy 3: Match without phase prefix (e.g., "SPINE-ANGLE" from "0-SPINE-ANGLE")
            if value is None and '-' in name:
                parts = name.split('-', 1)
                if len(parts) == 2 and parts[0].isdigit():
                    base_name = parts[1]
                    # Try exact base name
                    if base_name in features:
                        value = features[base_name]
                    # Try with underscores
                    underscore_base = base_name.replace('-', '_')
                    if underscore_base in features:
                        value = features[underscore_base]
            
            # Strategy 4: Try common feature name variations
            if value is None:
                # Convert to underscore format and try
                underscore_full = name.replace('-', '_')
                for feat_key in features.keys():
                    if feat_key.replace('-', '_') == underscore_full:
                        value = features[feat_key]
                        break

            # Default to 0.0 if not found
            if value is None:
                value = 0.0
            
            # Replace None and NaN with 0.0
            if value is None or (isinstance(value, float) and np.isnan(value)):
                value = 0.0
            
            X.append(value)

        # Convert to numpy and ensure no NaN values
        X = np.array(X, dtype=np.float32)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Apply imputer if available (from new training pipeline)
        if hasattr(self, 'imputer') and self.imputer is not None:
            X = self.imputer.transform(X.reshape(1, -1)).flatten()
        
        return X

    def _get_phase_at_frame(self, frame_idx: int, phase_ranges: Dict) -> str:
        """Get phase name for a specific frame"""
        for phase_name, (start, end) in phase_ranges.items():
            if start <= frame_idx <= end:
                return phase_name
        return "UNKNOWN"

    def save(self, filepath: str):
        """Save trained model to file"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'feature_stats': self.feature_stats,
            'fault_thresholds': self.fault_thresholds,
            'score_stats': self.score_stats
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"💾 Fault detector saved to {filepath}")

    def load(self, filepath: str):
        """Load trained model from file (supports both .pkl and .pt formats)"""
        import torch
        
        # Check if it's a PyTorch model
        if filepath.endswith('.pt'):
            self._load_pytorch_model(filepath)
            return
        
        # Try to load as PyTorch first if .pt version exists
        pt_filepath = filepath.replace('.pkl', '.pt')
        import os
        if os.path.exists(pt_filepath):
            self._load_pytorch_model(pt_filepath)
            return
        
        # Fall back to pickle format
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        self.model = model_data['model']
        self.scaler = model_data.get('scaler')
        self.feature_names = model_data.get('feature_names', model_data.get('features'))
        self.feature_stats = model_data.get('feature_stats')
        self.fault_thresholds = model_data.get('fault_thresholds', self.fault_thresholds)
        self.score_stats = model_data.get('score_stats')
        
        # Support for new classifier model
        self.imputer = model_data.get('imputer')
        self.model_type = model_data.get('model_type', 'isolation_forest')
        
        # Get metrics if available
        self.metrics = model_data.get('metrics', {})

        print(f"📂 Fault detector loaded from {filepath}")
        print(f"   Model type: {self.model_type}")
        if self.metrics:
            print(f"   CV Accuracy: {self.metrics.get('cv_accuracy', 'N/A')}")
    
    def _load_pytorch_model(self, filepath: str):
        """Load a PyTorch model"""
        import torch
        import torch.nn as nn
        
        # Define the model architecture (must match training)
        class GolfSwingClassifier(nn.Module):
            def __init__(self, input_size: int, hidden_sizes: list = [256, 128, 64, 32], dropout: float = 0.3):
                super(GolfSwingClassifier, self).__init__()
                
                layers = []
                prev_size = input_size
                
                layers.append(nn.BatchNorm1d(input_size))
                
                for hidden_size in hidden_sizes:
                    layers.append(nn.Linear(prev_size, hidden_size))
                    layers.append(nn.BatchNorm1d(hidden_size))
                    layers.append(nn.ReLU())
                    layers.append(nn.Dropout(dropout))
                    prev_size = hidden_size
                
                layers.append(nn.Linear(prev_size, 1))
                layers.append(nn.Sigmoid())
                
                self.model = nn.Sequential(*layers)
                
            def forward(self, x):
                return self.model(x)
        
        # Load checkpoint
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        checkpoint = torch.load(filepath, map_location=device, weights_only=False)
        
        # Get model config
        config = checkpoint.get('model_config', {})
        input_size = config.get('input_size', 126)
        hidden_sizes = config.get('hidden_sizes', [256, 128, 64, 32])
        dropout = config.get('dropout', 0.3)
        
        # Create and load model
        self.model = GolfSwingClassifier(input_size, hidden_sizes, dropout)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(device)
        self.model.eval()
        
        # Store device for inference
        self._device = device
        self._is_pytorch = True
        
        # Load other components
        self.scaler = checkpoint.get('scaler')
        self.imputer = checkpoint.get('imputer')
        self.feature_names = checkpoint.get('feature_names', [])
        self.metrics = checkpoint.get('metrics', {})
        self.model_type = 'PyTorch Neural Network'
        
        print(f"📂 PyTorch model loaded from {filepath}")
        print(f"   Model type: {self.model_type}")
        print(f"   Device: {device}")
        if self.metrics:
            print(f"   Test Accuracy: {self.metrics.get('test_accuracy', 'N/A')}")
            print(f"   Test F1: {self.metrics.get('test_f1', 'N/A')}")


if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("Fault Detector - Test")
    print("=" * 60)

    # Create synthetic test data
    np.random.seed(42)
    X_train = np.random.randn(1000, 10)  # 1000 samples, 10 features
    feature_names = [f'feature_{i}' for i in range(10)]

    # Train
    detector = FaultDetector()
    detector.train(X_train, feature_names, contamination=0.1)

    # Test on normal sample
    test_features = {f'feature_{i}': np.random.randn() for i in range(10)}
    score, faults, details = detector.predict(test_features)
    print(f"\nTest sample anomaly score: {score:.1f}")
    print(f"Faults detected: {faults}")

    # Save
    detector.save("models/fault_detector.pkl")
