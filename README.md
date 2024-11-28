# Jarvis AI Assistant

Jarvis is an advanced AI assistant designed for seamless voice interaction, incorporating wake word detection, text-to-speech capabilities, weather updates, and intelligent chat functionality. This repository contains the Python implementation of Jarvis, combining multiple APIs and libraries to create a versatile and interactive assistant.

---

## Features

###  Core Functionality
- **Wake Word Detection**:  
   Listens for the wake word ("Jarvis") and activates upon detection.
- **Speech Recognition**:  
   Converts spoken audio into text using Google Speech Recognition.
- **Intelligent Responses**:  
   Engages in conversation with a formal and witty tone using a conversational AI model.

###  Text-to-Speech (TTS)
- **ElevenLabs API**:  
   Provides realistic TTS playback.  
- **Fallback**:  
   Uses `pyttsx3` for offline speech synthesis.

###  Real-Time Weather Updates
Fetches real-time weather information from OpenWeatherMap API and integrates it into conversations and scheduled tasks.

### Scheduled Tasks
- **Hourly Weather Updates**:  
   Keeps you informed with the latest weather data.
- **Daily Good Morning Message**:  
   Provides a morning summary with weather updates and system status.

### Continuous Brown Noise
Generates and plays brown noise to keep Bluetooth speakers or audio devices active.

---

## Installation

### Prerequisites
- Python 3.8 or higher
- [API Keys](#configuration)
- Required Python Libraries:  
  Install all dependencies by running:
  ```bash
  pip install -r requirements.txt
