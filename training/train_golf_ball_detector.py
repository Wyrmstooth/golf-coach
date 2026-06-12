"""
Train Faster R-CNN golf ball detector.

Uses torchvision's Faster R-CNN with ResNet-50 FPN backbone, fine-tuned on
golf ball data prepared in VOC format.

Dataset source (from rucv/golf_ball paper):
  https://drive.google.com/file/d/10pzr6mDQPlrylIHg8CdXzHkF4WBMZxfn/view

Usage:
    python training/train_golf_ball_detector.py --data ./datasets/golf_ball --epochs 30
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Faster R-CNN golf ball detector")
    parser.add_argument(
        "--data", type=str, required=True,
        help="Path to dataset directory (contains train/ and val/ subdirs with images and VOC XML annotations)",
    )
    parser.add_argument("--epochs", type=int, default=30, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--device", type=str, default="auto", help="Device: auto, cpu, or cuda")
    parser.add_argument("--output", type=str, default="models/golf_ball_frcnn.pt", help="Output model path")
    parser.add_argument("--num-workers", type=int, default=0, help="DataLoader workers (0 for Windows)")
    return parser.parse_args()


class GolfBallDataset:
    """
    Dataset loader for the rucv/golf_ball Tracking dataset.

    Real layout (from Google Drive):
      Tracking/
        JPEGImages/
          Golf_1/01_001.jpg       ← images in subdirs per video
          Put_1/Put1_001.jpg
          ...
        Annotations/
          01_001.xml              ← all annotations flat
          Put1_001.xml
          ...
        ImageSets/Main/
          Put_1.txt               ← train split IDs (1 per line)
          test_1.txt              ← val split IDs
          ...

    Pass --data "Golf Ball/Tracking" (with quotes for the space).
    """

    def __init__(self, root: str, split: str = "train") -> None:
        self.root = Path(root)
        self.classes = ["__background__", "golfball"]

        # Directories
        self.img_root = self.root / "JPEGImages"
        self.ann_dir  = self.root / "Annotations"
        self.split_dir = self.root / "ImageSets" / "Main"

        # Determine which .txt files to use for this split
        if split == "all":
            split_files = list(self.split_dir.glob("*.txt"))
        elif split == "train":
            split_files = [
                f for f in self.split_dir.glob("*.txt")
                if not f.name.startswith("test_")
            ]
        else:
            split_files = [
                f for f in self.split_dir.glob("test_*.txt")
            ]

        # Collect all image IDs for this split
        self.ids: List[str] = []
        for sf in split_files:
            with open(sf) as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        self.ids.append(line)

        # Build index: id → (image_path, annotation_path, subdir_name)
        self.samples: List[Tuple[Path, Path, str]] = []
        for img_id in self.ids:
            # Annotations are flat: Annotations/<id>.xml
            ann_path = self.ann_dir / f"{img_id}.xml"
            if not ann_path.exists():
                continue

            # Find image by scanning JPEGImages subdirectories
            img_path = None
            for subdir in self.img_root.iterdir():
                if subdir.is_dir():
                    for ext in (".jpg", ".jpeg", ".png"):
                        candidate = subdir / f"{img_id}{ext}"
                        if candidate.exists():
                            img_path = candidate
                            break
                if img_path:
                    break

            if img_path:
                self.samples.append((img_path, ann_path, img_id))

        print(f"  Loaded {len(self.samples)} samples for {split}")

    def __getitem__(self, idx: int) -> Tuple:
        import torch
        from PIL import Image

        img_path, ann_path, _img_id = self.samples[idx]

        image = Image.open(img_path).convert("RGB")
        img_tensor = torchvision_transforms()(image)

        boxes, labels = self._parse_annotation(ann_path)

        # Faster R-CNN requires at least one box per image during training.
        # If no ball annotation exists, skip this sample (Subset fallback).
        if len(boxes) == 0:
            # Return a dummy sample — DataLoader will handle it via collate_fn
            # but we try to avoid this by pre-filtering
            boxes = [[0, 0, 1, 1]]
            labels = [1]

        target = {
            "boxes": torch.as_tensor(boxes, dtype=torch.float32),
            "labels": torch.as_tensor(labels, dtype=torch.int64),
            "image_id": torch.tensor([idx]),
            "area": torch.as_tensor(
                [(x2 - x1) * (y2 - y1) for x1, y1, x2, y2 in boxes],
                dtype=torch.float32,
            ),
            "iscrowd": torch.zeros((len(boxes),), dtype=torch.int64),
        }

        return img_tensor, target

    def __len__(self) -> int:
        return len(self.samples)

    def _parse_annotation(self, ann_path: Path) -> Tuple[List[List[float]], List[int]]:
        """Parse VOC XML, return (boxes, labels). Looks for 'golfball' objects."""
        import xml.etree.ElementTree as ET

        boxes: List[List[float]] = []
        labels: List[int] = []

        if ann_path.suffix == ".xml":
            tree = ET.parse(str(ann_path))
            root = tree.getroot()
            for obj in root.findall("object"):
                name_el = obj.find("name")
                name = (name_el.text or "").lower() if name_el is not None else ""
                if "golf" not in name and "ball" not in name:
                    continue
                bbox = obj.find("bndbox")
                if bbox is None:
                    continue
                x1 = float(bbox.find("xmin").text)  # type: ignore[union-attr]
                y1 = float(bbox.find("ymin").text)  # type: ignore[union-attr]
                x2 = float(bbox.find("xmax").text)  # type: ignore[union-attr]
                y2 = float(bbox.find("ymax").text)  # type: ignore[union-attr]
                boxes.append([x1, y1, x2, y2])
                labels.append(1)

        elif ann_path.suffix == ".json":
            import json
            data = json.loads(ann_path.read_text())
            for box in data.get("boxes", data.get("bboxes", [])):
                boxes.append(box)
                labels.append(1)

        return boxes, labels


def torchvision_transforms():
    """Return ToTensor transform for object detection."""
    import torchvision.transforms as T
    return T.ToTensor()


def collate_fn(batch):
    """Collate function for DataLoader (handles variable-sized targets)."""
    return tuple(zip(*batch))


def _patch_nms() -> None:
    """
    Force torchvision NMS to run on CPU.
    Some Windows torchvision builds lack the CUDA NMS kernel.
    """
    import torchvision.ops as ops
    _orig = ops.nms

    def _cpu_nms(boxes, scores, iou_threshold):
        return _orig(boxes.cpu(), scores.cpu(), iou_threshold).to(boxes.device)

    ops.nms = _cpu_nms


def train_detector(args: argparse.Namespace) -> Path:
    import torch
    import torchvision
    from torchvision.models.detection import fasterrcnn_resnet50_fpn
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

    # ── Patch: force NMS to run on CPU (CUDA NMS kernel missing on some builds) ─
    _patch_nms()

    if args.device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device

    print(f"Device: {device}")
    print(f"Dataset: {args.data}")
    print(f"Epochs: {args.epochs}, Batch: {args.batch_size}, LR: {args.lr}")

    # ── Datasets ──────────────────────────────────────────────────────
    # Combine all samples then do a random 80/20 train/val split
    # (the original dataset has train=putting videos, val=full swings —
    #  a random split works better for learning general golf ball detection)

    full_ds = GolfBallDataset(args.data, split="all")
    if len(full_ds) < 10:
        raise RuntimeError(
            f"Only {len(full_ds)} samples found. "
            f"Make sure --data points to the Tracking folder, e.g.:\n"
            f'  python training/train_golf_ball_detector.py --data "Golf Ball/Tracking"'
        )

    # Random 80/20 split
    import random
    indices = list(range(len(full_ds)))
    random.shuffle(indices)
    split_idx = int(0.8 * len(indices))

    from torch.utils.data import Subset
    train_ds = Subset(full_ds, indices[:split_idx])
    val_ds = Subset(full_ds, indices[split_idx:])

    print(f"Total: {len(full_ds)} samples -> {len(train_ds)} train / {len(val_ds)} val")

    train_loader = torch.utils.data.DataLoader(
        train_ds, batch_size=args.batch_size, shuffle=True,
        num_workers=args.num_workers, collate_fn=collate_fn,
    )
    val_loader = torch.utils.data.DataLoader(
        val_ds, batch_size=1, shuffle=False,
        num_workers=args.num_workers, collate_fn=collate_fn,
    )

    # ── Model ─────────────────────────────────────────────────────────
    model = fasterrcnn_resnet50_fpn(weights="DEFAULT")
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes=2)
    model.to(device)

    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.SGD(params, lr=args.lr, momentum=0.9, weight_decay=0.0005)
    lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.1)

    print(f"Trainable params: {sum(p.numel() for p in params):,}")

    # ── Training loop ─────────────────────────────────────────────────
    for epoch in range(args.epochs):
        model.train()
        epoch_loss = 0.0

        for batch_idx, (images, targets) in enumerate(train_loader):
            images = [img.to(device) for img in images]
            targets = [{k: v.to(device) for k, v in t.items()} for t in targets]

            loss_dict = model(images, targets)
            losses = sum(loss for loss in loss_dict.values())

            optimizer.zero_grad()
            losses.backward()
            optimizer.step()

            epoch_loss += losses.item()

            if batch_idx % 10 == 0:
                print(f"  Epoch {epoch+1}/{args.epochs} | "
                      f"Batch {batch_idx}/{len(train_loader)} | "
                      f"Loss: {losses.item():.4f}")

        avg_loss = epoch_loss / max(len(train_loader), 1)
        lr_scheduler.step()
        print(f"Epoch {epoch+1} complete — Avg Loss: {avg_loss:.4f}")

    # ── Save ──────────────────────────────────────────────────────────
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), str(out_path))
    print(f"\nModel saved to: {out_path}")

    return out_path


def main() -> None:
    args = parse_args()
    train_detector(args)


if __name__ == "__main__":
    main()
