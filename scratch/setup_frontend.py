import os
import requests

MODELS_DIR = "frontend/public/models"
GITHUB_RAW = "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights"

models = [
    "tiny_face_detector_model-weights_manifest.json",
    "tiny_face_detector_model-shard1",
    "face_landmark_68_model-weights_manifest.json",
    "face_landmark_68_model-shard1",
    "face_recognition_model-weights_manifest.json",
    "face_recognition_model-shard1"
]

if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)

print("⏬ Downloading AI models for face detection (this might take a minute)...")

for model in models:
    url = f"{GITHUB_RAW}/{model}"
    print(f"Downloading {model}...")
    r = requests.get(url)
    with open(os.path.join(MODELS_DIR, model), "wb") as f:
        f.write(r.content)

print("✅ UI setup complete! You can now run 'npm run dev' inside the frontend folder.")
