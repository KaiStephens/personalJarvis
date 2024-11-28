import requests
import time
import numpy as np
import sounddevice as sd
import schedule
import threading
import io
import sounddevice as sd
import soundfile as sf
from apiKeys import api_key_weather, api_key_elevenlabs

# --- OpenWeatherMap Configuration ---
city = "Newmarket"
weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key_weather}&units=metric"

# Shared weather data
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

# Initial weather update
update_weather()

# --- ElevenLabs TTS Configuration ---
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

        # Read the audio content into a buffer
        audio_data = io.BytesIO(response.content)
        
        # Play the audio using sounddevice and soundfile
        with sf.SoundFile(audio_data) as audio_file:
            audio_data.seek(0)  # Reset the buffer to the beginning
            sd.play(audio_file.read(dtype="float32"), samplerate=audio_file.samplerate)
            sd.wait()  # Wait for playback to finish
        
        print("Audio played successfully.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# --- Brown Noise Configuration ---
def generate_brown_noise():
    """
    Generates and plays continuous brown noise to keep speakers active.
    """
    sample_rate = 44100
    duration = 1  # Duration of each segment in seconds
    amplitude = 0.02  # Very low volume
    
    # Generate Brown noise
    size = sample_rate * duration
    random_numbers = np.cumsum(np.random.normal(0, 1, size))  # Cumulative sum of Gaussian noise
    brown_noise = amplitude * (random_numbers / max(abs(random_numbers)))  # Normalize and scale
    
    # Convert to stereo
    stereo_data = np.column_stack((brown_noise, brown_noise)).astype(np.float32)  # Convert to float32
    
    # Start continuous playback
    with sd.OutputStream(samplerate=sample_rate, channels=2, dtype=np.float32) as stream:
        while True:
            stream.write(stereo_data)

# --- Scheduled Task ---
def say_good_morning():
    """Generates and plays 'Good morning' audio with weather information."""
    text = "Good morning, sir. All systems are operational. Monitor and lights turning on. "
    text += f"The temperature is {weather_data['temp']}°C, and the weather is currently {weather_data['description']}."
    generate_audio(text)
    print("Good morning message generated.")
say_good_morning()
# --- Schedule Configuration ---
# Schedule the weather update every hour
schedule.every().hour.do(update_weather)

# Schedule the good morning message for 6:30 AM
schedule.every().day.at("06:30").do(say_good_morning)

# Start the brown noise in a separate thread
brown_noise_thread = threading.Thread(target=generate_brown_noise, daemon=True)
brown_noise_thread.start()

print("The script is running. It will say 'Good morning' at 6:30 AM.")
print("Brown noise is playing to keep speakers active.")

# Keep the script running to check the schedule
try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping the script...")
