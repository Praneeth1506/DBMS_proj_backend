from flask import Blueprint, request
from app.controllers.audio_controller import process_audio_upload, record_audio_from_mic

audio_bp = Blueprint('audio_bp', __name__)

@audio_bp.route('/audio/upload', methods=['POST'])
def audio_upload():
    return process_audio_upload(request)

@audio_bp.route('/audio/record_from_mic', methods=['POST'])
def audio_record_from_mic():
    return record_audio_from_mic(request)
