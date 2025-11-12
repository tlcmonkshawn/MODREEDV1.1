"""Audio input/output handling for Live API."""
import pyaudio
import numpy as np
import asyncio
from typing import Optional, Callable
import config


class AudioHandler:
    """Handles audio input and output for Live API."""
    
    def __init__(self):
        """Initialize audio handler."""
        self.pyaudio_instance = pyaudio.PyAudio()
        self.input_stream: Optional[pyaudio.Stream] = None
        self.output_stream: Optional[pyaudio.Stream] = None
        self.is_recording = False
        self.is_playing = False
        self.is_muted = False
        
        # Callbacks
        self.on_audio_input: Optional[Callable] = None
        
    def start_input(self):
        """Start audio input stream."""
        if self.input_stream:
            return
        
        self.input_stream = self.pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=config.AUDIO_CHANNELS,
            rate=config.AUDIO_INPUT_RATE,
            input=True,
            frames_per_buffer=config.AUDIO_CHUNK_SIZE
        )
        self.is_recording = True
        asyncio.create_task(self._input_loop())
    
    def stop_input(self):
        """Stop audio input stream."""
        self.is_recording = False
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
            self.input_stream = None
    
    def start_output(self):
        """Start audio output stream."""
        if self.output_stream:
            return
        
        self.output_stream = self.pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=config.AUDIO_CHANNELS,
            rate=config.AUDIO_OUTPUT_RATE,
            output=True,
            frames_per_buffer=config.AUDIO_CHUNK_SIZE
        )
        self.is_playing = True
    
    def stop_output(self):
        """Stop audio output stream."""
        self.is_playing = False
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
            self.output_stream = None
    
    def mute(self):
        """Mute audio input."""
        self.is_muted = True
    
    def unmute(self):
        """Unmute audio input."""
        self.is_muted = False
    
    def play_audio(self, audio_data: bytes):
        """Play audio data through output stream.
        
        Args:
            audio_data: Raw PCM audio bytes (24kHz, 16-bit, little-endian)
        """
        if self.output_stream and self.is_playing:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            self.output_stream.write(audio_array.tobytes())
    
    async def _input_loop(self):
        """Internal loop for capturing audio input."""
        while self.is_recording:
            if self.input_stream and not self.is_muted:
                try:
                    audio_data = self.input_stream.read(
                        config.AUDIO_CHUNK_SIZE,
                        exception_on_overflow=False
                    )
                    if self.on_audio_input:
                        self.on_audio_input(audio_data)
                except Exception as e:
                    print(f"Error reading audio: {e}")
            await asyncio.sleep(0.01)  # Small delay to prevent busy waiting
    
    def cleanup(self):
        """Clean up audio resources."""
        self.stop_input()
        self.stop_output()
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()

