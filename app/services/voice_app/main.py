from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import shutil
import os
from app.services.voice_app.transcription_service import transcribe_audio
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/", response_class=HTMLResponse)
async def voice_home(request: Request):
    return templates.TemplateResponse(request=request, name="voice_test.html")

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    
    temp_path = os.path.join("uploads", file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    text = transcribe_audio(temp_path)
    
    if text:
        return {"status": "success", "text": text}
    else:
        return {"status": "error", "message": "Transcription failed"}
