import whisper
import os

# Create a place to store temporary audio files
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Load the whisper model ('small' is significantly better for Tamil)
model = whisper.load_model("small")

def transcribe_audio(file_path):
    """
    Takes a path to an audio file and returns the transcribed text.
    """
    try:
        # Auto-detect language (works for both English and Tamil)
        result = model.transcribe(file_path)
        return result["text"].strip()
    except Exception as e:
        print(f"Transcription Error: {e}")
        return None
    finally:
        # Clean up the file after transcription if desired
        if os.path.exists(file_path):
            os.remove(file_path)
