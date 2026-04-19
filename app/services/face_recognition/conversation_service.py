import json
import os
import tempfile
import time
import threading
from datetime import datetime
from typing import Optional, Callable
import contextlib

import numpy as np
import sounddevice as sd
import soundfile as sf
from openai import OpenAI
from faster_whisper import WhisperModel
from dotenv import load_dotenv

from app.database.db import get_db_connection

load_dotenv()

@contextlib.contextmanager
def get_conn():
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# ── OpenAI client ─────────────────────────────────────────────────────────────
_openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Whisper model ──────────────────────────────────────────────────────────────
_whisper_lock  = threading.Lock()
_whisper_model: Optional[WhisperModel] = None

# ── Audio constants ────────────────────────────────────────────────────────────
SAMPLE_RATE      = 16000
CHANNELS         = 1
DTYPE            = "float32"
CHUNK_DURATION   = 0.3          # seconds per processing chunk
SPEECH_THRESHOLD = 0.015        # RMS threshold — tweak if too sensitive
SILENCE_TIMEOUT  = 5.0          # seconds of silence → trigger live transcription
PRE_SPEECH_PAD   = 0.5          # seconds of audio kept before speech onset

# ── Global recording state ─────────────────────────────────────────────────────
_rec_lock         = threading.Lock()
_is_recording     = False
_rec_thread: Optional[threading.Thread] = None

# Buffers
_full_buffer:    list[np.ndarray] = []   # entire session audio (for final save)
_speech_buffer:  list[np.ndarray] = []  # current speech segment being built
_pre_buffer:     list[np.ndarray] = []  # rolling pre-speech padding

# Accumulated live transcript (all chunks this session)
_live_transcript_parts: list[str] = []

# VAD state
_silence_start: Optional[float] = None
_has_speech    = False

# Callback: called with new text each time a chunk is transcribed
_transcript_callback: Optional[Callable[[str], None]] = None


# =============================================================================
# Whisper
# =============================================================================

def _get_whisper() -> WhisperModel:
    global _whisper_model
    with _whisper_lock:
        if _whisper_model is None:
            print("[ConvService] Loading Whisper small …")
            _whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
            print("[ConvService] Whisper ready ✓")
        return _whisper_model


# =============================================================================
# Public recording API
# =============================================================================

def record_audio(on_transcript: Optional[Callable[[str], None]] = None) -> None:
    """
    Start continuous VAD-based audio capture.
    `on_transcript(text)` is called each time a speech segment is transcribed.
    Call stop_recording() to end the session.
    """
    global _is_recording, _rec_thread, _transcript_callback
    global _full_buffer, _speech_buffer, _pre_buffer
    global _live_transcript_parts, _has_speech, _silence_start

    with _rec_lock:
        if _is_recording:
            return
        # Reset state
        _full_buffer           = []
        _speech_buffer         = []
        _pre_buffer            = []
        _live_transcript_parts = []
        _has_speech            = False
        _silence_start         = None
        _transcript_callback   = on_transcript
        _is_recording          = True

    _rec_thread = threading.Thread(target=_vad_record_loop, daemon=True, name="VADRecorder")
    _rec_thread.start()
    print("[ConvService] VAD recording started ✓")


def stop_recording() -> np.ndarray:
    """
    Stop audio capture and return the full session audio as a flat float32 array.
    """
    global _is_recording
    with _rec_lock:
        _is_recording = False

    if _rec_thread and _rec_thread.is_alive():
        _rec_thread.join(timeout=3.0)

    with _rec_lock:
        if not _full_buffer:
            return np.array([], dtype=np.float32)
        combined = np.concatenate(_full_buffer, axis=0)
        _full_buffer.clear()
        print(f"[ConvService] Recording stopped — {len(combined)/SAMPLE_RATE:.1f}s total")
        return combined


def is_recording() -> bool:
    return _is_recording


def has_speech() -> bool:
    """True if VAD currently detects active speech (user is talking right now)."""
    with _rec_lock:
        return _has_speech


def get_live_transcript() -> str:
    """Return the accumulated live transcript for the current session."""
    with _rec_lock:
        return " ".join(_live_transcript_parts)


# =============================================================================
# VAD loop
# =============================================================================

