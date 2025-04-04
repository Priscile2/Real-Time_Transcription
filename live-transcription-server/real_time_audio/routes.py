from fastapi import APIRouter, WebSocket, WebSocketDisconnect, File, UploadFile
from .handler import transcription_handler
import logging
import asyncio
from pathlib import Path
from pathlib import Path


logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/transcribe")
async def transcribe_audio(websocket: WebSocket):
    """WebSocket endpoint for real-time audio transcription"""
    session_id = None
    try:
        session_id = await transcription_handler.connect(websocket)
        # Use asyncio.Future() to keep the connection open indefinitely
        await asyncio.Future()  # This will never complete normally
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")
        if session_id:
            await transcription_handler.disconnect(session_id)
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
        if session_id:
            await transcription_handler.disconnect(session_id)
            
            
UPLOAD_DIR = Path("uploaded_audio")
UPLOAD_DIR.mkdir(exist_ok=True)  # Ensure directory exists

@router.post("/api/transcription/upload-video")
async def upload_audio(file: UploadFile = File(...)):
    """Endpoint to upload an audio file for transcription."""
    try:
        # Generate unique filename
        file_ext = file.filename.split(".")[-1]
        if file_ext not in ["wav", "mp3","mp4", "mov","flac", "ogg", "m4a"]:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = UPLOAD_DIR / filename

        # Save uploaded file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Transcribe the audio file
        transcription = transcription_handler.transcribe_audio_file(str(file_path))

        return {"filename": filename, "transcription": transcription}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio file: {e}")