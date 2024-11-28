import speech_recognition as sr
import threading
import queue
import time
import ollama
import json
import os
from datetime import datetime
import pyttsx3
import requests
import numpy as np
import sounddevice as sd
import schedule
import io
import sounddevice as sd
import soundfile as sf
from apiKeys import api_key_weather, api_key_elevenlabs, city

weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key_weather}&units=metric"

weather_data = {"description": "unknown", "temp": 0.0}

def update_weather():
    """Fetches the current weather from OpenWeatherMap API."""
    try:
        res = requests.get(weather_url)
        data = res.json()
        weather_data["description"] = data['weather'][0]['description']
        weather_data["temp"] = data['main']['temp']
        print(f"Weather updated: {weather_data['temp']}°C, {weather_data['description']}")
    except Exception as e:
        print(f"Failed to fetch weather data: {e}")

update_weather()

elevenlabs_url = "https://api.elevenlabs.io/v1/text-to-speech/JBFqnCBsd6RMkjVDRZzb"

def generate_audio(text):
    """Uses ElevenLabs API to convert text to speech and play it directly."""
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key_elevenlabs
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }

    try:
        response = requests.post(elevenlabs_url, json=data, headers=headers)
        response.raise_for_status()

        audio_data = io.BytesIO(response.content)
        
        with sf.SoundFile(audio_data) as audio_file:
            audio_data.seek(0)
            sd.play(audio_file.read(dtype="float32"), samplerate=audio_file.samplerate)
            sd.wait() 
        
        print("Audio played successfully.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# Only if using a bluetooth speaker that disconnects
def generate_brown_noise():
    """
    Generates and plays continuous brown noise to keep speakers active.
    """
    sample_rate = 44100
    duration = 1  
    amplitude = 0.02 
    
    size = sample_rate * duration
    random_numbers = np.cumsum(np.random.normal(0, 1, size))  
    brown_noise = amplitude * (random_numbers / max(abs(random_numbers))) 
    
    stereo_data = np.column_stack((brown_noise, brown_noise)).astype(np.float32) 
    
    with sd.OutputStream(samplerate=sample_rate, channels=2, dtype=np.float32) as stream:
        while True:
            stream.write(stereo_data)

def say_good_morning():
    """Generates and plays 'Good morning' audio with weather information."""
    text = "Good morning, sir. All systems are operational. Monitor and lights turning on. "
    text += f"The temperature is {weather_data['temp']}°C, and the weather is currently {weather_data['description']}."
    generate_audio(text)
    print("Good morning message generated.")

schedule.every().hour.do(update_weather)
schedule.every().day.at("06:30").do(say_good_morning)

brown_noise_thread = threading.Thread(target=generate_brown_noise, daemon=True)
brown_noise_thread.start()

class ChatSession:
    def __init__(self, history_file='chat_history.json'):
        self.history_file = history_file
        self.history = self.load_history()
        
    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    print(f"\nLoaded {len(history)} messages from history")
                    return history
        except Exception as e:
            print(f"\nWarning: Could not load chat history: {str(e)}")
        return []

    def save_history(self):
        try:
            directory = os.path.dirname(os.path.abspath(self.history_file))
            os.makedirs(directory, exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            print(f"\nWarning: Could not save chat history: {str(e)}")
            
    def get_single_response(self, context=None, model='llama3.2:3b'):
        special_instruction = (
            "You are Jarvis, an advanced AI assistant modeled after the AI from Iron Man. "
            "Respond with a single, concise sentence. Speak with a highly intelligent, formal, "
            "and respectful tone. Use a subtle touch of wit. Address the user as 'Sir' if possible."
        )
        messages = [{'role': 'system', 'content': special_instruction}]
        if context:
            messages.append({'role': 'user', 'content': context})
        response = ollama.chat(model=model, messages=messages)
        full_response = response['message']['content']
        if context:
            timestamp = datetime.now().isoformat()
            self.history.append({'timestamp': timestamp, 'role': 'user', 'content': context})
            self.history.append({'timestamp': datetime.now().isoformat(), 'role': 'assistant', 'content': full_response})
            self.save_history()
        return full_response


def generate_audio(text):
    engine = pyttsx3.init()

    voices = engine.getProperty('voices')

    for voice in voices:
        if "en_GB" in voice.id:
            engine.setProperty('voice', voice.id)
            print(f"Using voice: {voice.name} ({voice.id})")
            break
    else:
        print("en_GB voice not found. Using default voice.")

    engine.setProperty('rate', 200)
    engine.setProperty('volume', 1.0)  
    engine.say(text)

    engine.runAndWait()

class WakeWordDetector:
    def __init__(self, wake_word="jarvis", sensitivity=0.8):
        self.wake_word = wake_word.lower()
        self.sensitivity = sensitivity
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.stop_listening = False
        self.audio_queue = queue.Queue()
        self.chat_session = ChatSession()

    def _calculate_similarity(self, input_text):
        input_text = input_text.lower()
        wake_words = self.wake_word.split()
        input_words = input_text.split()
        matching_words = [word for word in wake_words if word in input_words]
        similarity = len(matching_words) / len(wake_words)
        return similarity

    def _listen_for_wake_word(self):
        while not self.stop_listening:
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=3)
                self.audio_queue.put(audio)
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                print(f"Error in listening: {e}")
                time.sleep(1)

    def _process_audio_queue(self):
        while not self.stop_listening:
            try:
                audio = self.audio_queue.get(timeout=1)
                try:
                    time.sleep(1)
                    text = self.recognizer.recognize_google(audio).lower()
                    print(f"Heard: {text}")
                    similarity = self._calculate_similarity(text)
                    if similarity >= self.sensitivity:
                        print(f"Wake word detected! (Similarity: {similarity:.2f})")
                        response = self.chat_session.get_single_response(context=text)
                        print(f"Jarvis: {response}")
                        generate_audio(response)
                except sr.UnknownValueError:
                    pass
                except sr.RequestError:
                    print("Could not request results from speech recognition service")
            except queue.Empty:
                continue

    def start(self):
        self.stop_listening = False
        self.listener_thread = threading.Thread(target=self._listen_for_wake_word, daemon=True)
        self.listener_thread.start()
        self.processor_thread = threading.Thread(target=self._process_audio_queue, daemon=True)
        self.processor_thread.start()

    def stop(self):
        self.stop_listening = True
        if self.listener_thread:
            self.listener_thread.join()
        if hasattr(self, 'processor_thread'):
            self.processor_thread.join()

def main():
    print("Initializing Jarvis Wake Word Detection...")
    detector = WakeWordDetector(wake_word="jarvis", sensitivity=0.7)
    try:
        detector.start()
        print("Jarvis is now listening. Say 'Jarvis' to activate.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Jarvis wake word detection...")
        detector.stop()

if __name__ == "__main__":
    main()