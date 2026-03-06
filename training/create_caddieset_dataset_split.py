"""
Create CaddieSet-Compatible Training Dataset with Train/Test Split

This script:
1. Reads train/test split from prepare_train_test_split.py
2. Only processes training videos (excludes test videos)
3. Extracts CaddieSet-compatible biomechanical features
4. Creates swing-level dataset for training

Output: training_data/golf_swings_dataset.csv
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from tqdm import tqdm
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')

from training.caddieset_feature_extractor import CaddieSetFeatureExtractor, SwingPhaseConfig


def load_train_videos(train_list_path: Path) -> Dict[str, List[Path]]:
    """
    Load training video list from file
    
    Returns:
        Dict with 'good' and 'bad' keys containing lists of video paths
    """
    videos = {'good': [], 'bad': []}
    
    if not train_list_path.exists():
        return videos
    
    with open(train_list_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('good:'):
                path = Path(line[5:])
                if path.exists():
                    videos['good'].append(path)
            elif line.startswith('bad:'):
                path = Path(line[4:])
                if path.exists():
                    videos['bad'].append(path)
    
    return videos


def discover_training_videos(base_path: Path, exclude_test: bool = True) -> Dict[str, List[Path]]:
    """
    Discover training videos, optionally excluding test videos
    
    Args:
        base_path: Base project path
        exclude_test: If True, exclude videos in test_videos folder
    
    Returns:
        Dict with 'good' and 'bad' keys containing lists of video paths
    """
    # First try to load from train list
    train_list_path = base_path / 'training_data' / 'train_videos.txt'
    if train_list_path.exists():
        print(f"📂 Loading training videos from: {train_list_path}")
        videos = load_train_videos(train_list_path)
        if videos['good'] or videos['bad']:
            return videos
    
    # Fallback: discover all videos and exclude test ones
    videos = {'good': [], 'bad': []}
    
    good_path = base_path / 'good_swings'
    bad_path = base_path / 'bad_swings'
    test_path = base_path / 'test_videos'
    
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    
    # Get test video names if excluding
    test_names = set()
    if exclude_test and test_path.exists():
        for ext in video_extensions:
            for test_video in (test_path / 'good_swings').glob(f'*{ext}'):
                test_names.add(test_video.name)
            for test_video in (test_path / 'bad_swings').glob(f'*{ext}'):
                test_names.add(test_video.name)
    
    if good_path.exists():
        for ext in video_extensions:
            for video in good_path.glob(f'*{ext}'):
                if video.name not in test_names:
                    videos['good'].append(video)
            for video in good_path.glob(f'*{ext.upper()}'):
                if video.name not in test_names:
                    videos['good'].append(video)
    
    if bad_path.exists():
        for ext in video_extensions:
            for video in bad_path.glob(f'*{ext}'):
                if video.name not in test_names:
                    videos['bad'].append(video)
            for video in bad_path.glob(f'*{ext.upper()}'):
                if video.name not in test_names:
                    videos['bad'].append(video)
    
    # Remove duplicates
    videos['good'] = list(set(videos['good']))
    videos['bad'] = list(set(videos['bad']))
    
    return videos


def load_reference_caddieset(csv_path: Path) -> pd.DataFrame:
    """Load CaddieSet.csv to understand feature distribution"""
    if not csv_path.exists():
        return None
    
    df = pd.read_csv(csv_path)
    print(f"\n📊 Reference CaddieSet Statistics:")
    print(f"   Total swings: {len(df)}")
    print(f"   Columns: {len(df.columns)}")
    
    feature_cols = [col for col in df.columns if '-' in col and col[0].isdigit()]
    print(f"   Feature columns: {len(feature_cols)}")
    
    return df


def compute_dataset_statistics(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """Compute statistics for each feature to enable normalization"""
    stats = {}
    feature_cols = [col for col in df.columns if '-' in col and col[0].isdigit()]
    
    for col in feature_cols:
        values = df[col].dropna()
        if len(values) > 0:
            stats[col] = {
                'mean': float(values.mean()),
                'std': float(values.std()) if len(values) > 1 else 1.0,
                'min': float(values.min()),
                'max': float(values.max()),
                'median': float(values.median())
            }
    
    return stats


def main():
    print("=" * 70)
    print("Creating Training Dataset (Excluding Test Videos)")
    print("=" * 70)
    
    base_path = Path(__file__).parent.parent
    
    # Discover training videos (excluding test set)
    videos = discover_training_videos(base_path, exclude_test=True)
    
    print(f"\n📂 Training Videos (excluding test set):")
    print(f"   Good swings: {len(videos['good'])}")
    for v in videos['good']:
        print(f"      - {v.name}")
    print(f"   Bad swings: {len(videos['bad'])}")
    for v in videos['bad']:
        print(f"      - {v.name}")
    
    if not videos['good'] and not videos['bad']:
        print("\n❌ No training videos found!")
        print("   Please run 'python training/prepare_train_test_split.py' first")
        return
    
    # Load reference CaddieSet
    reference_df = load_reference_caddieset(base_path / 'CaddieSet.csv')
    
    # Initialize feature extractor with smoothing
    config = SwingPhaseConfig(
        min_frames=3,
        smoothing_window=7,
        velocity_threshold=0.02
    )
    extractor = CaddieSetFeatureExtractor(config)
    
    # Extract features from training videos
    all_swings = []
    
    print("\n" + "=" * 70)
    print("Extracting Features from Training Videos")
    print("=" * 70)
    
    for label, video_list in videos.items():
        is_good = (label == 'good')
        
        for video_path in tqdm(video_list, desc=f"Processing {label} swings"):
            try:
                print(f"\n{'='*50}")
                print(f"Processing: {video_path.name} (label: {label})")
                
                # Extract features
                features = extractor.extract_from_video(
                    str(video_path),
                    preprocess=True,
                    verbose=True
                )
                
                if not features:
                    print(f"  ⚠️ No features extracted from {video_path.name}")
                    continue
                
                # Add metadata
                swing_data = {
                    'video_name': video_path.name,
                    'video_path': str(video_path),
                    'quality_label': 0 if is_good else 1,
                    'quality_name': 'good' if is_good else 'bad'
                }
                
                # Add extracted features
                swing_data.update(features)
                
                all_swings.append(swing_data)
                
                print(f"  ✅ Extracted {len(features)} features")
                
            except Exception as e:
                print(f"  ❌ Error processing {video_path.name}: {e}")
                import traceback
                traceback.print_exc()
    
    extractor.close()
    
    if not all_swings:
        print("\n❌ No features were extracted from any video!")
        return
    
    # Create DataFrame
    df = pd.DataFrame(all_swings)
    
    print(f"\n" + "=" * 70)
    print("Dataset Summary")
    print("=" * 70)
    print(f"Total training swings: {len(df)}")
    print(f"Good swings: {(df['quality_label'] == 0).sum()}")
    print(f"Bad swings: {(df['quality_label'] == 1).sum()}")
    print(f"Features: {len([c for c in df.columns if '-' in c and c[0].isdigit()])}")
    
    # Get feature columns
    feature_cols = sorted([c for c in df.columns if '-' in c and c[0].isdigit()])
    
    print(f"\n📊 Extracted Feature Columns ({len(feature_cols)}):")
    for i, col in enumerate(feature_cols[:20], 1):
        sample_val = df[col].dropna().iloc[0] if not df[col].dropna().empty else 'N/A'
        print(f"   {i:2d}. {col}: {sample_val:.2f}" if isinstance(sample_val, (int, float)) else f"   {i:2d}. {col}: {sample_val}")
    if len(feature_cols) > 20:
        print(f"   ... and {len(feature_cols) - 20} more features")
    
    # Compare with reference CaddieSet
    if reference_df is not None:
        ref_feature_cols = [c for c in reference_df.columns if '-' in c and c[0].isdigit()]
        common_features = set(feature_cols) & set(ref_feature_cols)
        print(f"\n📈 CaddieSet Compatibility:")
        print(f"   Reference features: {len(ref_feature_cols)}")
        print(f"   Extracted features: {len(feature_cols)}")
        print(f"   Common features: {len(common_features)}")
    
    # Save dataset
    output_dir = base_path / 'training_data'
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / 'golf_swings_dataset.csv'
    df.to_csv(output_path, index=False)
    print(f"\n💾 Dataset saved to: {output_path}")
    
    # Compute and save statistics
    stats = compute_dataset_statistics(df)
    stats_path = output_dir / 'dataset_statistics.csv'
    stats_df = pd.DataFrame(stats).T
    stats_df.to_csv(stats_path)
    print(f"💾 Statistics saved to: {stats_path}")
    
    # Print class balance warning if needed
    good_count = (df['quality_label'] == 0).sum()
    bad_count = (df['quality_label'] == 1).sum()
    if good_count == 0 or bad_count == 0:
        print(f"\n⚠️  WARNING: Dataset is missing one class!")
    elif abs(good_count - bad_count) / max(good_count, bad_count) > 0.5:
        print(f"\n⚠️  WARNING: Class imbalance detected!")
        print(f"   Good: {good_count}, Bad: {bad_count}")
    
    print("\n" + "=" * 70)
    print("✅ Training Dataset Creation Complete")
    print("=" * 70)
    print(f"\nNext step: Run 'python training/train_pytorch_models.py' to train models")


if __name__ == '__main__':
    main()
