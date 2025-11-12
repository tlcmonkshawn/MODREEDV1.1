"""Configuration settings for the Live API application."""
import os
from dotenv import load_dotenv

load_dotenv()

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT', '')
GOOGLE_CLOUD_LOCATION = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')

# Live API Model Configuration
MODEL_ID = 'gemini-live-2.5-flash-preview-native-audio-09-2025'

# Audio Configuration
AUDIO_INPUT_RATE = 16000  # 16kHz PCM input
AUDIO_OUTPUT_RATE = 24000  # 24kHz PCM output
AUDIO_CHUNK_SIZE = 4200
AUDIO_CHANNELS = 1
AUDIO_FORMAT = 'pcm'  # 16-bit PCM, little-endian

# Video Configuration
VIDEO_FPS = 1  # Live API processes at 1 frame per second
VIDEO_WIDTH = 768
VIDEO_HEIGHT = 768

# Flask Configuration
FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///images.db')

# Image Storage
IMAGE_STORAGE_DIR = os.getenv('IMAGE_STORAGE_DIR', 'static/images')
IMAGE_MAX_SIZE_MB = 7

# Session Configuration
MAX_SESSION_DURATION_MINUTES = 10