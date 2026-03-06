"""
Visualization tools for golf swing analysis
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm
import mediapipe as mp

from utils.ball_tracker import BallTrajectoryPoint


class SwingVisualizer:
    """Create visualizations for golf swing analysis"""
    
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_style = mp.solutions.drawing_styles
    
    def plot_trajectory(
        self,
        frame_data: List[Dict],
        phase_ranges: Dict[str, Tuple[int, int]],
        output_path: Optional[str] = None
    ):
        """
        Plot wrist trajectory with phase annotations
        
        Args:
            frame_data: List of frame data dictionaries
            phase_ranges: Phase ranges dict
            output_path: Path to save plot (if None, displays instead)
        """
        x = np.array([d['frame_idx'] for d in frame_data])
        y = np.array([
            d['wrist_y'] if d['wrist_y'] is not None else np.nan
            for d in frame_data
        ], dtype=np.float32)
        
        # Flip Y axis for intuitive visualization (up = low Y value in image)
        valid_y = y[~np.isnan(y)]
        if len(valid_y) > 0:
            y_flipped = np.max(valid_y) - y + np.min(valid_y)
        else:
            y_flipped = y
        
        plt.figure(figsize=(14, 6))
        plt.plot(x, y_flipped, label='Wrist Y (flipped)', color='black', linewidth=2)
        
        colors = ['gray', 'blue', 'orange', 'green', 'red', 'purple']
        for i, (phase, (start, end)) in enumerate(phase_ranges.items()):
            plt.axvspan(start, end, alpha=0.3, color=colors[i % len(colors)], label=phase)
        
        plt.xlabel("Frame Index", fontsize=12)
        plt.ylabel("Wrist Y (flipped)", fontsize=12)
        plt.title("Golf Swing Wrist Trajectory with Phase Detection", fontsize=14)
        plt.legend(loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150)
            print(f"💾 Saved trajectory plot: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def add_phase_label(
        self,
        frame: np.ndarray,
        phase: str,
        scale: float = 1.0
    ) -> np.ndarray:
        """
        Add phase label to frame
        
        Args:
            frame: Input frame
            phase: Phase name
            scale: Scale factor for text size
        
        Returns:
            Frame with phase label
        """
        height, width = frame.shape[:2]
        label_h = int(35 * scale)
        font_s = 0.4 * scale
        thick = max(1, int(2 * scale))
        
        cv2.rectangle(frame, (3, 3), (width-3, label_h), (0, 0, 0), -1)
        cv2.rectangle(frame, (3, 3), (width-3, label_h), (0, 255, 0), 2)
        cv2.putText(frame, phase, (int(5*scale), int(25*scale)),
                   cv2.FONT_HERSHEY_DUPLEX, font_s, (0, 255, 0), thick)
        
        return frame
    
    def add_angles_overlay(
        self,
        frame: np.ndarray,
        angles: Dict[str, float],
        scale: float = 1.0
    ) -> np.ndarray:
        """
        Add angle measurements to frame
        
        Args:
            frame: Input frame
            angles: Dictionary of angle measurements
            scale: Scale factor for text size
        
        Returns:
            Frame with angle overlays
        """
        height, width = frame.shape[:2]
        y_pos = height - int(45 * scale)
        line_h = int(10 * scale)
        small_f = 0.25 * scale
        small_t = max(1, int(1 * scale))
        
        y_offset = 0
        for angle_name, angle_value in angles.items():
            color = (0, 255, 0) if 'Elbow' in angle_name else (0, 255, 255)
            cv2.putText(frame, f"{angle_name}:{angle_value:.0f}",
                       (3, y_pos + line_h * y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, small_f, color, small_t)
            y_offset += 1
        
        return frame
    
    def add_frame_counter(
        self,
        frame: np.ndarray,
        frame_idx: int,
        scale: float = 1.0
    ) -> np.ndarray:
        """Add frame counter to frame"""
        height, width = frame.shape[:2]
        cv2.putText(frame, f"#{frame_idx}",
                   (width - int(30*scale), height - int(3*scale)),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.25*scale, (150,150,150),
                   max(1, int(1*scale)))
        return frame
    
    def draw_pose_skeleton(
        self,
        frame: np.ndarray,
        pose_landmarks,
        connections: bool = True
    ) -> np.ndarray:
        """
        Draw pose skeleton on frame

        Args:
            frame: Input frame
            pose_landmarks: MediaPipe pose landmarks
            connections: Whether to draw connections

        Returns:
            Frame with pose skeleton
        """
        if pose_landmarks:
            if connections:
                self.mp_drawing.draw_landmarks(
                    frame,
                    pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=self.mp_style.get_default_pose_landmarks_style()
                )
        return frame

    def plot_swing_analysis(
        self,
        wrist_y: np.ndarray,
        smoothed_y: np.ndarray,
        phase_ranges: Dict[str, Tuple[int, int]],
        swing_start: int,
        swing_end: int,
        output_path: str
    ):
        """
        Create comprehensive swing analysis plot

        Args:
            wrist_y: Raw wrist Y positions
            smoothed_y: Smoothed wrist Y positions
            phase_ranges: Dictionary of phase ranges
            swing_start: Start frame of swing
            swing_end: End frame of swing
            output_path: Path to save plot
        """
        fig, ax = plt.subplots(figsize=(14, 6))

        # Create frame indices
        frames = np.arange(len(wrist_y))

        # Flip Y for intuitive visualization (lower values = higher position)
        valid_mask = ~np.isnan(wrist_y)
        if np.any(valid_mask):
            y_max = np.nanmax(wrist_y)
            y_min = np.nanmin(wrist_y)
            wrist_y_flipped = y_max - wrist_y + y_min
            smoothed_y_flipped = y_max - smoothed_y + y_min
        else:
            wrist_y_flipped = wrist_y
            smoothed_y_flipped = smoothed_y

        # Plot trajectories
        ax.plot(frames, wrist_y_flipped, 'lightgray', alpha=0.5, linewidth=1, label='Raw trajectory')
        ax.plot(frames, smoothed_y_flipped, 'black', linewidth=2, label='Smoothed trajectory')

        # Mark swing boundaries
        ax.axvline(swing_start, color='green', linestyle='--', linewidth=2, label='Swing start')
        ax.axvline(swing_end, color='red', linestyle='--', linewidth=2, label='Swing end')

        # Color-code phases
        colors = {
            'ADDRESS': 'gray',
            'BACKSWING': 'blue',
            'TOP': 'orange',
            'DOWNSWING': 'green',
            'IMPACT': 'red',
            'FOLLOW_THROUGH': 'purple'
        }

        for phase, (start, end) in phase_ranges.items():
            color = colors.get(phase, 'lightblue')
            ax.axvspan(start, end, alpha=0.2, color=color, label=phase)

        # Labels and formatting
        ax.set_xlabel('Frame Number', fontsize=12)
        ax.set_ylabel('Wrist Height (pixels, flipped)', fontsize=12)
        ax.set_title('Golf Swing Analysis - Wrist Trajectory & Phase Detection', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left', fontsize=9)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"💾 Saved analysis plot: {output_path}")

    def plot_ball_trajectory(
        self,
        ball_trajectory: List[BallTrajectoryPoint],
        phase_ranges: Dict[str, Tuple[int, int]],
        output_path: str,
    ):
        """
        Plot ball height and horizontal displacement over time with phase spans.
        """
        if not ball_trajectory:
            return

        frames = np.array([pt.frame for pt in ball_trajectory], dtype=np.int32)
        xs = np.array(
            [np.nan if pt.x is None else pt.x for pt in ball_trajectory],
            dtype=np.float32,
        )
        ys = np.array(
            [np.nan if pt.y is None else pt.y for pt in ball_trajectory],
            dtype=np.float32,
        )

        valid_mask = ~np.isnan(xs) & ~np.isnan(ys)
        if not np.any(valid_mask):
            return

        fig, ax = plt.subplots(figsize=(14, 6))

        # Normalize so that start point is at 0
        x0 = xs[valid_mask][0]
        y0 = ys[valid_mask][0]
        dx = xs - x0
        dy = y0 - ys  # flip so upward motion is positive

        ax.plot(frames, dx, label="Horizontal (px)", color="tab:blue", linewidth=2)
        ax2 = ax.twinx()
        ax2.plot(frames, dy, label="Vertical (px)", color="tab:orange", linewidth=2)

        # Phase spans
        colors = {
            "ADDRESS": "gray",
            "BACKSWING": "blue",
            "TOP": "orange",
            "DOWNSWING": "green",
            "IMPACT": "red",
            "FOLLOW_THROUGH": "purple",
        }
        for phase, (start, end) in phase_ranges.items():
            color = colors.get(phase, "lightblue")
            ax.axvspan(start, end, alpha=0.1, color=color)

        ax.set_xlabel("Frame Number", fontsize=12)
        ax.set_ylabel("Horizontal Displacement (px)", fontsize=12)
        ax2.set_ylabel("Vertical Displacement (px, up positive)", fontsize=12)
        ax.set_title(
            "Ball Trajectory - Horizontal & Vertical Displacement",
            fontsize=14,
            fontweight="bold",
        )
        ax.grid(True, alpha=0.3)

        # Combined legend
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines + lines2, labels + labels2, loc="upper left", fontsize=9)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        print(f"💾 Saved ball trajectory plot: {output_path}")
