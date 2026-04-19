import os
import tempfile
import queue
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write as wav_write
from fastapi import UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

# (Local imports are used within functions for db.py)
from app.ai_models.transcription.whisper_service import transcribe_audio_file

# ---------------------------------------------------------------------------
# VAD constants — tune these if needed
# ---------------------------------------------------------------------------
SAMPLE_RATE      = 16000                          # Hz (Whisper's native rate)
CHANNELS         = 1
CHUNK_MS         = 30                             # audio chunk size in ms
CHUNK_FRAMES     = int(SAMPLE_RATE * CHUNK_MS / 1000)

# RMS energy threshold for speech detection (0–32767 for int16).
# Raise in noisy environments; lower for soft voices.
SPEECH_THRESHOLD = 500

# Consecutive silent chunks before stopping (~1.5 s of silence)
SILENCE_CHUNKS   = int(1500 / CHUNK_MS)           # 50 chunks × 30 ms

# Safety cap — always stop after this many seconds
MAX_DURATION_SEC = 60


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _rms(chunk: np.ndarray) -> float:
    return float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))

def record_audio_with_vad() -> np.ndarray:
    """
    Stream mic audio with a simple energy-based Voice Activity Detector.

    State machine:
        WAITING  → silent until speech energy >= SPEECH_THRESHOLD
        SPEAKING → recording; resets silence counter on every speech chunk
        SILENCE  → stops after SILENCE_CHUNKS consecutive quiet chunks

    Returns a 1-D int16 numpy array of the captured speech.
    """
    audio_queue: queue.Queue = queue.Queue()

    def _callback(indata, frames, time, status):
        audio_queue.put(indata.copy())

    recorded_chunks: list[np.ndarray] = []
    speech_started = False
    silent_count   = 0
    max_chunks     = int(MAX_DURATION_SEC * 1000 / CHUNK_MS)
    total_chunks   = 0

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        blocksize=CHUNK_FRAMES,
        callback=_callback,
    ):
        while total_chunks < max_chunks:
            chunk = audio_queue.get().flatten()
            total_chunks += 1
            energy = _rms(chunk)

            if not speech_started:
                if energy >= SPEECH_THRESHOLD:
                    speech_started = True
                    silent_count   = 0
                    recorded_chunks.append(chunk)
            else:
                recorded_chunks.append(chunk)
                if energy < SPEECH_THRESHOLD:
                    silent_count += 1
                    if silent_count >= SILENCE_CHUNKS:
                        break
                else:
                    silent_count = 0

    if not recorded_chunks:
        return np.array([], dtype=np.int16)
    return np.concatenate(recorded_chunks)


# ---------------------------------------------------------------------------
# Controllers
# ---------------------------------------------------------------------------

async def process_audio_upload(
    audio: UploadFile,
    userid: int = 1,
    personid: Optional[int] = None,
):
    """
    Accept an uploaded audio file, transcribe it with Whisper and save to DB.
    """
    from app.database.db import save_conversation
    temp_path = None
    try:
        contents = await audio.read()
        temp_fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(temp_fd)

        with open(temp_path, "wb") as f:
            f.write(contents)

        text = transcribe_audio_file(temp_path)
        interaction_id = save_conversation(userid, personid, text, None, None)

        return JSONResponse({
            "message": "Audio processed successfully",
            "transcription": text,
            "interactionid": interaction_id,
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def record_audio_from_mic(userid: int = 1, personid: Optional[int] = None):
    """
    Record audio from the server's microphone using VAD.

    Waits silently until speech is detected, records until ~1.5 s of silence,
    then transcribes with Whisper and saves to DB.
    """
    from app.database.db import save_conversation
    temp_path = None
    try:
        audio_data = record_audio_with_vad()

        if audio_data.size == 0:
            raise HTTPException(
                status_code=422,
                detail="No speech detected. Please speak into the microphone.",
            )

        temp_fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(temp_fd)

        wav_write(temp_path, SAMPLE_RATE, audio_data)
        text = transcribe_audio_file(temp_path)
        interaction_id = save_conversation(userid, personid, text, None, None)

        return JSONResponse({
            "message": "Microphone recording processed successfully",
            "transcription": text,
            "interactionid": interaction_id,
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
