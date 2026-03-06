"""
Prepare Training Data with Train/Test Split

This script:
1. Creates a test set by reserving some videos from good_swings/ and bad_swings/
2. Moves test videos to test_videos/ folder
3. Then runs the dataset creation on remaining training videos

Usage:
    python training/prepare_train_test_split.py
"""

import sys
from pathlib import Path
import shutil
import random

sys.path.append(str(Path(__file__).parent.parent))


def prepare_train_test_split(
    good_swings_path: Path,
    bad_swings_path: Path,
    test_output_path: Path,
    num_test_good: int = 2,
    num_test_bad: int = 3,
    seed: int = 42
):
    """
    Prepare train/test split by moving some videos to test folder
    
    Args:
        good_swings_path: Path to good swing videos
        bad_swings_path: Path to bad swing videos
        test_output_path: Path to save test videos
        num_test_good: Number of good swing videos for testing
        num_test_bad: Number of bad swing videos for testing
        seed: Random seed for reproducibility
    """
    random.seed(seed)
    
    print("=" * 70)
    print("Preparing Train/Test Split")
    print("=" * 70)
    
    # Create test directories
    test_good_path = test_output_path / 'good_swings'
    test_bad_path = test_output_path / 'bad_swings'
    test_good_path.mkdir(parents=True, exist_ok=True)
    test_bad_path.mkdir(parents=True, exist_ok=True)
    
    # Discover videos
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    
    good_videos = []
    bad_videos = []
    
    for ext in video_extensions:
        good_videos.extend(good_swings_path.glob(f'*{ext}'))
        good_videos.extend(good_swings_path.glob(f'*{ext.upper()}'))
        bad_videos.extend(bad_swings_path.glob(f'*{ext}'))
        bad_videos.extend(bad_swings_path.glob(f'*{ext.upper()}'))
    
    # Remove duplicates and sort
    good_videos = sorted(list(set(good_videos)))
    bad_videos = sorted(list(set(bad_videos)))
    
    print(f"\n📂 Found Videos:")
    print(f"   Good swings: {len(good_videos)}")
    print(f"   Bad swings: {len(bad_videos)}")
    
    # Check if we have enough videos
    if len(good_videos) < num_test_good + 2:
        print(f"\n⚠️  Not enough good swing videos for split.")
        print(f"   Have: {len(good_videos)}, Need at least: {num_test_good + 2}")
        num_test_good = max(0, len(good_videos) - 2)
    
    if len(bad_videos) < num_test_bad + 2:
        print(f"\n⚠️  Not enough bad swing videos for split.")
        print(f"   Have: {len(bad_videos)}, Need at least: {num_test_bad + 2}")
        num_test_bad = max(0, len(bad_videos) - 2)
    
    # Randomly select test videos
    random.shuffle(good_videos)
    random.shuffle(bad_videos)
    
    test_good = good_videos[:num_test_good]
    test_bad = bad_videos[:num_test_bad]
    
    print(f"\n🎯 Test Set Selection:")
    print(f"   Good swings for test: {num_test_good}")
    for v in test_good:
        print(f"      - {v.name}")
    print(f"   Bad swings for test: {num_test_bad}")
    for v in test_bad:
        print(f"      - {v.name}")
    
    # Copy test videos to test folder (not move, to keep originals)
    print(f"\n📁 Copying test videos to {test_output_path}...")
    
    for video in test_good:
        dest = test_good_path / video.name
        shutil.copy2(video, dest)
        print(f"   ✅ Copied {video.name} -> test/good_swings/")
    
    for video in test_bad:
        dest = test_bad_path / video.name
        shutil.copy2(video, dest)
        print(f"   ✅ Copied {video.name} -> test/bad_swings/")
    
    # Create train list file (remaining videos)
    train_good = good_videos[num_test_good:]
    train_bad = bad_videos[num_test_bad:]
    
    train_list_path = test_output_path.parent / 'training_data' / 'train_videos.txt'
    train_list_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(train_list_path, 'w') as f:
        f.write("# Training Videos\n")
        f.write("# Good Swings\n")
        for v in train_good:
            f.write(f"good:{v}\n")
        f.write("# Bad Swings\n")
        for v in train_bad:
            f.write(f"bad:{v}\n")
    
    test_list_path = test_output_path.parent / 'training_data' / 'test_videos.txt'
    with open(test_list_path, 'w') as f:
        f.write("# Test Videos\n")
        f.write("# Good Swings\n")
        for v in test_good:
            f.write(f"good:{v}\n")
        f.write("# Bad Swings\n")
        for v in test_bad:
            f.write(f"bad:{v}\n")
    
    print(f"\n📝 Train/Test lists saved:")
    print(f"   Train list: {train_list_path}")
    print(f"   Test list: {test_list_path}")
    
    print(f"\n📊 Final Split Summary:")
    print(f"   Training: {len(train_good)} good + {len(train_bad)} bad = {len(train_good) + len(train_bad)} total")
    print(f"   Testing:  {len(test_good)} good + {len(test_bad)} bad = {len(test_good) + len(test_bad)} total")
    
    return {
        'train_good': train_good,
        'train_bad': train_bad,
        'test_good': test_good,
        'test_bad': test_bad
    }


def main():
    base_path = Path(__file__).parent.parent
    
    good_swings_path = base_path / 'good_swings'
    bad_swings_path = base_path / 'bad_swings'
    test_output_path = base_path / 'test_videos'
    
    # Check if directories exist
    if not good_swings_path.exists():
        print(f"❌ Good swings directory not found: {good_swings_path}")
        return
    if not bad_swings_path.exists():
        print(f"❌ Bad swings directory not found: {bad_swings_path}")
        return
    
    # Prepare split: reserve 2 good and 3 bad videos for testing
    split = prepare_train_test_split(
        good_swings_path=good_swings_path,
        bad_swings_path=bad_swings_path,
        test_output_path=test_output_path,
        num_test_good=2,  # Reserve 2 good swings for testing
        num_test_bad=3,   # Reserve 3 bad swings for testing
        seed=42
    )
    
    print("\n" + "=" * 70)
    print("✅ Train/Test Split Complete")
    print("=" * 70)
    print("\n🚀 Next Steps:")
    print("   1. Run dataset creation: python training/create_caddieset_dataset_split.py")
    print("   2. Train models: python training/train_pytorch_models.py")


if __name__ == '__main__':
    main()
