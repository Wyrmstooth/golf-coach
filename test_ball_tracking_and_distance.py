"""
Basic sanity tests for Module 3: ball tracking & distance estimation.

These tests are lightweight and do not require real videos; they are
intended as developer checks rather than formal unit tests.
"""

from pathlib import Path

from utils.ball_tracker import BallTrajectoryPoint
from utils.distance_estimator import DistanceEstimator
from utils.ball_tracker import BallTracker
from models.ball_detector import BallDetector


def test_distance_estimator_on_synthetic_trajectory():
    # Create a simple synthetic trajectory: ball moves 200 px horizontally
    traj = []
    fps = 30.0
    for i in range(20):
        traj.append(
            BallTrajectoryPoint(
                frame=i,
                t_sec=i / fps,
                x=100 + i * 10,  # 0 → 190 px
                y=200 - i * 2,   # modest upward motion
                confidence=0.9,
            )
        )

    quality = {
        "status": "ok",
        "detection_rate": 1.0,
        "longest_gap_frames": 0.0,
        "num_frames": len(traj),
    }

    estimator = DistanceEstimator(pixel_to_meter=0.02)
    result = estimator.estimate(traj, quality_metrics=quality)

    assert result is not None
    print("Synthetic distance estimate:", result)


def test_ball_tracker_handles_missing_video():
    tracker = BallTracker()
    detector = BallDetector(model_path="models/ball_detector.pt")

    traj, quality = tracker.track(
        video_path="non_existent_video.mp4",
        impact_range=(10, 12),
        fps=30.0,
        detector=detector,
    )

    assert traj == []
    assert isinstance(quality, dict)
    print("Tracker quality on missing video:", quality)


if __name__ == "__main__":
    print("Running basic Module 3 tests...")
    test_distance_estimator_on_synthetic_trajectory()
    test_ball_tracker_handles_missing_video()
    print("✓ Tests finished")

