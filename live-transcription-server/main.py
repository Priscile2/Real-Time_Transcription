from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from real_time_audio.routes import router as audio_router
from real_time_audio.service import TranscriptionService
import uuid
import subprocess
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Allow CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins, change to specific domains for production
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],  # Allow all headers
)

app.include_router(audio_router)

transcription_service = TranscriptionService()

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Endpoint for transcribing uploaded audio files.
    
    Args:
        file: The uploaded audio file
        
    Returns:
        JSON response with transcribed text using consistent key name
    """
    logger.info(f"Received file upload: {file.filename}")
    
    # Generate a unique filename for processing
    file_extension = file.filename.split(".")[-1].lower()
    temp_filename = f"temp_{uuid.uuid4()}.{file_extension}"
    temp_audio_path = f"temp_{uuid.uuid4()}.wav"  # Convert to WAV for transcription
    
    try:
        # Save the uploaded file
        with open(temp_filename, "wb") as buffer:
            buffer.write(await file.read())
        
        logger.info(f"Saved temporary file: {temp_filename}")
        
        # Convert to WAV using ffmpeg
        try:
            subprocess.run(
                ["ffmpeg", "-i", temp_filename, "-ac", "1", "-ar", "16000", temp_audio_path],
                check=True
            )
            logger.info(f"Converted to WAV: {temp_audio_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio conversion failed: {e}")
            return {"error": f"Audio conversion failed: {e}"}
        
        # Read converted audio
        with open(temp_audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()

        # Transcribe audio
        logger.info("Starting transcription")
        transcription_text = transcription_service.transcribe(audio_bytes)
        logger.info(f"Transcription complete: {transcription_text[:50]}...")
        
        # Always use a consistent key name for the transcription
        return {
            "transcriptionText": transcription_text,  # Use this as the consistent key name
        }
        
    except Exception as e:
        logger.error(f"Error in transcribe_audio: {e}")
        return {"error": str(e)}
        
    finally:
        # Clean up temporary files
        try:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            logger.info("Temporary files cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}")

# To run the server, use the command:
# uvicorn main:app --reload