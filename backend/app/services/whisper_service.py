"""
services/whisper_service.py — Whisper STT integration (from legacy app)
"""
import os
import logging
import whisper

logger = logging.getLogger(__name__)

# Load the whisper model once when this module is imported
# "base" or "tiny" is faster for local runs. Adjust model size based on hardware.
_model = None


def get_whisper_model():
    """Lazy load Whisper model"""
    global _model
    if _model is None:
        logger.info("Loading Whisper model (base)...")
        _model = whisper.load_model("base")
        logger.info("Whisper model loaded successfully")
    return _model


def transcribe_audio_file(file_path: str) -> str:
    """
    Transcribe a given audio file using OpenAI's Whisper model.
    
    Args:
        file_path: Path to audio file
    
    Returns:
        Transcribed text
    
    Raises:
        FileNotFoundError: If audio file doesn't exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    model = get_whisper_model()
    result = model.transcribe(file_path)
    return result["text"].strip()
