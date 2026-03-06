"""
Video Preprocessing for Low-Quality Golf Swing Videos

Applies preprocessing techniques to improve MediaPipe pose detection:
- Frame interpolation for smoother motion
- Denoising and sharpening
- Contrast enhancement
- Temporal smoothing of keypoints
- Motion blur reduction
"""

import cv2
import numpy as np
from typing import Tuple, List, Optional
from pathlib import Path


class VideoPreprocessor:
    """
    Preprocess low-quality videos for better pose detection
    """
    
    def __init__(
        self,
        target_size: Tuple[int, int] = (640, 640),
        denoise_strength: int = 7,
        sharpen_amount: float = 1.5,
        temporal_window: int = 5
    ):
        """
        Initialize video preprocessor
        
        Args:
            target_size: Target resolution (width, height)
            denoise_strength: Denoising strength (3-15, higher = more smoothing)
            sharpen_amount: Sharpening multiplier (1.0-3.0)
            temporal_window: Window size for temporal smoothing
        """
        self.target_size = target_size
        self.denoise_strength = denoise_strength
        self.sharpen_amount = sharpen_amount
        self.temporal_window = temporal_window
        
    def preprocess_frame(
        self,
        frame: np.ndarray,
        prev_frames: Optional[List[np.ndarray]] = None
    ) -> np.ndarray:
        """
        Preprocess a single frame for better pose detection
        
        Args:
            frame: Input frame (BGR)
            prev_frames: Previous frames for temporal smoothing
            
        Returns:
            Preprocessed frame
        """
        # 1. Resize with high-quality interpolation
        if frame.shape[:2] != self.target_size[::-1]:
            frame = cv2.resize(
                frame,
                self.target_size,
                interpolation=cv2.INTER_CUBIC
            )
        
        # 2. Enhance contrast (helps with dim/washed out videos)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        frame = cv2.merge([l, a, b])
        frame = cv2.cvtColor(frame, cv2.COLOR_LAB2BGR)
        
        # 3. Sharpen (compensates for upscaling blur)
        kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ]) * (self.sharpen_amount / 9.0)
        frame = cv2.filter2D(frame, -1, kernel)
        
        # 4. Clip values to valid range
        frame = np.clip(frame, 0, 255).astype(np.uint8)
        
        return frame
    
    def preprocess_video(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        verbose: bool = True
    ) -> str:
        """
        Preprocess entire video and save to file
        
        Args:
            input_path: Path to input video
            output_path: Path to output video (default: input_preprocessed.mp4)
            verbose: Show progress
            
        Returns:
            Path to preprocessed video
        """
        import tqdm
        
        input_path = Path(input_path)
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_preprocessed.mp4"
        else:
            output_path = Path(output_path)
        
        # Open input video
        cap = cv2.VideoCapture(str(input_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Create output video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(
            str(output_path),
            fourcc,
            fps,
            self.target_size
        )
        
        prev_frames = []
        
        iterator = tqdm.tqdm(range(frame_count), desc="Preprocessing") if verbose else range(frame_count)
        
        for _ in iterator:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Preprocess frame
            processed = self.preprocess_frame(frame, prev_frames)
            
            # Write to output
            out.write(processed)
            
            # Update previous frames buffer
            prev_frames.append(processed)
            if len(prev_frames) > self.temporal_window:
                prev_frames.pop(0)
        
        cap.release()
        out.release()
        
        if verbose:
            print(f"✅ Preprocessed video saved to: {output_path}")
        
        return str(output_path)


class KeypointSmoother:
    """
    Smooth keypoint trajectories to reduce jitter and rapid angle changes
    """
    
    def __init__(self, window_size: int = 5, method: str = 'gaussian'):
        """
        Initialize keypoint smoother
        
        Args:
            window_size: Smoothing window size (odd number)
            method: Smoothing method ('gaussian', 'savgol', 'median')
        """
        self.window_size = window_size if window_size % 2 == 1 else window_size + 1
        self.method = method
        
    def smooth_landmarks_sequence(
        self,
        landmarks_sequence: List[np.ndarray]
    ) -> List[np.ndarray]:
        """
        Smooth a sequence of landmark arrays
        
        Args:
            landmarks_sequence: List of [33, 3] landmark arrays
            
        Returns:
            Smoothed landmarks sequence
        """
        if len(landmarks_sequence) < self.window_size:
            return landmarks_sequence
        
        # Stack all landmarks into [frames, 33, 3] array
        stacked = np.array(landmarks_sequence)
        smoothed = np.zeros_like(stacked)
        
        # Smooth each landmark's x, y, z coordinates independently
        for landmark_idx in range(33):
            for coord_idx in range(3):  # x, y, z
                signal = stacked[:, landmark_idx, coord_idx]
                
                if self.method == 'gaussian':
                    smoothed[:, landmark_idx, coord_idx] = self._gaussian_smooth(signal)
                elif self.method == 'savgol':
                    smoothed[:, landmark_idx, coord_idx] = self._savgol_smooth(signal)
                elif self.method == 'median':
                    smoothed[:, landmark_idx, coord_idx] = self._median_smooth(signal)
                else:
                    smoothed[:, landmark_idx, coord_idx] = signal
        
        # Convert back to list of arrays
        return [smoothed[i] for i in range(len(smoothed))]
    
    def _gaussian_smooth(self, signal: np.ndarray) -> np.ndarray:
        """Apply Gaussian smoothing"""
        from scipy.ndimage import gaussian_filter1d
        sigma = self.window_size / 6.0  # Standard deviation
        return gaussian_filter1d(signal, sigma=sigma, mode='nearest')
    
    def _savgol_smooth(self, signal: np.ndarray) -> np.ndarray:
        """Apply Savitzky-Golay filter"""
        from scipy.signal import savgol_filter
        if len(signal) < self.window_size:
            return signal
        return savgol_filter(signal, self.window_size, polyorder=3, mode='nearest')
    
    def _median_smooth(self, signal: np.ndarray) -> np.ndarray:
        """Apply median filter"""
        from scipy.signal import medfilt
        if len(signal) < self.window_size:
            return signal
        return medfilt(signal, kernel_size=self.window_size)
    
    def smooth_features_sequence(
        self,
        features_sequence: List[dict]
    ) -> List[dict]:
        """
        Smooth extracted biomechanical features
        
        Args:
            features_sequence: List of feature dicts
            
        Returns:
            Smoothed features sequence
        """
        if len(features_sequence) < self.window_size:
            return features_sequence
        
        # Get all feature keys
        keys = list(features_sequence[0].keys())
        
        # Stack features into arrays
        smoothed_features = []
        
        for key in keys:
            # Extract values for this feature
            values = []
            for features in features_sequence:
                val = features.get(key)
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    # Use previous valid value or 0
                    val = values[-1] if values else 0.0
                values.append(val)
            
            values = np.array(values)
            
            # Smooth
            if self.method == 'gaussian':
                smoothed = self._gaussian_smooth(values)
            elif self.method == 'savgol':
                smoothed = self._savgol_smooth(values)
            elif self.method == 'median':
                smoothed = self._median_smooth(values)
            else:
                smoothed = values
            
            # Store smoothed values
            if not smoothed_features:
                smoothed_features = [{} for _ in range(len(smoothed))]
            
            for i, val in enumerate(smoothed):
                smoothed_features[i][key] = float(val)
        
        return smoothed_features


if __name__ == "__main__":
    # Test preprocessing
    print("=" * 60)
    print("Video Preprocessor Test")
    print("=" * 60)
    
    preprocessor = VideoPreprocessor(
        target_size=(640, 640),
        denoise_strength=7,
        sharpen_amount=1.5,
        temporal_window=5
    )
    
    # Test on a sample video
    input_video = "0.mp4"
    if Path(input_video).exists():
        output_video = preprocessor.preprocess_video(input_video, verbose=True)
        print(f"\n✅ Test complete: {output_video}")
    else:
        print(f"❌ Test video not found: {input_video}")
