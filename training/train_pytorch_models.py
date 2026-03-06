"""
Train Golf Swing Analysis Models using PyTorch with CUDA Support

This script trains deep learning models instead of sklearn pickle models:
1. Swing Quality Classifier - Neural network for classifying good vs bad swings
2. Performance Predictor - Neural network for predicting ball speed, distance, carry

Key improvements:
- Uses PyTorch with CUDA GPU acceleration
- K-Fold Cross-Validation for small datasets (more reliable metrics)
- Strong regularization (dropout, weight decay, label smoothing)
- Early stopping and learning rate scheduling
- Saves models as .pt files (PyTorch format)
- Honest metrics reporting (no overfitting artifacts)

Usage:
    python training/train_pytorch_models.py
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import json
import warnings
warnings.filterwarnings('ignore')

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split, StratifiedKFold, LeaveOneOut
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    f1_score,
    roc_auc_score,
    accuracy_score
)


# Check CUDA availability
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Memory Available: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")


class GolfSwingClassifier(nn.Module):
    """
    Deep neural network for golf swing quality classification
    
    Architecture:
    - Input layer with batch normalization
    - 4 hidden layers with dropout and ReLU activation
    - Output layer with sigmoid for binary classification
    """
    
    def __init__(self, input_size: int, hidden_sizes: List[int] = [256, 128, 64, 32], dropout: float = 0.3):
        super(GolfSwingClassifier, self).__init__()
        
        layers = []
        prev_size = input_size
        
        # Input batch normalization
        layers.append(nn.BatchNorm1d(input_size))
        
        # Hidden layers
        for hidden_size in hidden_sizes:
            layers.append(nn.Linear(prev_size, hidden_size))
            layers.append(nn.BatchNorm1d(hidden_size))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev_size = hidden_size
        
        # Output layer
        layers.append(nn.Linear(prev_size, 1))
        layers.append(nn.Sigmoid())
        
        self.model = nn.Sequential(*layers)
        
    def forward(self, x):
        return self.model(x)


class GolfPerformancePredictor(nn.Module):
    """
    Deep neural network for golf performance prediction
    
    Predicts: Ball Speed, Distance, Carry
    """
    
    def __init__(self, input_size: int, hidden_sizes: List[int] = [256, 128, 64], dropout: float = 0.2):
        super(GolfPerformancePredictor, self).__init__()
        
        layers = []
        prev_size = input_size
        
        # Input batch normalization
        layers.append(nn.BatchNorm1d(input_size))
        
        # Hidden layers
        for hidden_size in hidden_sizes:
            layers.append(nn.Linear(prev_size, hidden_size))
            layers.append(nn.BatchNorm1d(hidden_size))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev_size = hidden_size
        
        # Output layer (3 targets: BallSpeed, Distance, Carry)
        layers.append(nn.Linear(prev_size, 3))
        
        self.model = nn.Sequential(*layers)
        
    def forward(self, x):
        return self.model(x)


class GolfModelTrainer:
    """
    Train and evaluate golf swing analysis models using PyTorch
    """
    
    def __init__(self, dataset_path: str, reference_path: Optional[str] = None):
        """
        Initialize trainer
        
        Args:
            dataset_path: Path to extracted swing features CSV
            reference_path: Optional path to CaddieSet.csv for reference
        """
        self.dataset_path = Path(dataset_path)
        self.reference_path = Path(reference_path) if reference_path else None
        
        self.df = None
        self.reference_df = None
        self.feature_cols = None
        self.scaler = None
        self.imputer = None
        
    def load_data(self) -> bool:
        """Load and validate dataset"""
        print("\n" + "=" * 70)
        print("Loading Dataset")
        print("=" * 70)
        
        if not self.dataset_path.exists():
            print(f"❌ Dataset not found: {self.dataset_path}")
            print(f"   Run 'python training/create_caddieset_dataset.py' first")
            return False
        
        self.df = pd.read_csv(self.dataset_path)
        print(f"✅ Loaded {len(self.df)} swings from {self.dataset_path.name}")
        
        # Load reference CaddieSet if available
        if self.reference_path and self.reference_path.exists():
            self.reference_df = pd.read_csv(self.reference_path)
            print(f"✅ Loaded {len(self.reference_df)} reference swings from CaddieSet")
        
        # Get feature columns (phase-prefixed)
        self.feature_cols = sorted([
            col for col in self.df.columns 
            if '-' in col and col[0].isdigit()
        ])
        
        print(f"\n📊 Dataset Statistics:")
        print(f"   Total swings: {len(self.df)}")
        print(f"   Feature columns: {len(self.feature_cols)}")
        
        if 'quality_label' in self.df.columns:
            good_count = (self.df['quality_label'] == 0).sum()
            bad_count = (self.df['quality_label'] == 1).sum()
            print(f"   Good swings: {good_count}")
            print(f"   Bad swings: {bad_count}")
            
            if good_count == 0 or bad_count == 0:
                print(f"\n❌ ERROR: Need both good and bad swings for training!")
                return False
        
        return True
    
    def prepare_features(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features for training
        
        Returns:
            X: Feature matrix
            y: Labels (0=good, 1=bad)
        """
        print("\n" + "=" * 70)
        print("Preparing Features")
        print("=" * 70)
        
        # Extract features and labels
        X = self.df[self.feature_cols].values
        y = self.df['quality_label'].values
        
        print(f"Initial shape: X={X.shape}, y={y.shape}")
        
        # Handle missing values with imputation
        self.imputer = SimpleImputer(strategy='median')
        X = self.imputer.fit_transform(X)
        
        # Handle infinite values
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Use RobustScaler for better handling of outliers
        self.scaler = RobustScaler()
        X = self.scaler.fit_transform(X)
        
        print(f"After preprocessing: X={X.shape}")
        print(f"   NaN count: {np.isnan(X).sum()}")
        print(f"   Inf count: {np.isinf(X).sum()}")
        
        return X, y
    
    def train_quality_classifier(
        self, 
        X: np.ndarray, 
        y: np.ndarray,
        epochs: int = 150,
        batch_size: int = 4,
        learning_rate: float = 0.0005,
        patience: int = 30,
        n_folds: int = 5
    ) -> Dict:
        """
        Train swing quality classifier with PyTorch using K-Fold Cross-Validation
        
        For small datasets (<50 samples), uses K-Fold CV to get reliable metrics.
        
        Args:
            X: Feature matrix
            y: Labels
            epochs: Number of training epochs
            batch_size: Batch size for training
            learning_rate: Initial learning rate
            patience: Early stopping patience
            n_folds: Number of cross-validation folds
        
        Returns:
            results: Dictionary with model and metrics
        """
        print("\n" + "=" * 70)
        print("Training Swing Quality Classifier (PyTorch + K-Fold CV)")
        print("=" * 70)
        
        # Check class balance
        unique, counts = np.unique(y, return_counts=True)
        print(f"\nClass distribution: {dict(zip(unique, counts))}")
        
        # Adjust folds based on dataset size
        min_class_size = min(counts)
        n_folds = min(n_folds, min_class_size)
        n_folds = max(2, n_folds)
        
        print(f"\n⚠️  Small dataset ({len(y)} samples) - Using {n_folds}-Fold Cross-Validation")
        print("   This provides more reliable performance estimates than train/test split")
        
        # Initialize model architecture for final model
        input_size = X.shape[1]
        
        # Use smaller architecture for small datasets to prevent overfitting
        if len(y) < 50:
            hidden_sizes = [64, 32, 16]
            dropout = 0.5  # Higher dropout for small datasets
        else:
            hidden_sizes = [128, 64, 32]
            dropout = 0.4
        
        # Cross-validation
        cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
        
        fold_accuracies = []
        fold_f1s = []
        fold_aucs = []
        all_y_true = []
        all_y_pred = []
        all_y_proba = []
        
        print(f"\n🔄 Running {n_folds}-Fold Cross-Validation...")
        
        for fold, (train_idx, val_idx) in enumerate(cv.split(X, y)):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            # Convert to tensors
            X_train_t = torch.FloatTensor(X_train).to(device)
            y_train_t = torch.FloatTensor(y_train).unsqueeze(1).to(device)
            X_val_t = torch.FloatTensor(X_val).to(device)
            y_val_t = torch.FloatTensor(y_val).unsqueeze(1).to(device)
            
            # Create dataloader
            train_dataset = TensorDataset(X_train_t, y_train_t)
            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, drop_last=False)
            
            # Initialize fresh model for each fold
            model = GolfSwingClassifier(
                input_size=input_size,
                hidden_sizes=hidden_sizes,
                dropout=dropout
            ).to(device)
            
            # Loss with label smoothing to prevent overconfidence
            criterion = nn.BCELoss()
            optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.1)
            scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
            
            # Training loop for this fold
            best_val_loss = float('inf')
            best_model_state = None
            patience_counter = 0
            
            for epoch in range(epochs):
                # Training phase
                model.train()
                for batch_X, batch_y in train_loader:
                    optimizer.zero_grad()
                    outputs = model(batch_X)
                    # Label smoothing
                    smooth_y = batch_y * 0.9 + 0.05
                    loss = criterion(outputs, smooth_y)
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                    optimizer.step()
                
                scheduler.step()
                
                # Validation phase
                model.eval()
                with torch.no_grad():
                    val_outputs = model(X_val_t)
                    val_loss = criterion(val_outputs, y_val_t).item()
                
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_model_state = model.state_dict().copy()
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if patience_counter >= patience:
                    break
            
            # Evaluate fold
            model.load_state_dict(best_model_state)
            model.eval()
            with torch.no_grad():
                val_outputs = model(X_val_t)
                val_preds = (val_outputs > 0.5).float().cpu().numpy().flatten()
                val_probs = val_outputs.cpu().numpy().flatten()
            
            y_val_np = y_val_t.cpu().numpy().flatten()
            
            fold_acc = accuracy_score(y_val_np, val_preds)
            fold_f1 = f1_score(y_val_np, val_preds, average='weighted', zero_division=0)
            try:
                fold_auc = roc_auc_score(y_val_np, val_probs)
            except:
                fold_auc = 0.5
            
            fold_accuracies.append(fold_acc)
            fold_f1s.append(fold_f1)
            fold_aucs.append(fold_auc)
            
            all_y_true.extend(y_val_np.tolist())
            all_y_pred.extend(val_preds.tolist())
            all_y_proba.extend(val_probs.tolist())
            
            print(f"   Fold {fold+1}: Acc={fold_acc:.3f}, F1={fold_f1:.3f}, AUC={fold_auc:.3f}")
        
        # Calculate cross-validation metrics
        cv_accuracy = np.mean(fold_accuracies)
        cv_accuracy_std = np.std(fold_accuracies)
        cv_f1 = np.mean(fold_f1s)
        cv_f1_std = np.std(fold_f1s)
        cv_auc = np.mean(fold_aucs)
        cv_auc_std = np.std(fold_aucs)
        
        print(f"\n📊 Cross-Validation Results ({n_folds}-Fold):")
        print(f"   Accuracy: {cv_accuracy:.3f} ± {cv_accuracy_std:.3f}")
        print(f"   F1 Score: {cv_f1:.3f} ± {cv_f1_std:.3f}")
        print(f"   ROC-AUC:  {cv_auc:.3f} ± {cv_auc_std:.3f}")
        
        # Overall confusion matrix from all folds
        cm = confusion_matrix(all_y_true, all_y_pred)
        print(f"\n   Combined Confusion Matrix:")
        print(f"              Predicted")
        print(f"              Good   Bad")
        print(f"   Actual Good  {int(cm[0][0]):4d}  {int(cm[0][1]):4d}")
        print(f"   Actual Bad   {int(cm[1][0]):4d}  {int(cm[1][1]):4d}")
        
        # Classification report from CV predictions
        print(f"\n   Classification Report (from CV):")
        print(classification_report(all_y_true, all_y_pred, target_names=['Good', 'Bad'], zero_division=0))
        
        # =====================================================================
        # Train FINAL model on ALL data (for deployment)
        # =====================================================================
        print(f"\n🏋️ Training final model on ALL {len(y)} samples...")
        
        # Convert all data to tensors
        X_all_t = torch.FloatTensor(X).to(device)
        y_all_t = torch.FloatTensor(y).unsqueeze(1).to(device)
        
        all_dataset = TensorDataset(X_all_t, y_all_t)
        all_loader = DataLoader(all_dataset, batch_size=batch_size, shuffle=True, drop_last=False)
        
        # Fresh model for final training
        final_model = GolfSwingClassifier(
            input_size=input_size,
            hidden_sizes=hidden_sizes,
            dropout=dropout
        ).to(device)
        
        criterion = nn.BCELoss()
        optimizer = optim.AdamW(final_model.parameters(), lr=learning_rate, weight_decay=0.1)
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
        
        # Train for fixed epochs (no validation split)
        for epoch in range(epochs):
            final_model.train()
            for batch_X, batch_y in all_loader:
                optimizer.zero_grad()
                outputs = final_model(batch_X)
                smooth_y = batch_y * 0.9 + 0.05
                loss = criterion(outputs, smooth_y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(final_model.parameters(), max_norm=1.0)
                optimizer.step()
            scheduler.step()
            
            if (epoch + 1) % 50 == 0:
                print(f"   Final model epoch {epoch+1}/{epochs}")
        
        print("✅ Final model trained")
        
        # Store final model's hidden_sizes and dropout for saving
        self._final_hidden_sizes = hidden_sizes
        self._final_dropout = dropout
        
        return {
            'model': final_model,
            'cv_accuracy': cv_accuracy,
            'cv_accuracy_std': cv_accuracy_std,
            'cv_f1': cv_f1,
            'cv_f1_std': cv_f1_std,
            'cv_auc': cv_auc,
            'cv_auc_std': cv_auc_std,
            'confusion_matrix': cm.tolist(),
            'n_folds': n_folds
        }
    
    def train_performance_predictor(
        self,
        X: np.ndarray,
        epochs: int = 200,
        batch_size: int = 16,
        learning_rate: float = 0.001,
        patience: int = 25
    ) -> Optional[Dict]:
        """
        Train performance prediction model using CaddieSet data
        
        Args:
            X: Feature matrix from extracted swings
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Initial learning rate
            patience: Early stopping patience
        
        Returns:
            results: Dictionary with model and metrics
        """
        print("\n" + "=" * 70)
        print("Training Performance Predictor (PyTorch + CUDA)")
        print("=" * 70)
        
        if self.reference_df is None:
            print("⚠️  CaddieSet not loaded. Skipping performance predictor.")
            return None
        
        # Extract features and targets from CaddieSet
        caddie_features = [c for c in self.reference_df.columns 
                         if '-' in c and c[0].isdigit()]
        
        # Find common features
        common_features = list(set(caddie_features) & set(self.feature_cols))
        print(f"   Using {len(common_features)} common features with CaddieSet")
        
        if len(common_features) < 10:
            print("   ⚠️  Too few common features. Using all CaddieSet features.")
            common_features = caddie_features
        
        # Prepare CaddieSet data
        X_caddie = self.reference_df[common_features].values
        
        # Target variables
        targets = ['BallSpeed', 'Distance', 'Carry']
        missing_targets = [t for t in targets if t not in self.reference_df.columns]
        if missing_targets:
            print(f"   ⚠️  Missing targets: {missing_targets}")
            print("   Cannot train performance predictor without target data.")
            return None
        
        y_caddie = self.reference_df[targets].values
        
        # Handle missing values
        caddie_imputer = SimpleImputer(strategy='median')
        X_caddie = np.nan_to_num(X_caddie, nan=np.nan, posinf=np.nan, neginf=np.nan)
        X_caddie = caddie_imputer.fit_transform(X_caddie)
        
        # Handle NaN in targets
        valid_mask = ~np.isnan(y_caddie).any(axis=1)
        X_caddie = X_caddie[valid_mask]
        y_caddie = y_caddie[valid_mask]
        
        print(f"   CaddieSet samples: {len(X_caddie)}")
        
        # Normalize features and targets
        from sklearn.preprocessing import StandardScaler
        feature_scaler = StandardScaler()
        target_scaler = StandardScaler()
        
        X_caddie_scaled = feature_scaler.fit_transform(X_caddie)
        y_caddie_scaled = target_scaler.fit_transform(y_caddie)
        
        # Split data
        X_train, X_temp, y_train, y_temp = train_test_split(
            X_caddie_scaled, y_caddie_scaled, test_size=0.3, random_state=42
        )
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=0.5, random_state=42
        )
        
        print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        # Convert to PyTorch tensors
        X_train_t = torch.FloatTensor(X_train).to(device)
        y_train_t = torch.FloatTensor(y_train).to(device)
        X_val_t = torch.FloatTensor(X_val).to(device)
        y_val_t = torch.FloatTensor(y_val).to(device)
        X_test_t = torch.FloatTensor(X_test).to(device)
        y_test_t = torch.FloatTensor(y_test).to(device)
        
        # Create dataloaders
        train_dataset = TensorDataset(X_train_t, y_train_t)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        
        # Initialize model
        input_size = X_caddie_scaled.shape[1]
        model = GolfPerformancePredictor(
            input_size=input_size,
            hidden_sizes=[256, 128, 64],
            dropout=0.2
        ).to(device)
        
        print(f"\n📦 Model Architecture:")
        print(model)
        total_params = sum(p.numel() for p in model.parameters())
        print(f"\nTotal parameters: {total_params:,}")
        
        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=10, factor=0.5)
        
        # Training loop
        best_val_loss = float('inf')
        best_model_state = None
        patience_counter = 0
        
        print(f"\n🚀 Starting training for {epochs} epochs...")
        
        for epoch in range(epochs):
            # Training phase
            model.train()
            epoch_loss = 0
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            
            train_loss = epoch_loss / len(train_loader)
            
            # Validation phase
            model.eval()
            with torch.no_grad():
                val_outputs = model(X_val_t)
                val_loss = criterion(val_outputs, y_val_t).item()
            
            scheduler.step(val_loss)
            
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_model_state = model.state_dict().copy()
                patience_counter = 0
            else:
                patience_counter += 1
            
            if (epoch + 1) % 20 == 0:
                print(f"   Epoch {epoch+1:3d}: Train Loss={train_loss:.4f}, Val Loss={val_loss:.4f}")
            
            if patience_counter >= patience:
                print(f"\n⏹️  Early stopping at epoch {epoch+1}")
                break
        
        # Load best model
        model.load_state_dict(best_model_state)
        
        # Evaluation
        model.eval()
        with torch.no_grad():
            test_outputs = model(X_test_t)
        
        # Inverse transform to original scale
        y_test_orig = target_scaler.inverse_transform(y_test_t.cpu().numpy())
        y_pred_orig = target_scaler.inverse_transform(test_outputs.cpu().numpy())
        
        # Compute R² score
        from sklearn.metrics import r2_score, mean_absolute_error
        r2 = r2_score(y_test_orig, y_pred_orig)
        
        print(f"\n📊 Test Results:")
        print(f"   Overall R²: {r2:.3f}")
        
        for i, target in enumerate(targets):
            target_r2 = r2_score(y_test_orig[:, i], y_pred_orig[:, i])
            mae = mean_absolute_error(y_test_orig[:, i], y_pred_orig[:, i])
            print(f"\n   {target}:")
            print(f"      R²: {target_r2:.3f}")
            print(f"      MAE: {mae:.2f}")
        
        return {
            'model': model,
            'feature_scaler': feature_scaler,
            'target_scaler': target_scaler,
            'caddie_imputer': caddie_imputer,
            'feature_names': common_features,
            'targets': targets,
            'test_r2': r2
        }
    
    def save_models(
        self,
        classifier_results: Dict,
        predictor_results: Optional[Dict],
        output_dir: Path
    ):
        """Save trained PyTorch models"""
        print("\n" + "=" * 70)
        print("Saving Models")
        print("=" * 70)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get hidden sizes from training
        hidden_sizes = getattr(self, '_final_hidden_sizes', [64, 32, 16])
        dropout = getattr(self, '_final_dropout', 0.5)
        
        # Save classifier
        classifier_path = output_dir / 'swing_quality_classifier.pt'
        torch.save({
            'model_state_dict': classifier_results['model'].state_dict(),
            'model_config': {
                'input_size': len(self.feature_cols),
                'hidden_sizes': hidden_sizes,
                'dropout': dropout
            },
            'scaler': self.scaler,
            'imputer': self.imputer,
            'feature_names': self.feature_cols,
            'metrics': {
                'cv_accuracy': classifier_results['cv_accuracy'],
                'cv_f1': classifier_results['cv_f1'],
                'cv_auc': classifier_results['cv_auc']
            }
        }, classifier_path)
        print(f"💾 Saved classifier: {classifier_path}")
        
        # Also save for compatibility with fault_detector
        fault_detector_path = output_dir / 'fault_detector.pt'
        torch.save({
            'model_state_dict': classifier_results['model'].state_dict(),
            'model_config': {
                'input_size': len(self.feature_cols),
                'hidden_sizes': hidden_sizes,
                'dropout': dropout
            },
            'scaler': self.scaler,
            'imputer': self.imputer,
            'feature_names': self.feature_cols,
            'metrics': {
                'cv_accuracy': classifier_results['cv_accuracy'],
                'cv_f1': classifier_results['cv_f1'],
                'cv_auc': classifier_results['cv_auc']
            }
        }, fault_detector_path)
        print(f"💾 Saved (compatibility): {fault_detector_path}")
        
        # Save predictor if available
        if predictor_results:
            predictor_path = output_dir / 'performance_predictor.pt'
            torch.save({
                'model_state_dict': predictor_results['model'].state_dict(),
                'model_config': {
                    'input_size': len(predictor_results['feature_names']),
                    'hidden_sizes': [256, 128, 64],
                    'dropout': 0.2
                },
                'feature_scaler': predictor_results['feature_scaler'],
                'target_scaler': predictor_results['target_scaler'],
                'imputer': predictor_results['caddie_imputer'],
                'feature_names': predictor_results['feature_names'],
                'targets': predictor_results['targets'],
                'metrics': {
                    'test_r2': predictor_results['test_r2']
                }
            }, predictor_path)
            print(f"💾 Saved predictor: {predictor_path}")
        
        # Save training report with honest metrics
        report = {
            'dataset': str(self.dataset_path),
            'num_swings': len(self.df),
            'num_features': len(self.feature_cols),
            'device': str(device),
            'classifier': {
                'cv_accuracy': classifier_results['cv_accuracy'],
                'cv_accuracy_std': classifier_results['cv_accuracy_std'],
                'cv_f1': classifier_results['cv_f1'],
                'cv_f1_std': classifier_results['cv_f1_std'],
                'cv_auc': classifier_results['cv_auc'],
                'cv_auc_std': classifier_results['cv_auc_std'],
                'n_folds': classifier_results['n_folds'],
                'confusion_matrix': classifier_results['confusion_matrix'],
                'note': 'Metrics from K-Fold Cross-Validation (honest estimate)'
            }
        }
        if predictor_results:
            report['predictor'] = {
                'test_r2': predictor_results['test_r2']
            }
        
        report_path = output_dir / 'training_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📝 Saved report: {report_path}")


