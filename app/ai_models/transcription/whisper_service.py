import whisper
import os

# Load the whisper model once when this module is imported.
# "base" or "tiny" is faster for local runs. Adjust model size based on hardware.
model = whisper.load_model("base")

def transcribe_audio_file(file_path: str) -> str:
    """
    Transcribe a given audio file using OpenAI's Whisper model.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    result = model.transcribe(file_path)
    return result["text"].strip()
