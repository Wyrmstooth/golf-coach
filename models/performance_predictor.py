"""
Performance Prediction Model

Predicts shot outcomes from biomechanical features:
- Ball Speed (mph)
- Distance (yards)
- Carry Distance (yards)

Uses CaddieSet ground truth data for training
Model: Random Forest Regressor (good for small datasets, interpretable)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import pickle
from pathlib import Path
import yaml

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error


class PerformancePredictor:
    """
    Predict shot performance from swing biomechanics

    Outputs:
    - Ball Speed: Expected ball velocity (mph)
    - Distance: Total distance (yards)
    - Carry: Carry distance (yards)
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize performance predictor

        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.model = None
        self.scaler = None
        self.feature_names = None
        self.target_names = ['BallSpeed', 'Distance', 'Carry']

        # Feature importance (populated after training)
        self.feature_importance = None

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        feature_names: List[str],
        normalize: bool = True
    ) -> Dict:
        """
        Train performance prediction model

        Args:
            X_train: Training features [n_samples, n_features]
            y_train: Training targets [n_samples, 3] (BallSpeed, Distance, Carry)
            X_test: Test features
            y_test: Test targets
            feature_names: List of feature names
            normalize: Whether to normalize features

        Returns:
            metrics: Dict with training and test metrics
        """
        print("\n🤖 Training performance prediction model...")

        self.feature_names = feature_names

        # Normalize features
        if normalize:
            self.scaler = StandardScaler()
            X_train = self.scaler.fit_transform(X_train)
            X_test = self.scaler.transform(X_test)

        # Train Random Forest
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )

        self.model.fit(X_train, y_train)

        # Evaluate
        y_train_pred = self.model.predict(X_train)
        y_test_pred = self.model.predict(X_test)

        metrics = {
            'train': self._compute_metrics(y_train, y_train_pred),
            'test': self._compute_metrics(y_test, y_test_pred)
        }

        # Feature importance
        self.feature_importance = self.model.feature_importances_

        # Print results
        print(f"\n📊 Training Results:")
        print(f"   Train R² scores: {metrics['train']['r2']}")
        print(f"   Test R² scores:  {metrics['test']['r2']}")
        print(f"\n   Train MAE: {metrics['train']['mae']}")
        print(f"   Test MAE:  {metrics['test']['mae']}")

        # Top features
        top_indices = np.argsort(self.feature_importance)[-10:][::-1]
        print(f"\n🔝 Top 10 Important Features:")
        for i, idx in enumerate(top_indices):
            print(f"   {i+1}. {feature_names[idx]}: {self.feature_importance[idx]:.3f}")

        return metrics

    def predict(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Predict shot performance from biomechanical features

        Args:
            features: Dictionary of biomechanical features

        Returns:
            predictions: Dict with BallSpeed, Distance, Carry, confidence
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Check if using PyTorch model
        if hasattr(self, '_is_pytorch') and self._is_pytorch:
            return self._predict_pytorch(features)

        # Convert features dict to array
        X = self._features_to_array(features)

        # Normalize if scaler exists
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X.reshape(1, -1))
        else:
            X_scaled = X.reshape(1, -1)

        # Get predictions from all trees in the forest for uncertainty estimation
        if hasattr(self.model, 'estimators_'):
            # Get predictions from each tree
            tree_predictions = np.array([
                tree.predict(X_scaled)[0] for tree in self.model.estimators_
            ])
            
            # Mean prediction
            y_pred = np.mean(tree_predictions, axis=0)
            
            # Standard deviation across trees (uncertainty)
            y_std = np.std(tree_predictions, axis=0)
            
            # Calculate confidence based on prediction variance
            # Lower variance = higher confidence
            # Use coefficient of variation (std/mean) as uncertainty measure
            cv_scores = []
            for i in range(len(y_pred)):
                if abs(y_pred[i]) > 1e-6:
                    cv = y_std[i] / abs(y_pred[i])
                    cv_scores.append(cv)
            
            if cv_scores:
                avg_cv = np.mean(cv_scores)
                # Map CV to confidence: CV=0 -> 95%, CV=0.5 -> 50%, CV>=1 -> 20%
                confidence = max(20.0, min(95.0, 95.0 - (avg_cv * 150)))
            else:
                confidence = 50.0
        else:
            # Fallback for non-ensemble models
            y_pred = self.model.predict(X_scaled)[0]
            confidence = 60.0  # Default moderate confidence
        
        # Adjust confidence based on feature coverage
        feature_coverage = self._calculate_feature_coverage(features)
        confidence = confidence * (0.5 + 0.5 * feature_coverage)
        
        # Clamp confidence to realistic range (never 100%, never below 20%)
        confidence = max(20.0, min(85.0, confidence))

        predictions = {
            'BallSpeed': float(y_pred[0]),
            'Distance': float(y_pred[1]),
            'Carry': float(y_pred[2]),
            'confidence': float(confidence)
        }

        return predictions
    
    def _calculate_feature_coverage(self, features: Dict[str, float]) -> float:
        """
        Calculate what percentage of expected features are present and valid
        
        Returns:
            coverage: 0.0 to 1.0
        """
        if self.feature_names is None:
            return 0.5
        
        valid_count = 0
        total_count = len(self.feature_names)
        
        for name in self.feature_names:
            if name in features:
                value = features[name]
                if value is not None and not (isinstance(value, float) and np.isnan(value)):
                    valid_count += 1
        
        return valid_count / max(total_count, 1)

    def predict_sequence(
        self,
        features_sequence: List[Dict[str, float]]
    ) -> Dict:
        """
        Predict performance from swing sequence (uses mean features)

        Args:
            features_sequence: List of feature dicts for each frame

        Returns:
            predictions: Dict with BallSpeed, Distance, Carry, confidence
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        # Aggregate features across sequence (use mean)
        aggregated_features = self._aggregate_features(features_sequence)

        # Predict
        predictions = self.predict(aggregated_features)

        # Add confidence estimate (based on feature consistency)
        confidence = self._estimate_confidence(features_sequence)
        predictions['confidence'] = confidence

        return predictions

    def predict_by_phase(
        self,
        features_sequence: List[Dict[str, float]],
        phase_ranges: Dict[str, Tuple[int, int]]
    ) -> Dict[str, Dict]:
        """
        Predict performance using features from specific phases

        Args:
            features_sequence: List of feature dicts
            phase_ranges: Phase boundaries

        Returns:
            predictions_by_phase: Dict of predictions for each phase
        """
        results = {}

        for phase_name, (start, end) in phase_ranges.items():
            # Extract features for this phase
            phase_features = features_sequence[start:end+1]

            if len(phase_features) > 0:
                # Aggregate and predict
                agg_features = self._aggregate_features(phase_features)
                predictions = self.predict(agg_features)
                results[phase_name] = predictions

        return results

    def get_feature_importance(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """
        Get top N most important features

        Args:
            top_n: Number of features to return

        Returns:
            List of (feature_name, importance) tuples
        """
        if self.feature_importance is None:
            return []

        indices = np.argsort(self.feature_importance)[-top_n:][::-1]

        return [
            (self.feature_names[i], self.feature_importance[i])
            for i in indices
        ]

    def _compute_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
        """Compute regression metrics for each target"""
        metrics = {
            'r2': [],
            'mae': [],
            'rmse': []
        }

        for i, target_name in enumerate(self.target_names):
            r2 = r2_score(y_true[:, i], y_pred[:, i])
            mae = mean_absolute_error(y_true[:, i], y_pred[:, i])
            rmse = np.sqrt(mean_squared_error(y_true[:, i], y_pred[:, i]))

            metrics['r2'].append(f"{target_name}={r2:.3f}")
            metrics['mae'].append(f"{target_name}={mae:.1f}")
            metrics['rmse'].append(f"{target_name}={rmse:.1f}")

        return metrics

    def _features_to_array(self, features: Dict[str, float]) -> np.ndarray:
        """Convert feature dict to numpy array matching training features"""
        if self.feature_names is None:
            raise ValueError("Feature names not set")

        X = []
        for name in self.feature_names:
            # Handle CaddieSet format (phase-FEATURE)
            if name in features:
                value = features[name]
            else:
                # Try to match without phase prefix
                base_name = name.split('-', 1)[-1] if '-' in name else name
                value = features.get(base_name, 0.0)

            # Replace None and NaN with 0.0
            if value is None or (isinstance(value, float) and np.isnan(value)):
                value = 0.0
            
            X.append(value)

        # Convert to numpy and ensure no NaN values
        X = np.array(X, dtype=np.float32)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        return X

    def _aggregate_features(self, features_sequence: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Aggregate features across frames (use mean)

        Args:
            features_sequence: List of feature dicts

        Returns:
            aggregated_features: Dict with mean values
        """
        if not features_sequence:
            return {}

        # Get all feature keys
        all_keys = set()
        for features in features_sequence:
            all_keys.update(features.keys())

        # Compute mean for each feature
        aggregated = {}
        for key in all_keys:
            values = [
                features[key]
                for features in features_sequence
                if key in features and features[key] is not None
            ]
            if values:
                aggregated[key] = np.mean(values)
            else:
                aggregated[key] = None

        return aggregated

    def _estimate_confidence(self, features_sequence: List[Dict[str, float]]) -> float:
        """
        Estimate prediction confidence based on feature consistency

        Args:
            features_sequence: List of feature dicts

        Returns:
            confidence: 0-100 (100 = very confident)
        """
        if len(features_sequence) < 2:
            return 50.0

        # Calculate coefficient of variation for key features
        key_features = ['SPINE_ANGLE', 'HIP_ROTATION', 'SHOULDER_ROTATION']
        cv_scores = []

        for key in key_features:
            values = [
                features[key]
                for features in features_sequence
                if key in features and features[key] is not None
            ]

            if len(values) > 1:
                mean_val = np.mean(values)
                std_val = np.std(values)
                cv = std_val / (abs(mean_val) + 1e-6)
                cv_scores.append(cv)

        if cv_scores:
            avg_cv = np.mean(cv_scores)
            # Lower CV = higher confidence
            confidence = max(0, min(100, 100 * (1 - avg_cv)))
        else:
            confidence = 50.0

        return confidence

    def save(self, filepath: str):
        """Save trained model to file"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'target_names': self.target_names,
            'feature_importance': self.feature_importance
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"💾 Performance predictor saved to {filepath}")

    def load(self, filepath: str):
        """Load trained model from file (supports both .pkl and .pt formats)"""
        import torch
        import os
        
        # Check if it's a PyTorch model
        if filepath.endswith('.pt'):
            self._load_pytorch_model(filepath)
            return
        
        # Try to load as PyTorch first if .pt version exists
        pt_filepath = filepath.replace('.pkl', '.pt')
        if os.path.exists(pt_filepath):
            self._load_pytorch_model(pt_filepath)
            return
        
        # Fall back to pickle format
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        self.model = model_data['model']
        self.scaler = model_data.get('scaler')
        self.feature_names = model_data['feature_names']
        self.target_names = model_data.get('target_names', self.target_names)
        self.feature_importance = model_data.get('feature_importance')

        print(f"📂 Performance predictor loaded from {filepath}")
    
    def _load_pytorch_model(self, filepath: str):
        """Load a PyTorch performance predictor model"""
        import torch
        import torch.nn as nn
        
        # Define the model architecture (must match training)
        class GolfPerformancePredictor(nn.Module):
            def __init__(self, input_size: int, hidden_sizes: list = [256, 128, 64], dropout: float = 0.2):
                super(GolfPerformancePredictor, self).__init__()
                
                layers = []
                prev_size = input_size
                
                layers.append(nn.BatchNorm1d(input_size))
                
                for hidden_size in hidden_sizes:
                    layers.append(nn.Linear(prev_size, hidden_size))
                    layers.append(nn.BatchNorm1d(hidden_size))
                    layers.append(nn.ReLU())
                    layers.append(nn.Dropout(dropout))
                    prev_size = hidden_size
                
                layers.append(nn.Linear(prev_size, 3))  # 3 outputs
                
                self.model = nn.Sequential(*layers)
                
            def forward(self, x):
                return self.model(x)
        
        # Load checkpoint
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        checkpoint = torch.load(filepath, map_location=device, weights_only=False)
        
        # Get model config
        config = checkpoint.get('model_config', {})
        input_size = config.get('input_size', 54)
        hidden_sizes = config.get('hidden_sizes', [256, 128, 64])
        dropout = config.get('dropout', 0.2)
        
        # Create and load model
        self.model = GolfPerformancePredictor(input_size, hidden_sizes, dropout)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(device)
        self.model.eval()
        
        # Store for inference
        self._device = device
        self._is_pytorch = True
        self._feature_scaler = checkpoint.get('feature_scaler')
        self._target_scaler = checkpoint.get('target_scaler')
        self._imputer = checkpoint.get('imputer')
        
        # Load other components
        self.feature_names = checkpoint.get('feature_names', [])
        self.target_names = checkpoint.get('targets', ['BallSpeed', 'Distance', 'Carry'])
        self.scaler = self._feature_scaler
        
        print(f"📂 PyTorch performance predictor loaded from {filepath}")
        print(f"   Device: {device}")
        print(f"   Targets: {self.target_names}")
    
    def _predict_pytorch(self, features: Dict[str, float]) -> Dict[str, float]:
        """Predict using PyTorch model"""
        import torch
        
        # Convert features dict to array
        X = self._features_to_array(features)
        
        # Handle missing values with imputer
        if self._imputer is not None:
            X = self._imputer.transform(X.reshape(1, -1))
        else:
            X = X.reshape(1, -1)
        
        # Handle infinite values
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Scale features
        if self._feature_scaler is not None:
            X_scaled = self._feature_scaler.transform(X)
        else:
            X_scaled = X
        
        # Convert to tensor and predict
        X_tensor = torch.FloatTensor(X_scaled).to(self._device)
        
        self.model.eval()
        with torch.no_grad():
            output = self.model(X_tensor)
            predictions_scaled = output.cpu().numpy()[0]
        
        # Inverse transform to original scale
        if self._target_scaler is not None:
            predictions = self._target_scaler.inverse_transform(predictions_scaled.reshape(1, -1))[0]
        else:
            predictions = predictions_scaled
        
        # Calculate confidence based on feature coverage and prediction reasonableness
        confidence = self._calculate_pytorch_confidence(features, predictions)
        
        return {
            'BallSpeed': float(predictions[0]),
            'Distance': float(predictions[1]),
            'Carry': float(predictions[2]),
            'confidence': float(confidence)
        }
    
    def _calculate_pytorch_confidence(self, features: Dict[str, float], predictions: np.ndarray) -> float:
        """
        Calculate confidence for PyTorch predictions
        
        Args:
            features: Original feature dictionary
            predictions: Model predictions [BallSpeed, Distance, Carry]
        
        Returns:
            Confidence score (0-100)
        """
        # Base confidence from feature coverage
        feature_coverage = self._calculate_feature_coverage(features)
        
        # Check prediction reasonableness
        ball_speed, distance, carry = predictions
        
        # Reasonable ranges for golf shots
        reasonable_ball_speed = 50 <= ball_speed <= 200  # mph
        reasonable_distance = 50 <= distance <= 350     # yards
        reasonable_carry = 40 <= carry <= 300          # yards
        reasonable_carry_distance = carry <= distance   # carry should be <= total distance
        
        # Calculate reasonableness score
        reasonableness_factors = [
            reasonable_ball_speed,
            reasonable_distance,
            reasonable_carry,
            reasonable_carry_distance
        ]
        
        reasonableness_score = sum(reasonableness_factors) / len(reasonableness_factors)
        
        # Combine factors: feature coverage (50%) + reasonableness (50%)
        confidence = (feature_coverage * 50) + (reasonableness_score * 50)
        
        # Clamp to realistic range
        confidence = max(25.0, min(85.0, confidence))
        
        return confidence


if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("Performance Predictor - Test")
    print("=" * 60)

    # Create synthetic test data
    np.random.seed(42)
    X_train = np.random.randn(1000, 50)
    y_train = np.random.randn(1000, 3) * 10 + [100, 200, 180]  # BallSpeed, Distance, Carry
    X_test = np.random.randn(200, 50)
    y_test = np.random.randn(200, 3) * 10 + [100, 200, 180]

    feature_names = [f'feature_{i}' for i in range(50)]

    # Train
    predictor = PerformancePredictor()
    metrics = predictor.train(X_train, y_train, X_test, y_test, feature_names)

    # Test prediction
    test_features = {f'feature_{i}': np.random.randn() for i in range(50)}
    predictions = predictor.predict(test_features)
    print(f"\nTest predictions: {predictions}")

    # Save
    Path("models").mkdir(exist_ok=True)
    predictor.save("models/performance_predictor.pkl")