def main():
    print("=" * 70)
    print("🏌️ Golf Swing Model Training Pipeline (PyTorch + CUDA)")
    print("=" * 70)
    
    base_path = Path(__file__).parent.parent
    
    # Paths
    dataset_path = base_path / 'training_data' / 'golf_swings_dataset.csv'
    reference_path = base_path / 'CaddieSet.csv'
    output_dir = base_path / 'models'
    
    # Initialize trainer
    trainer = GolfModelTrainer(
        dataset_path=str(dataset_path),
        reference_path=str(reference_path)
    )
    
    # Load data
    if not trainer.load_data():
        print("\n❌ Failed to load data. Exiting.")
        return
    
    # Prepare features
    X, y = trainer.prepare_features()
    
    # Train quality classifier
    classifier_results = trainer.train_quality_classifier(
        X, y,
        epochs=200,
        batch_size=8,
        learning_rate=0.001,
        patience=25
    )
    
    # Train performance predictor (using CaddieSet)
    predictor_results = trainer.train_performance_predictor(
        X,
        epochs=200,
        batch_size=16,
        learning_rate=0.001,
        patience=30
    )
    
    # Save models
    trainer.save_models(classifier_results, predictor_results, output_dir)
    
    print("\n" + "=" * 70)
    print("✅ Training Complete")
    print("=" * 70)
    print("\n📦 Trained Models (PyTorch):")
    print(f"   • {output_dir}/swing_quality_classifier.pt")
    print(f"   • {output_dir}/fault_detector.pt (compatibility)")
    if predictor_results:
        print(f"   • {output_dir}/performance_predictor.pt")
    
    print("\n🚀 Next Steps:")
    print("   1. Run: python analyze_video.py --video your_video.mp4")
    print("   2. Or use the web app: python golf_coach_app.py")


if __name__ == '__main__':
    main()