def _vad_record_loop():
    """
    Continuous recording thread.
    Reads CHUNK_DURATION-second chunks, applies simple energy VAD,
    accumulates speech, and triggers transcription on silence.
    """
    global _has_speech, _silence_start, _speech_buffer, _pre_buffer, _full_buffer

    chunk_frames    = int(CHUNK_DURATION * SAMPLE_RATE)
    pre_buffer_max  = int(PRE_SPEECH_PAD / CHUNK_DURATION)

    print("[ConvService] VAD loop running …")

    while True:
        with _rec_lock:
            if not _is_recording:
                break

        try:
            chunk = sd.rec(chunk_frames, samplerate=SAMPLE_RATE,
                           channels=CHANNELS, dtype=DTYPE)
            sd.wait()
            chunk_flat = chunk.flatten()
        except Exception as e:
            print(f"[ConvService] Record chunk error: {e}")
            time.sleep(0.5)
            continue

        rms = float(np.sqrt(np.mean(chunk_flat ** 2)))
        now = time.time()

        with _rec_lock:
            if not _is_recording:
                break

            # Accumulate to full buffer always
            _full_buffer.append(chunk_flat.copy())

            if rms >= SPEECH_THRESHOLD:
                # ── Speech detected ───────────────────────────────────────────
                if not _has_speech:
                    # Include pre-speech padding for natural start
                    _speech_buffer.extend(list(_pre_buffer))
                    _pre_buffer.clear()
                    _has_speech    = True
                    _silence_start = None

                _speech_buffer.append(chunk_flat.copy())

            else:
                # ── Silence ───────────────────────────────────────────────────
                if _has_speech:
                    _speech_buffer.append(chunk_flat.copy())  # trailing silence context

                    if _silence_start is None:
                        _silence_start = now
                    elif now - _silence_start >= SILENCE_TIMEOUT:
                        # Trigger live transcription of accumulated speech
                        segment = np.concatenate(_speech_buffer)
                        _speech_buffer  = []
                        _silence_start  = None
                        _has_speech     = False

                        # Run in background so we don't block recording
                        threading.Thread(
                            target=_transcribe_segment,
                            args=(segment,),
                            daemon=True,
                        ).start()
                else:
                    # Rolling pre-speech buffer
                    _pre_buffer.append(chunk_flat.copy())
                    if len(_pre_buffer) > pre_buffer_max:
                        _pre_buffer.pop(0)

    print("[ConvService] VAD loop stopped")


def _transcribe_segment(audio: np.ndarray):
    """Transcribe one speech segment and invoke the callback."""
    global _live_transcript_parts
    text = transcribe_audio(audio)
    if not text:
        return

    with _rec_lock:
        _live_transcript_parts.append(text)

    if _transcript_callback:
        try:
            full_so_far = " ".join(_live_transcript_parts)
            _transcript_callback(full_so_far)
        except Exception as e:
            print(f"[ConvService] Transcript callback error: {e}")


# =============================================================================
# Transcription
# =============================================================================

def transcribe_audio(audio: np.ndarray) -> str:
    """
    Transcribe a float32 audio array using Whisper.
    Returns the full transcript string (may be empty).
    """
    if audio is None or len(audio) < SAMPLE_RATE * 0.3:   # skip < 0.3s clips
        return ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, SAMPLE_RATE)
            tmp_path = f.name

        model    = _get_whisper()
        segments, _ = model.transcribe(
            tmp_path,
            language="en",
            beam_size=3,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=300),
        )
        os.unlink(tmp_path)
        transcript = " ".join(seg.text.strip() for seg in segments).strip()
        if transcript:
            print(f"[ConvService] Transcript chunk ({len(transcript)}c): {transcript[:80]}")
        return transcript
    except Exception as e:
        print(f"[ConvService] Transcription error: {e}")
        return ""


# =============================================================================
# Summarisation
# =============================================================================

def summarize_conversation(transcript: str) -> str:
    """
    Use OpenAI GPT-4o-mini to produce a 1–2 sentence summary.
    Falls back to first 200 chars of transcript on any error.
    """
    if not transcript or len(transcript.strip()) < 10:
        return transcript or ""
    try:
        response = _openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise summariser. "
                        "Summarise the following conversation transcript in 1–2 sentences. "
                        "Focus on the key topic and tone."
                    ),
                },
                {"role": "user", "content": transcript},
            ],
            max_tokens=100,
            temperature=0.3,
        )
        summary = response.choices[0].message.content.strip()
        print(f"[ConvService] Summary: {summary}")
        return summary
    except Exception as e:
        print(f"[ConvService] Summarisation error: {e}")
        return transcript[:200]


# =============================================================================
# Database helpers
# =============================================================================

def save_person(
    name: str,
    relationship_type: str,
    priority_level: int = 3,
    notes: str = "",
    userid: int = 1,
) -> int:
    """
    Insert a new row into knownperson and userknownperson.
    Returns the new personid.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.knownperson (name, relationshiptype, prioritylevel, notes)
                VALUES (%s, %s, %s, %s)
                RETURNING personid
                """,
                (name, relationship_type, priority_level, notes),
            )
            person_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO public.userknownperson (userid, personid)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (userid, person_id),
            )
    print(f"[ConvService] New person saved: personid={person_id}, name={name}")
    return person_id


