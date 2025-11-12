"""Live API WebSocket client for video and audio streaming."""
import asyncio
import base64
import json
from typing import Optional, Callable, Dict, Any
from google import genai
from google.genai import types
import config


class LiveAPIClient:
    """Client for managing Live API WebSocket connections."""
    
    def __init__(self, project: str, location: str):
        """Initialize the Live API client.
        
        Args:
            project: Google Cloud project ID
            location: Google Cloud location (e.g., 'us-central1')
        """
        self.client = genai.Client(
            vertexai=True,
            project=project,
            location=location,
        )
        self.session: Optional[Any] = None
        self.model = config.MODEL_ID
        self.is_connected = False
        self.is_speaking = False
        self.is_listening = False
        
        # Callbacks
        self.on_audio_received: Optional[Callable] = None
        self.on_text_received: Optional[Callable] = None
        self.on_transcription: Optional[Callable] = None
        self.on_tool_call: Optional[Callable] = None
        self.on_state_change: Optional[Callable] = None
        
    async def connect(self, tools: Optional[list] = None, system_instruction: Optional[str] = None):
        """Connect to the Live API session.
        
        Args:
            tools: List of function calling tools
            system_instruction: System instruction for the model
        """
        config_obj = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO, types.Modality.TEXT],
            input_audio_transcription={},
            output_audio_transcription={},
        )
        
        if tools:
            config_obj.tools = tools
            
        if system_instruction:
            config_obj.system_instruction = system_instruction
        
        self.session = await self.client.aio.live.connect(
            model=self.model,
            config=config_obj
        )
        self.is_connected = True
        
        if self.on_state_change:
            self.on_state_change("connected")
        
        # Start receiving messages
        asyncio.create_task(self._receive_messages())
    
    async def disconnect(self):
        """Disconnect from the Live API session."""
        if self.session:
            await self.session.close()
            self.is_connected = False
            if self.on_state_change:
                self.on_state_change("disconnected")
    
    async def send_audio(self, audio_data: bytes):
        """Send audio data to the Live API.
        
        Args:
            audio_data: Raw PCM audio bytes (16kHz, 16-bit, little-endian)
        """
        if not self.session or not self.is_connected:
            return
        
        if not self.is_listening:
            self.is_listening = True
            if self.on_state_change:
                self.on_state_change("listening")
        
        try:
            await self.session.send(
                input={
                    "data": audio_data,
                    "mime_type": "audio/pcm"
                }
            )
        except Exception as e:
            print(f"Error sending audio: {e}")
    
    async def send_video_frame(self, frame_data: bytes, mime_type: str = "image/jpeg"):
        """Send a video frame to the Live API.
        
        Args:
            frame_data: Image frame data (JPEG/PNG bytes)
            mime_type: MIME type of the frame (image/jpeg or image/png)
        """
        if not self.session or not self.is_connected:
            return
        
        try:
            await self.session.send(
                input={
                    "data": frame_data,
                    "mime_type": mime_type
                }
            )
        except Exception as e:
            print(f"Error sending video frame: {e}")
    
    async def send_text(self, text: str):
        """Send text message to the Live API.
        
        Args:
            text: Text message to send
        """
        if not self.session or not self.is_connected:
            return
        
        try:
            await self.session.send_client_content(
                turns=types.Content(
                    role="user",
                    parts=[types.Part(text=text)]
                )
            )
        except Exception as e:
            print(f"Error sending text: {e}")
    
    async def _receive_messages(self):
        """Receive and process messages from the Live API."""
        if not self.session:
            return
        
        try:
            async for message in self.session.receive():
                # Handle server content
                if hasattr(message, 'server_content') and message.server_content:
                    sc = message.server_content
                    
                    # Handle input transcription
                    if hasattr(sc, 'input_transcription') and sc.input_transcription:
                        if self.on_transcription:
                            self.on_transcription(sc.input_transcription, "input")
                    
                    # Handle output transcription
                    if hasattr(sc, 'output_transcription') and sc.output_transcription:
                        if self.on_transcription:
                            self.on_transcription(sc.output_transcription, "output")
                    
                    # Handle model turn (audio/text output)
                    if hasattr(sc, 'model_turn') and sc.model_turn:
                        if hasattr(sc.model_turn, 'parts') and sc.model_turn.parts:
                            for part in sc.model_turn.parts:
                                # Handle audio
                                if hasattr(part, 'inline_data') and part.inline_data:
                                    if part.inline_data.mime_type == "audio/pcm":
                                        if not self.is_speaking:
                                            self.is_speaking = True
                                            self.is_listening = False
                                            if self.on_state_change:
                                                self.on_state_change("speaking")
                                        
                                        if self.on_audio_received:
                                            self.on_audio_received(part.inline_data.data)
                                
                                # Handle text
                                if hasattr(part, 'text') and part.text:
                                    if self.on_text_received:
                                        self.on_text_received(part.text)
                    
                    # Check if generation is complete
                    if hasattr(sc, 'generation_complete') and sc.generation_complete:
                        self.is_speaking = False
                        if self.on_state_change:
                            self.on_state_change("idle")
                
                # Handle tool calls
                if hasattr(message, 'tool_call') and message.tool_call:
                    if self.on_tool_call:
                        self.on_tool_call(message.tool_call)
                        
        except Exception as e:
            print(f"Error receiving messages: {e}")
            self.is_connected = False
            if self.on_state_change:
                self.on_state_change("error")

