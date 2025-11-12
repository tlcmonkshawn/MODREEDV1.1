"""Video capture and frame processing for Live API."""
import cv2
import numpy as np
from typing import Optional, Callable
import config
import asyncio


class VideoCapture:
    """Handles video capture from camera and frame processing."""
    
    def __init__(self, camera_index: int = 0):
        """Initialize video capture.
        
        Args:
            camera_index: Camera device index (0 for default)
        """
        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_capturing = False
        self.current_frame: Optional[np.ndarray] = None
        self.is_paused = False
        self.paused_frame: Optional[np.ndarray] = None
        
        # Callback for frame updates
        self.on_frame: Optional[Callable] = None
        
    def start(self):
        """Start video capture."""
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera {self.camera_index}")
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.VIDEO_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.VIDEO_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, config.VIDEO_FPS)
        
        self.is_capturing = True
        asyncio.create_task(self._capture_loop())
    
    def stop(self):
        """Stop video capture."""
        self.is_capturing = False
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def flip_camera(self):
        """Switch between front and rear cameras."""
        # This is a simplified implementation
        # In a real app, you'd need to handle multiple camera indices
        self.stop()
        self.camera_index = 1 - self.camera_index
        self.start()
    
    def pause(self):
        """Pause video capture and freeze current frame."""
        self.is_paused = True
        if self.current_frame is not None:
            self.paused_frame = self.current_frame.copy()
    
    def resume(self):
        """Resume video capture."""
        self.is_paused = False
        self.paused_frame = None
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the current frame (paused or live).
        
        Returns:
            Current video frame as numpy array, or None if not available
        """
        if self.is_paused and self.paused_frame is not None:
            return self.paused_frame
        return self.current_frame
    
    def capture_snapshot(self) -> Optional[bytes]:
        """Capture a snapshot of the current frame.
        
        Returns:
            JPEG-encoded image bytes, or None if no frame available
        """
        frame = self.get_current_frame()
        if frame is None:
            return None
        
        # Resize to required resolution if needed
        if frame.shape[1] != config.VIDEO_WIDTH or frame.shape[0] != config.VIDEO_HEIGHT:
            frame = cv2.resize(frame, (config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
        
        # Encode as JPEG
        success, encoded_image = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if success:
            return encoded_image.tobytes()
        return None
    
    async def _capture_loop(self):
        """Internal loop for capturing frames."""
        frame_interval = 1.0 / config.VIDEO_FPS  # 1 second for 1 FPS
        
        while self.is_capturing:
            if not self.is_paused:
                ret, frame = self.cap.read()
                if ret:
                    # Convert BGR to RGB for web display
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.current_frame = frame_rgb
                    
                    if self.on_frame:
                        self.on_frame(frame_rgb)
            
            await asyncio.sleep(frame_interval)

