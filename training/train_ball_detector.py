"""
Train YOLOv8 golf ball detector for Module 3.

This script assumes you have prepared a YOLO-format dataset with:
- data.yaml describing train/val paths and the single "ball" class
- images and labels in standard YOLO layout.

Example data.yaml:

    path: ./datasets/golf_ball
    train: images/train
    val: images/val
    names:
      0: ball

Usage (from project root):

    # Basic training with default settings
    python training/train_ball_detector.py --data ./datasets/golf_ball/data.yaml

    # Custom settings
    python training/train_ball_detector.py \\
        --data ./datasets/golf_ball/data.yaml \\
        --model yolov8n.pt \\
        --epochs 80 \\
        --imgsz 640

The best weights are copied to models/ball_detector.pt for use by Module 3.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def train_ball_detector(
    data: str,
    model: str = "yolov8n.pt",
    epochs: int = 50,
    imgsz: int = 640,
    batch: int = 16,
    project: str = "runs/ball_detector",
    name: str = "exp",
) -> Path:
    from ultralytics import YOLO  # type: ignore

    root = Path(__file__).parent.parent
    data_path = Path(data)
    if not data_path.exists():
        raise FileNotFoundError(f"data.yaml not found at {data_path}")

    print("=" * 70)
    print("🏌️ Training YOLOv8 Golf Ball Detector")
    print("=" * 70)
    print(f"Data:   {data_path}")
    print(f"Model:  {model}")
    print(f"Epochs: {epochs}, Image size: {imgsz}, Batch: {batch}")
    print(f"Project: {project}, Name: {name}")
    print()

    yolo = YOLO(model)

    results = yolo.train(
        data=str(data_path),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        project=project,
        name=name,
        verbose=True,
    )

    best_ckpt = Path(results.best)
    if not best_ckpt.exists():
        raise FileNotFoundError(f"Best checkpoint not found at {best_ckpt}")

    # Copy best weights into models/ball_detector.pt
    models_dir = root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    out_path = models_dir / "ball_detector.pt"

    print(f"\n📦 Copying best weights to: {out_path}")
    out_path.write_bytes(best_ckpt.read_bytes())

    print("\n✅ Ball detector training complete")
    print(f"   Saved YOLO run at: {best_ckpt.parent}")
    print(f"   Inference model:   {out_path}")

    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train YOLOv8 golf ball detector")
    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to YOLO data.yaml describing golf ball dataset",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8n.pt",
        help="Base YOLO model (e.g. yolov8n.pt, yolov8s.pt)",
    )
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument(
        "--project",
        type=str,
        default="runs/ball_detector",
        help="Project directory for YOLO runs",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="exp",
        help="Run name (subdirectory inside project)",
    )

    args = parser.parse_args()
    train_ball_detector(
        data=args.data,
        model=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=args.project,
        name=args.name,
    )


if __name__ == "__main__":
    main()

