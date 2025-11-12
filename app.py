"""Main Flask application for the Live API video-aware call app."""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import asyncio
import base64
from datetime import datetime

from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, IMAGE_STORAGE_DIR
from live_api_client import LiveAPIClient
from video_capture import VideoCapture
from audio_handler import AudioHandler
from snapshot_tool import create_snapshot_tool, handle_snapshot_tool_call
from image_manager import ImageManager

app = Flask(__name__)
CORS(app)

# Ensure image storage directory exists
os.makedirs(IMAGE_STORAGE_DIR, exist_ok=True)
os.makedirs('static', exist_ok=True)

# Global instances
live_client: LiveAPIClient = None
video_capture: VideoCapture = None
audio_handler: AudioHandler = None
image_manager: ImageManager = None

@app.route('/')
def index():
    """Main application page."""
    return render_template('index.html')

@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})

@app.route('/api/snapshot', methods=['POST'])
def snapshot():
    """Capture a snapshot from the video stream."""
    try:
        data = request.json
        image_data_b64 = data.get('image', '').split(',')[1]  # Remove data:image/jpeg;base64, prefix
        image_data = base64.b64decode(image_data_b64)
        
        # Store image
        if image_manager:
            image_record = image_manager.store_image(image_data)
            return jsonify({
                'success': True,
                'item': {
                    'id': image_record.id,
                    'filename': image_record.filename,
                    'name': image_record.name,
                    'state': image_record.state,
                    'captured_at': image_record.captured_at.isoformat()
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Image manager not initialized'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/items', methods=['GET'])
def get_items():
    """Get list of captured items."""
    try:
        if image_manager:
            items = image_manager.get_recent_images(limit=20)
            return jsonify({
                'success': True,
                'items': [{
                    'id': item.id,
                    'filename': item.filename,
                    'name': item.name,
                    'category': item.category,
                    'state': item.state,
                    'captured_at': item.captured_at.isoformat()
                } for item in items]
            })
        else:
            return jsonify({'success': False, 'error': 'Image manager not initialized'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """Update an item's metadata."""
    try:
        data = request.json
        if image_manager:
            image = image_manager.update_image(
                item_id,
                name=data.get('name'),
                category=data.get('category'),
                state=data.get('state')
            )
            if image:
                return jsonify({
                    'success': True,
                    'item': {
                        'id': image.id,
                        'filename': image.filename,
                        'name': image.name,
                        'category': image.category,
                        'state': image.state
                    }
                })
            else:
                return jsonify({'success': False, 'error': 'Item not found'}), 404
        else:
            return jsonify({'success': False, 'error': 'Image manager not initialized'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/session/start', methods=['POST'])
def start_session():
    """Start a Live API session."""
    global live_client, video_capture, audio_handler, image_manager
    
    try:
        # Initialize components if not already done
        if not image_manager:
            image_manager = ImageManager()
        
        if not video_capture:
            video_capture = VideoCapture()
            video_capture.start()
        
        if not audio_handler:
            audio_handler = AudioHandler()
            audio_handler.start_input()
            audio_handler.start_output()
        
        # Create snapshot tool
        snapshot_tool = create_snapshot_tool(video_capture)
        
        # Initialize Live API client
        from config import GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION
        live_client = LiveAPIClient(GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION)
        
        # Set up callbacks
        def on_audio_received(audio):
            if audio_handler:
                audio_handler.play_audio(audio)
        
        def on_text_received(text):
            print(f"Received text: {text}")
            # Could send to frontend via WebSocket/SSE
        
        async def on_tool_call(tool_call):
            await handle_tool_call(tool_call)
        
        def on_state_change(state):
            update_reed_orb_state(state)
        
        live_client.on_audio_received = on_audio_received
        live_client.on_text_received = on_text_received
        live_client.on_tool_call = on_tool_call
        live_client.on_state_change = on_state_change
        
        # Connect to Live API (run in background)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(live_client.connect(tools=[snapshot_tool]))
        
        # Set up video frame callback
        async def send_frame(frame):
            await send_video_frame(frame)
        
        video_capture.on_frame = lambda frame: loop.create_task(send_frame(frame))
        
        # Set up audio input callback
        async def send_audio(audio):
            if live_client and live_client.is_connected:
                await live_client.send_audio(audio)
        
        audio_handler.on_audio_input = lambda audio: loop.create_task(send_audio(audio))
        
        return jsonify({'success': True, 'message': 'Session started'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/session/stop', methods=['POST'])
def stop_session():
    """Stop the Live API session."""
    global live_client, video_capture, audio_handler
    
    try:
        if live_client:
            asyncio.create_task(live_client.disconnect())
            live_client = None
        
        if video_capture:
            video_capture.stop()
            video_capture = None
        
        if audio_handler:
            audio_handler.cleanup()
            audio_handler = None
        
        return jsonify({'success': True, 'message': 'Session stopped'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

async def handle_tool_call(tool_call):
    """Handle tool calls from Live API."""
    if live_client and video_capture:
        response = await handle_snapshot_tool_call(tool_call, video_capture)
        
        # Store the captured image
        if response and response.get('function_response', {}).get('response', {}).get('snapshot_captured'):
            image_data_b64 = response['function_response']['response'].get('image_data')
            if image_data_b64 and image_manager:
                import base64
                image_data = base64.b64decode(image_data_b64)
                image_record = image_manager.store_image(image_data)
                print(f"Snapshot stored: {image_record.id}")
        
        # Send response back to Live API
        if live_client.session:
            try:
                await live_client.session.send_tool_response(response)
            except Exception as e:
                print(f"Error sending tool response: {e}")

def update_reed_orb_state(state):
    """Update Reed orb state (called via WebSocket or SSE)."""
    # This would send state updates to frontend via WebSocket or Server-Sent Events
    pass

async def send_video_frame(frame):
    """Send video frame to Live API."""
    import cv2
    import numpy as np
    
    if live_client and live_client.is_connected:
        try:
            # Convert RGB to BGR for OpenCV
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            # Resize to required resolution
            frame_resized = cv2.resize(frame_bgr, (768, 768))
            # Encode as JPEG
            _, buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_bytes = buffer.tobytes()
            await live_client.send_video_frame(frame_bytes, "image/jpeg")
        except Exception as e:
            print(f"Error sending video frame: {e}")

if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
