# Live API Video-Aware Call Application

A video-aware 2-way call application using Gemini 2.5 Flash Live API with snapshot capture, image management, and animated Reed orb interface.

## Features

- **Video-Aware 2-Way Call**: Real-time bidirectional video and audio communication with Gemini
- **Snapshot Capture**: Tool call-based snapshot functionality that pauses video stream and captures frames
- **Image Management**: Automatic storage of captured images with metadata (name, category, state)
- **Reed Orb Animation**: Animated orb that glows/wiggles when speaking and flashes when listening
- **Item Drawer**: Landscape mode shows captured items in a drawer, portrait mode shows alerts
- **Bootie Viewer**: Secondary interface with video display, Reed profile, and item details

## Requirements

- Python 3.9+
- Google Cloud Project with Vertex AI enabled
- Camera and microphone access
- PortAudio (for audio on Linux/Mac)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <project-directory>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install PortAudio (Linux):
```bash
sudo apt-get install portaudio19-dev
```

4. Install PortAudio (Mac):
```bash
brew install portaudio
```

5. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Google Cloud credentials
```

6. Set up Google Cloud credentials:
- Create a service account in Google Cloud Console
- Download the JSON key file
- Set `GOOGLE_APPLICATION_CREDENTIALS` in `.env` to the path of the key file

## Configuration

Edit `.env` file with your settings:

- `GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID
- `GOOGLE_CLOUD_LOCATION`: Location (default: us-central1)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON key
- `FLASK_HOST`: Flask server host (default: 127.0.0.1)
- `FLASK_PORT`: Flask server port (default: 5000)
- `DATABASE_URL`: Database URL (default: sqlite:///images.db)
- `IMAGE_STORAGE_DIR`: Directory for storing images (default: static/images)

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Click "Start Session" to begin the video call

4. Use the controls:
- **FLIP**: Switch between front and rear cameras
- **SNAP**: Capture a snapshot (pauses video, captures frame)
- **MUTE**: Mute/unmute audio input

## Project Structure

```
.
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── live_api_client.py     # Live API WebSocket client
├── video_capture.py       # Video capture and processing
├── audio_handler.py       # Audio input/output handling
├── snapshot_tool.py       # Snapshot function calling tool
├── image_manager.py       # Image storage and management
├── templates/
│   └── index.html        # Main UI template
├── static/
│   ├── css/
│   │   └── style.css     # Styles
│   ├── js/
│   │   ├── app.js        # Main application logic
│   │   └── reed-orb.js   # Reed orb animation
│   └── images/           # Stored images
└── requirements.txt       # Python dependencies
```

## How It Works

1. **Video Streaming**: Video frames are captured at 1 FPS (768x768) and sent to Live API
2. **Audio Streaming**: Audio is captured at 16kHz and sent to Live API, responses played at 24kHz
3. **Snapshot Capture**: When snapshot is triggered (via button or tool call):
   - Video stream is paused
   - Current frame is captured
   - Image is stored immediately in database
   - Item appears in drawer (landscape) or alert (portrait)
   - Video resumes after capture
4. **Reed Orb**: Animates based on audio state:
   - **Speaking**: Glows and wiggles
   - **Listening**: Flashes
   - **Idle**: Static

## API Endpoints

- `GET /` - Main application page
- `GET /api/health` - Health check
- `POST /api/snapshot` - Capture snapshot
- `GET /api/items` - Get captured items
- `PUT /api/items/<id>` - Update item metadata
- `POST /api/session/start` - Start Live API session
- `POST /api/session/stop` - Stop Live API session

## Notes

- Video is processed at 1 FPS by Live API (as per API requirements)
- Images are stored immediately upon capture (no preview required)
- Post-processing (naming, categorization) happens after storage
- The app automatically detects portrait vs landscape mode for UI adaptation

## License

[Your License Here]

