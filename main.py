import speech_recognition as sr
import pyaudio
import wave
import time
from datetime import datetime
import os
from utils.audio_tools import calculate_volume, save_audio

# ====== CONFIGURATION ======
LISTEN_DURATION = 30  # seconds
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
VOLUME_THRESHOLD = 1000  # Adjust this based on environment
DISTRESS_KEYWORDS = ["help", "please help me", "bachao", "choro"]
SAFE_PHRASE = "i am safe"
AUDIO_SAVE_DIR = "audio_logs"

# ====== INITIALIZE ======
recognizer = sr.Recognizer()
audio_interface = pyaudio.PyAudio()

def listen_for_speech(timeout=3):
    """Listen to mic for a short time and return audio data."""
    with sr.Microphone(sample_rate=RATE) as source:
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=timeout)
            return audio
        except sr.WaitTimeoutError:
            return None

def detect_keywords(text, keywords):
    """Check if any keyword is in the text."""
    text = text.lower()
    return any(kw in text for kw in keywords)

def get_timestamped_filename():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{AUDIO_SAVE_DIR}/distress_{timestamp}.wav"

def start_recording_loop(wf):
    print("[🔴 Recording started...] Say your safe phrase when safe.")
    recorded_frames = []

    while True:
        stream = audio_interface.open(format=FORMAT, channels=CHANNELS,
                                      rate=RATE, input=True, frames_per_buffer=CHUNK)
        data = stream.read(CHUNK)
        recorded_frames.append(data)
        stream.stop_stream()
        stream.close()

        # Detect loudness
        volume = calculate_volume(data)
        if volume > VOLUME_THRESHOLD:
            print(f"[‼️ Loud sound detected during recording] Volume: {volume}")

        # Detect safe phrase
        try:
            chunk_audio = sr.AudioData(data, RATE, 2)
            text = recognizer.recognize_google(chunk_audio).lower()
            print(f"[🗣️ Heard during recording]: {text}")
            if SAFE_PHRASE in text:
                print("[✅ Safe phrase detected. Stopping recording.]")
                break
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"[❌ Speech recognition error]: {e}")

    save_audio(wf, recorded_frames)
    print(f"[💾 Audio saved to {wf}]")


def main():
    print("[🚨 Safety Listener Activated] Listening for 30 seconds...")

    start_time = time.time()
    heard_something = False

    while time.time() - start_time < LISTEN_DURATION:
        audio = listen_for_speech(timeout=3)

        if audio is None:
            continue

        heard_something = True

        # Convert audio to text
        try:
            text = recognizer.recognize_google(audio)
            print(f"[🗣️ Heard]: {text}")
            if detect_keywords(text, DISTRESS_KEYWORDS):
                print("[‼️ Distress keyword detected]")
                output = 1
                print(f"Output: {output}")
                filename = get_timestamped_filename()
                start_recording_loop(filename)
                return
        except sr.UnknownValueError:
            pass

        # Also check for loud noises
        audio_data = audio.get_raw_data()
        volume = calculate_volume(audio_data)
        if volume > VOLUME_THRESHOLD:
            print(f"[‼️ Loud noise detected] Volume: {volume}")
            output = 1
            print(f"Output: {output}")
            filename = get_timestamped_filename()
            start_recording_loop(filename)
            return

    # After 30 seconds
    output = 0
    print("[🕒 30 seconds complete.]")
    print(f"Output: {output}")

if __name__ == "__main__":
    os.makedirs(AUDIO_SAVE_DIR, exist_ok=True)
    main()
