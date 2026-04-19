import speech_recognition as sr
import requests
import os

# Configuration
SERVER_URL = "http://localhost:8003/transcribe"

def record_and_transcribe():
    """
    Listens until the user stops talking, then sends the audio to the server.
    """
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("🎤 Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        print("🎙️ Listening... (Stop talking to finish)")
        try:
            # listens until silence is detected
            audio_data = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            
            # Save the captured audio locally
            filename = "temp_recording.wav"
            with open(filename, "wb") as f:
                f.write(audio_data.get_wav_data())
            
            print("📤 Sending to server...")
            with open(filename, 'rb') as f:
                files = {'file': f}
                response = requests.post(SERVER_URL, files=files)
                
            if response.status_code == 200:
                text = response.json().get("text")
                print(f"✅ Transcribed: {text}")
                return text
            else:
                print(f"❌ Server Error: {response.text}")
                return None
        
        except sr.WaitTimeoutError:
            print("⏳ No speech detected (Timeout).")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
        finally:
            if os.path.exists("temp_recording.wav"):
                os.remove("temp_recording.wav")

if __name__ == "__main__":
    # Test it
    record_and_transcribe()