def save_faceencoding(
    person_id: int,
    embedding: list,
    confidence_score: float = 0.90,
) -> int:
    """
    Insert a new face embedding for the given person.
    Returns the new faceencodingid.
    """
    encoding_json = json.dumps(embedding)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.faceencoding (personid, encodingdata, confidencescore)
                VALUES (%s, %s, %s)
                RETURNING faceencodingid
                """,
                (person_id, encoding_json, confidence_score),
            )
            enc_id = cur.fetchone()[0]
    print(f"[ConvService] Face encoding saved: faceencodingid={enc_id}, personid={person_id}")
    return enc_id


def save_conversation(
    userid: int,
    person_id: Optional[int],
    transcript: str,
    summary: str,
    emotion: str,
    location: str = "Living Room",
) -> int:
    """
    Insert a row into the conversation table.
    Returns the new interactionid.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.conversation
                    (userid, personid, interactiondatetime, location,
                     conversation, summarytext, emotiondetected)
                VALUES (%s, %s, NOW(), %s, %s, %s, %s)
                RETURNING interactionid
                """,
                (userid, person_id, location, transcript, summary, emotion),
            )
            interaction_id = cur.fetchone()[0]
    print(f"[ConvService] Conversation saved: interactionid={interaction_id}")
    return interaction_id


def save_emotion_record(interaction_id: int, emotion_type: str, confidence: float) -> int:
    """Insert a row into emotionrecord. Returns new emotionid."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.emotionrecord (interactionid, emotiontype, confidencelevel)
                VALUES (%s, %s, %s)
                RETURNING emotionid
                """,
                (interaction_id, emotion_type, confidence),
            )
            return cur.fetchone()[0]


# ── Query helpers ─────────────────────────────────────────────────────────────

def get_all_face_encodings(userid: int = 1) -> list:
    """
    Fetch all face encodings belonging to persons linked to `userid`.
    Returns list of {personid, faceencodingid, encodingdata, confidencescore}
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fe.faceencodingid, fe.personid, fe.encodingdata, fe.confidencescore
                FROM public.faceencoding fe
                JOIN public.userknownperson ukp ON ukp.personid = fe.personid
                WHERE ukp.userid = %s
                """,
                (userid,),
            )
            rows = cur.fetchall()
    return [
        {
            "faceencodingid": r[0],
            "personid":       r[1],
            "encodingdata":   r[2],
            "confidencescore": float(r[3]) if r[3] is not None else None,
        }
        for r in rows
    ]


def get_known_person(person_id: int) -> Optional[dict]:
    """Fetch a single knownperson row by personid."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT personid, name, relationshiptype, prioritylevel, notes
                FROM public.knownperson WHERE personid = %s
                """,
                (person_id,),
            )
            row = cur.fetchone()
    if not row:
        return None
    return {
        "personid": row[0], "name": row[1],
        "relationshiptype": row[2], "prioritylevel": row[3], "notes": row[4],
    }


def get_all_known_persons(userid: int = 1) -> list:
    """List all known persons linked to the given user."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT kp.personid, kp.name, kp.relationshiptype, kp.prioritylevel, kp.notes
                FROM public.knownperson kp
                JOIN public.userknownperson ukp ON ukp.personid = kp.personid
                WHERE ukp.userid = %s
                ORDER BY kp.prioritylevel ASC, kp.name ASC
                """,
                (userid,),
            )
            rows = cur.fetchall()
    return [
        {"personid": r[0], "name": r[1], "relationshiptype": r[2],
         "prioritylevel": r[3], "notes": r[4]}
        for r in rows
    ]


def get_conversation_history(userid: int = 1, limit: int = 20) -> list:
    """Return the most recent conversations for the given user, newest first."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.interactionid, c.personid, kp.name AS person_name,
                       kp.relationshiptype,
                       c.interactiondatetime, c.location,
                       c.conversation, c.summarytext, c.emotiondetected
                FROM public.conversation c
                LEFT JOIN public.knownperson kp ON kp.personid = c.personid
                WHERE c.userid = %s
                ORDER BY c.interactiondatetime DESC
                LIMIT %s
                """,
                (userid, limit),
            )
            rows = cur.fetchall()
    return [
        {
            "interactionid": r[0],
            "personid":      r[1],
            "person_name":   r[2],
            "relationshiptype": r[3],
            "timestamp":     r[4].isoformat() if r[4] else None,
            "location":      r[5],
            "conversation":  r[6],
            "summary":       r[7],
            "emotiondetected": r[8],
        }
        for r in rows
    ]
