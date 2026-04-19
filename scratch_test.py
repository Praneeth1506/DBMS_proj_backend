import cv2
import urllib.request
import numpy as np
from app.ai_models.face_recognition.face_service import detect_person_yolo

# download a test image of a person
url = "https://ultralytics.com/images/zidane.jpg"
req = urllib.request.urlopen(url)
arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
img = cv2.imdecode(arr, -1)

detected, bbox = detect_person_yolo(img)
print(f"Detected: {detected}, Bounding Box: {bbox}")
