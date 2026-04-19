import requests
import os
import time

# Note: This requires 'requests' to be installed
URL = "http://localhost:8002/transcribe"

def test_transcription():
    # 1. We'll use a dummy audio file path (you can replace this with a real .wav)
    # If you have a file named 'test.wav' in this folder, it will use it.
    filename = "test_audio.wav"
    
    # Create a fake tiny file if it doesn't exist just to test the connection
    if not os.path.exists(filename):
        print(f"No {filename} found. Please record a short .wav file or provide one.")
        return

    print(f"Sending {filename} to transcription service...")
    with open(filename, 'rb') as f:
        files = {'file': f}
        try:
            start_time = time.time()
            response = requests.post(URL, files=files)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                print("--- Success! ---")
                print(f"Time taken: {duration:.2f}s")
                print("Result JSON:", response.json())
            else:
                print("--- Error ---")
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"Failed to connect: {e}")

if __name__ == "__main__":
    test_transcription()
