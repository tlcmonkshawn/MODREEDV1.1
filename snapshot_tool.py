"""Snapshot tool function for Live API function calling."""
from typing import Dict, Any, Optional
from video_capture import VideoCapture


def create_snapshot_tool(video_capture: VideoCapture) -> Dict[str, Any]:
    """Create a function calling tool definition for snapshot capture.
    
    Args:
        video_capture: VideoCapture instance to use for snapshots
        
    Returns:
        Tool definition dictionary for Live API
    """
    return {
        "function_declarations": [{
            "name": "capture_snapshot",
            "description": "Capture a snapshot of the current video frame. This pauses the video stream, captures the current frame, and returns the image data for analysis and storage.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }]
    }


async def handle_snapshot_tool_call(tool_call: Dict[str, Any], video_capture: VideoCapture) -> Dict[str, Any]:
    """Handle a snapshot tool call from the Live API.
    
    Args:
        tool_call: Tool call message from Live API
        video_capture: VideoCapture instance to use for snapshots
        
    Returns:
        Tool response dictionary
    """
    function_name = tool_call.get("function_call", {}).get("name", "")
    
    if function_name == "capture_snapshot":
        # Pause video stream
        video_capture.pause()
        
        # Capture snapshot
        snapshot_data = video_capture.capture_snapshot()
        
        if snapshot_data:
            # Resume video after a brief moment
            import asyncio
            await asyncio.sleep(0.1)
            video_capture.resume()
            
            # Return snapshot data as base64
            import base64
            snapshot_b64 = base64.b64encode(snapshot_data).decode('utf-8')
            
            return {
                "function_response": {
                    "name": function_name,
                    "response": {
                        "snapshot_captured": True,
                        "image_data": snapshot_b64,
                        "mime_type": "image/jpeg",
                        "width": 768,
                        "height": 768
                    }
                }
            }
        else:
            video_capture.resume()
            return {
                "function_response": {
                    "name": function_name,
                    "response": {
                        "snapshot_captured": False,
                        "error": "Failed to capture snapshot"
                    }
                }
            }
    
    return {
        "function_response": {
            "name": function_name,
            "response": {
                "error": "Unknown function"
            }
        }
    }

