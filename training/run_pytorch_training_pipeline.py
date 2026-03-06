#!/usr/bin/env python3
"""
Complete Golf Coach Training Pipeline with PyTorch + CUDA

This script runs the complete training workflow:
1. Prepares train/test split (reserves 4-5 videos for testing)
2. Creates CaddieSet-compatible dataset from training videos only
3. Trains swing quality classifier with PyTorch (CUDA accelerated)
4. Trains performance predictor with PyTorch

Usage:
    python training/run_pytorch_training_pipeline.py
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import subprocess
import torch


def check_cuda():
    """Check CUDA availability and print GPU info"""
    print("\n" + "=" * 70)
    print("🖥️  CUDA/GPU Status")
    print("=" * 70)
    
    if torch.cuda.is_available():
        print(f"✅ CUDA is available!")
        print(f"   Device: {torch.cuda.get_device_name(0)}")
        print(f"   CUDA Version: {torch.version.cuda}")
        print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        return True
    else:
        print("⚠️  CUDA is NOT available. Training will use CPU (slower)")
        return False


def run_step(script_name: str, step_num: int, description: str) -> bool:
    """Run a training step and return success status"""
    print("\n" + "=" * 70)
    print(f"STEP {step_num}: {description}")
    print("=" * 70)
    
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(Path(__file__).parent.parent),
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Step failed with error code: {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Error running step: {e}")
        return False


def main():
    print("=" * 70)
    print("🏌️ GOLF COACH - PyTorch TRAINING PIPELINE")
    print("=" * 70)
    
    base_path = Path(__file__).parent.parent
    
    # Check CUDA availability
    cuda_available = check_cuda()
    
    # Check for videos
    good_videos = list((base_path / 'good_swings').glob('*.mp4'))
    bad_videos = list((base_path / 'bad_swings').glob('*.mp4'))
    
    print(f"\n📂 Input Summary:")
    print(f"   Good swing videos: {len(good_videos)}")
    print(f"   Bad swing videos: {len(bad_videos)}")
    print(f"   CaddieSet.csv: {'Found' if (base_path / 'CaddieSet.csv').exists() else 'Not found'}")
    
    if not good_videos and not bad_videos:
        print("\n❌ No videos found!")
        print(f"   Please add videos to:")
        print(f"   - {base_path / 'good_swings'}")
        print(f"   - {base_path / 'bad_swings'}")
        return
    
    if not good_videos or not bad_videos:
        print("\n⚠️  Warning: Need both good and bad swing videos for best results")
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Step 1: Prepare train/test split
    print("\n" + "=" * 70)
    print("STEP 1: Preparing Train/Test Split")
    print("=" * 70)
    
    if not run_step('prepare_train_test_split.py', 1, 'Preparing Train/Test Split'):
        print("\n❌ Train/test split failed. Please check errors above.")
        return
    
    # Check test folder was created
    test_path = base_path / 'test_videos'
    if not test_path.exists():
        print(f"\n⚠️  Test videos folder not created (may have too few videos)")
    else:
        test_good = list((test_path / 'good_swings').glob('*.mp4'))
        test_bad = list((test_path / 'bad_swings').glob('*.mp4'))
        print(f"\n✅ Test set created: {len(test_good)} good + {len(test_bad)} bad videos")
    
    # Step 2: Create dataset from training videos only
    print("\n" + "=" * 70)
    print("STEP 2: Creating CaddieSet-Compatible Dataset (Training Videos Only)")
    print("=" * 70)
    
    if not run_step('create_caddieset_dataset_split.py', 2, 'Creating Training Dataset'):
        print("\n❌ Dataset creation failed. Please check errors above.")
        return
    
    # Check dataset was created
    dataset_path = base_path / 'training_data' / 'golf_swings_dataset.csv'
    if not dataset_path.exists():
        print(f"\n❌ Dataset not created at: {dataset_path}")
        return
    
    print(f"\n✅ Dataset created: {dataset_path}")
    
    # Step 3: Train models with PyTorch
    print("\n" + "=" * 70)
    print("STEP 3: Training Golf Swing Models (PyTorch + CUDA)")
    print("=" * 70)
    
    if not run_step('train_pytorch_models.py', 3, 'Training PyTorch Models'):
        print("\n❌ Model training failed. Please check errors above.")
        return
    
    # Check models were created
    models_dir = base_path / 'models'
    classifier_path = models_dir / 'swing_quality_classifier.pt'
    
    if not classifier_path.exists():
        print(f"\n❌ Classifier not saved at: {classifier_path}")
        return
    
    # Print summary
    print("\n" + "=" * 70)
    print("✅ TRAINING PIPELINE COMPLETE")
    print("=" * 70)
    
    print("\n📦 Created Files:")
    print(f"   📊 Training Dataset: {dataset_path}")
    print(f"   🤖 Classifier (PyTorch): {classifier_path}")
    print(f"   🤖 Fault Detector (PyTorch): {models_dir / 'fault_detector.pt'}")
    
    if (models_dir / 'performance_predictor.pt').exists():
        print(f"   🤖 Predictor (PyTorch): {models_dir / 'performance_predictor.pt'}")
    
    print(f"   📝 Training Report: {models_dir / 'training_report.json'}")
    
    if test_path.exists():
        print(f"\n🧪 Test Videos Reserved:")
        print(f"   {test_path}")
    
    print("\n🚀 Next Steps:")
    print("   1. Analyze a test video: python analyze_video.py --video test_videos/good_swings/X.mp4")
    print("   2. Start the web app: python golf_coach_app.py")
    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
