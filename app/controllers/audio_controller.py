import os
import tempfile
import speech_recognition as sr
from flask import jsonify

from app.database.db import insert_conversation
from app.ai_models.transcription.whisper_service import transcribe_audio_file

def process_audio_upload(request):
    if 'audio' not in request.files:
        return jsonify({"error": "No 'audio' file in request"}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    userid = request.form.get('userid', 1) # Default to 1 if not provided
    personid = request.form.get('personid', None)

    # Save to temp file
    temp_fd, temp_path = tempfile.mkstemp(suffix=".wav")
    os.close(temp_fd)
    
    try:
        audio_file.save(temp_path)
        text = transcribe_audio_file(temp_path)
        
        # Save to database
        interaction_id = insert_conversation(userid=userid, personid=personid, text=text)
        
        return jsonify({
            "message": "Audio processed successfully",
            "transcription": text,
            "interactionid": interaction_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def record_audio_from_mic(request):
    """
    Record audio actively from the backend server's microphone.
    NOTE: This only uses the microphone of the machine hosting the backend.
    """
    data = request.json or {}
    userid = data.get('userid', 1)
    personid = data.get('personid', None)

    recognizer = sr.Recognizer()
    try:
        # Save the recorded audio to a temporary file, then transcribe using Whisper
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            # Record for up to 10 seconds or until silence
            audio_data = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        
        temp_fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(temp_fd)
        
        with open(temp_path, "wb") as f:
            f.write(audio_data.get_wav_data())
            
        text = transcribe_audio_file(temp_path)
        
        # Save to DB
        interaction_id = insert_conversation(userid=userid, personid=personid, text=text)
        
        return jsonify({
            "message": "Microphone recording processed successfully",
            "transcription": text,
            "interactionid": interaction_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
