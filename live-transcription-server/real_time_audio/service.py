import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import logging
import time
from datetime import datetime
import platform
import os
import tempfile
import io

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class TranscriptionService:
    def __init__(self):
        self.device, self.torch_dtype = self._setup_device_and_dtype()
        model_id = "openai/whisper-tiny"

        try:
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                model_id,
                torch_dtype=self.torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
            )
            self.model.to(self.device)
            self.model.eval()
            
            self.processor = AutoProcessor.from_pretrained(model_id)
            
            device_arg = self._get_pipeline_device()
            
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model,
                tokenizer=self.processor.tokenizer,
                feature_extractor=self.processor.feature_extractor,
                torch_dtype=self.torch_dtype,
                device=device_arg,
            )
            self.sampling_rate = 16000
            logger.info(f"TranscriptionService initialized successfully using device: {self.device}, dtype: {self.torch_dtype}")
        except Exception as e:
            logger.error(f"Failed to initialize TranscriptionService: {e}")
            raise

    def _setup_device_and_dtype(self):
        """Determine the appropriate device and dtype based on system capabilities."""
        if torch.cuda.is_available():
            logger.info("CUDA is available - using GPU")
            return "cuda:0", torch.float16
        elif (
            hasattr(torch.backends, "mps")
            and torch.backends.mps.is_available()
            and platform.system() == "Darwin"
        ):
            logger.info("MPS is available - using Apple Silicon GPU")
            return "mps", torch.float32  
        else:
            logger.info("No GPU detected - using CPU")
            return "cpu", torch.float32

    def _get_pipeline_device(self):
        """Convert device string to appropriate pipeline device argument"""
        if self.device == "cuda:0":
            return 0
        elif self.device == "mps":
            return "mps"
        else:
            return -1

    def convert_mov_to_wav(self, input_file_path: str) -> str:
        """Convert a MOV file to WAV using ffmpeg."""
        import ffmpeg
        
        output_file_path = input_file_path.replace(".mov", ".wav")

        try:
            ffmpeg.input(input_file_path).output(output_file_path, format="wav").run(overwrite_output=True)
            return output_file_path
        except Exception as e:
            logger.error(f"Error converting MOV to WAV: {e}")
            return None

    def transcribe_file(self, file_path: str) -> str:
        """Transcribe an uploaded audio file, converting it if necessary."""
        try:
            # Convert MOV to WAV if needed
            if file_path.lower().endswith(".mov"):
                converted_file_path = self.convert_mov_to_wav(file_path)
                if converted_file_path is None:
                    return "Transcription failed due to file conversion error."
                file_path = converted_file_path  # Use the converted WAV file

            # Read audio data from the file
            with open(file_path, "rb") as audio_file:
                audio_bytes = audio_file.read()

            # Call the correct transcription function
            transcription_text = self.transcribe(audio_bytes)

            # Clean up temporary files if applicable
            if file_path.endswith(".wav") and file_path.startswith("temp_"):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Error removing temporary file: {e}")
                
            # Return just the transcription text as a string
            return transcription_text

        except Exception as e:
            logger.error(f"Error transcribing file: {e}")
            return "Transcription failed."

    def transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio bytes to text."""
        start_time = time.perf_counter()
        start_datetime = datetime.now().isoformat()
        logger.info(f"Starting transcription at: {start_datetime}")
        
        try:
            pipeline_start = time.perf_counter()
            transcription = self.pipe(audio_data)
            pipeline_duration = time.perf_counter() - pipeline_start
            
            transcription_text = transcription.get("text", "").strip()
            total_duration = time.perf_counter() - start_time
            
            logger.info(
                f"Transcription completed - "
                f"Start time: {start_datetime}, "
                f"Pipeline execution: {pipeline_duration:.3f}s, "
                f"Total time: {total_duration:.3f}s, "
                f"Result length: {len(transcription_text)} chars, "
                f"Transcribed text: {transcription_text[:100]}..."  # Log just the first 100 chars
            )
            
            return transcription_text
        except Exception as e:
            error_duration = time.perf_counter() - start_time
            logger.error(f"Error in transcription after {error_duration:.3f}s: {e}")
            return "Transcription failed."
        finally:
            if self.device == "cuda:0":
                torch.cuda.empty_cache()