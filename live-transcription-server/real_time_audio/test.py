from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .handler import transcription_handler
import logging
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/transcribe")
async def transcribe_audio(websocket: WebSocket):
    """WebSocket endpoint for real-time audio transcription"""
    session_id = None
    try:
        logger.debug("Accepting WebSocket connection")
        await websocket.accept()  # Explicitly accept the connection
        session_id = await transcription_handler.connect(websocket)
        logger.info(f"Connection Successful, session_id: {session_id}")
        print('Connection Successful, session_id:', session_id)
        # Keep the connection open indefinitely
        await asyncio.Future()  # This will never complete normally
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")
        print(f"Client disconnected: {session_id}")
        if session_id:
            await transcription_handler.disconnect(session_id)
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
        print(f"Error in WebSocket connection: {e}")
        if session_id:
            await transcription_handler.disconnect(session_id)
