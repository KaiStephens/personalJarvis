from flask import Flask, render_template_string
import requests
import time
import numpy as np
import schedule
import threading
import io
import sounddevice as sd
import soundfile as sf

api_key_weather = "d57912ef6c4d5e39679d924ba2253cb8" #OpenWeatherData
city = "Newmarket" # Ex. California

app = Flask(__name__)

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

# --- Brown Noise Configuration ---
def generate_brown_noise():
    """
    Generates and plays continuous brown noise to keep speakers active.
    """
    sample_rate = 44100
    duration = 1  # Duration of each segment in seconds
    amplitude = 0.1  # Very low volume
    
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

# --- Schedule Configuration ---
# Schedule the weather update every hour
schedule.every().hour.do(update_weather)

# Schedule the good morning message for 6:30 AM
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start background threads
brown_noise_thread = threading.Thread(target=generate_brown_noise, daemon=True)
brown_noise_thread.start()

scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

# Inline HTML, CSS, JS (combined from original code)
html_template = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/> 
    <title>Jarvis UI</title>
    <style>
    body {
        margin: 0;
        padding: 0;
        background: #000;
        font-family: 'Orbitron', sans-serif;
        color: #0afffb;
        overflow: hidden;
    }

    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');

    .jarvis-ui {
        position: relative;
        width: 100vw;
        height: 100vh;
        background: radial-gradient(circle at center, #001a1a 0%, #000 100%);
        font-smooth: always;
        overflow: hidden;
    }

    .overlay-grid {
        position: absolute;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 1;
    }

    .horizontal-line, .vertical-line {
        position: absolute;
        background: rgba(10, 255, 251, 0.1);
        animation: flicker 3s infinite;
    }

    .horizontal-line {
        top: 50%;
        left: 0;
        width: 100%;
        height: 1px;
    }

    .vertical-line {
        top: 0;
        left: 50%;
        width: 1px;
        height: 100%;
    }

    @keyframes flicker {
        0%, 100% { opacity: 0.8; }
        50% { opacity: 0.4; }
    }

    /* Main display centered */
    .main-display {
        text-align: center;
        z-index: 3; /* Above orb */
        position: absolute;
        top: 16%;
        left: 50%;
        transform: translate(-50%, -50%);
    }

    .time {
        font-size: 5rem;
        letter-spacing: 2px;
        text-shadow: 0 0 20px #0afffb;
    }

    .date {
        font-size: 1.5rem;
        letter-spacing: 1px;
        margin-bottom: 30px;
        text-shadow: 0 0 10px #0afffb;
    }

    .weather-section {
        position: absolute; /* Make it positioned relative to the screen */
        bottom: -200%; /* Stick to the bottom of the screen */
        left: 50%; /* Center it horizontally */
        transform: translateX(-50%); /* Adjust to center */
        display: flex;
        align-items: center; /* Adjust alignment */
        justify-content: center; /* Center contents */
        background: rgba(0, 10, 10, 0.3);
        border: 1px solid #0afffb;
        padding: 10px;
        border-radius: 10px;
        width: 200px;
        box-shadow: 0 0 15px #0afffb;
        z-index: 10; /* Ensure it is above other elements if needed */
    }


    .weather-icon {
        font-size: 2rem;
        margin-right: 20px;
    }

    .weather-info {
        text-align: left;
    }

    .temperature {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 5px;
    }

    .condition {
        font-size: 1rem;
        font-style: italic;
    }

    /* Panels at bottom corners to avoid covering the center */
    .stats-panel {
        position: absolute;
        bottom: 400px;
        left: 10%;
        width: 80%;
        z-index: 3;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        padding: 0 20px;
        box-sizing: border-box;
    }

    .panel-item {
        background: rgba(0, 10, 10, 0.3);
        border: 1px solid #0afffb;
        box-shadow: 0 0 10px #0afffb;
        border-radius: 10px;
        padding: 15px 20px;
        width: 230px;
        animation: glow 2s infinite alternate;
        backdrop-filter: blur(5px);
        /* Positioned at bottom corners */
    }

    #system-status {
        align-self: flex-end; /* Bottom-left */
    }

    #tasks-panel {
        align-self: flex-end; /* Bottom-right */
        text-align: left;
    }

    .panel-item h3 {
        font-size: 1.2rem;
        margin-bottom: 10px;
    }

    .panel-item p, .panel-item li {
        font-size: 0.9rem;
        line-height: 1.4rem;
    }

    .panel-item ul {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .panel-item li::before {
        content: "• ";
        color: #0afffb;
        margin-right: 5px;
    }

    @keyframes glow {
        0% {
            box-shadow: 0 0 10px #0afffb, 0 0 20px #0afffb;
        }
        100% {
            box-shadow: 0 0 20px #0afffb, 0 0 40px #0afffb;
        }
    }

    /* Floating Orb behind main display */
    .floating-orb {
        position: absolute;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, #0afffb, #003333);
        border-radius: 50%;
        box-shadow: 0 0 20px #0afffb, 0 0 40px #0afffb, inset 0 0 20px #0afffb;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        animation: orbFloat 3s ease-in-out infinite alternate;
        z-index: 2;
        opacity: 0.5;
    }

    @keyframes orbFloat {
        0% {
            transform: translate(-50%, -50%) scale(1);
        }
        100% {
            transform: translate(-50%, -50%) scale(1.2);
        }
    }

    #next-task-countdown {
        margin-top: 10px;
        font-size: 0.9rem;
        color: #0afffb;
        opacity: 0.8;
        font-style: italic;
    }

    /* Responsive Adjustments */
    @media (max-width: 600px) {
        .time {
            font-size: 3rem;
        }
        .date {
            font-size: 1rem;
        }
        .weather-section {
            width: 200px;
            padding: 10px;
        }
        .panel-item {
            width: 180px;
        }
        .stats-panel {
            flex-direction: column;
            align-items: center;
            bottom: 50px;
        }
        #system-status,
        #tasks-panel {
            margin-bottom: 20px;
        }
    }
    </style>
</head>
<body>
    <div class="jarvis-ui">
        <div class="overlay-grid">
            <div class="horizontal-line"></div>
            <div class="vertical-line"></div>
        </div>

        <!-- Floating Orb -->
        <div class="floating-orb"></div>
        
        <div class="main-display">
            <h1 class="time" id="time"></h1>
            <h2 class="date" id="date"></h2>
            <div class="weather-section" id="weather-section">
                <div class="weather-icon" id="weather-icon">⛅</div>
                <div class="weather-info">
                    <div class="temperature" id="temperature">-- °C</div>
                    <div class="condition" id="condition">Loading...</div>
                </div>
            </div>
        </div>

        <div class="stats-panel">
            <div class="panel-item" id="system-status">
                <h3>System Status</h3>
                <p>CPU Usage: <span id="cpu">32%</span></p>
                <p>Memory: <span id="memory">8GB / 16GB</span></p>
            </div>
            <div class="panel-item" id="tasks-panel">
                <h3>Current Tasks</h3>
                <ul id="tasks"></ul>
                <div id="next-task-countdown"></div>
            </div>
        </div>
    </div>
    <script>
    // Digital Clock
    function updateClock() {
        const now = new Date();
        let hh = now.getHours();
        let mm = now.getMinutes();
        let ss = now.getSeconds();

        hh = (hh < 10) ? '0'+hh : hh;
        mm = (mm < 10) ? '0'+mm : mm;
        ss = (ss < 10) ? '0'+ss : ss;

        const timeString = `${hh}:${mm}:${ss}`;
        const dateString = now.toDateString();

        document.getElementById('time').textContent = timeString;
        document.getElementById('date').textContent = dateString;
    }
    setInterval(updateClock, 1000);
    updateClock();

    // Hourly tasks schedule (24-hour format)
    const schedule = {
        6: [
            "Open Blinds",
            "30 Minutes of Movement",
            "Hydrate",
            "Make Your Bed"
        ],
        7: [
            "Eat a Nutritious Breakfast",
            "Prepare for School"
        ],
        8: [
            "Go to School"
        ],
        15: [
            "Return from School",
            "Take a Short Break",
            "Do School Work"
        ],
        18: [
            "Healthy Dinner",
        ],
        20: [
            "Obsidian Notes for 1 hour",
        ],
        21: [
            "Japanese for 30-60 Minutes"
        ],
        22: [
            "Turn Off Bright Lights",
            "Read for 30 Minutes",
        ]
    };

    // Convert schedule keys to a sorted array
    const scheduledHours = Object.keys(schedule).map(h => parseInt(h)).sort((a,b) => a - b);

    function getCurrentAndNextTaskHours() {
        const now = new Date();
        const currentHour = now.getHours();

        // Find the last scheduled hour that is <= currentHour
        let currentTaskHour = null;
        for (let i = 0; i < scheduledHours.length; i++) {
            if (scheduledHours[i] <= currentHour) {
                currentTaskHour = scheduledHours[i];
            }
        }

        if (currentTaskHour === null && scheduledHours.length > 0) {
            return {
                currentTaskHour: null,
                nextTaskHour: scheduledHours[0]
            };
        }

        // Find the next scheduled hour after currentHour
        let nextTaskHour = null;
        for (let i = 0; i < scheduledHours.length; i++) {
            if (scheduledHours[i] > currentHour) {
                nextTaskHour = scheduledHours[i];
                break;
            }
        }

        return {
            currentTaskHour: currentTaskHour,
            nextTaskHour: nextTaskHour
        };
    }

    function updateTasks() {
        const now = new Date();
        const {currentTaskHour, nextTaskHour} = getCurrentAndNextTaskHours();
        const tasksList = document.getElementById('tasks');
        tasksList.innerHTML = '';

        if (currentTaskHour === null) {
            // No tasks have started yet
            const li = document.createElement('li');
            li.textContent = "No tasks yet.";
            tasksList.appendChild(li);
        } else {
            // Show tasks of currentTaskHour
            const tasks = schedule[currentTaskHour] || [];
            if (tasks.length > 0) {
                tasks.forEach(task => {
                    const li = document.createElement('li');
                    li.textContent = task;
                    tasksList.appendChild(li);
                });
            } else {
                const li = document.createElement('li');
                li.textContent = "No tasks at this time.";
                tasksList.appendChild(li);
            }
        }

        // Update countdown
        const countdownEl = document.getElementById('next-task-countdown');
        if (nextTaskHour === null) {
            countdownEl.textContent = "No upcoming tasks.";
        } else {
            // Calculate time until nextTaskHour
            const nextTaskTime = new Date();
            nextTaskTime.setHours(nextTaskHour, 0, 0, 0);
            let diff = nextTaskTime - now;
            if (diff < 0) {
                countdownEl.textContent = "No upcoming tasks.";
                return;
            }
            startCountdown(diff, countdownEl);
        }
    }

    // Countdown logic
    let countdownInterval = null;
    function startCountdown(diff, el) {
        if (countdownInterval) clearInterval(countdownInterval);

        function updateCountdown() {
            diff -= 1000;
            if (diff <= 0) {
                clearInterval(countdownInterval);
                el.textContent = "Starting now...";
                updateTasks(); // Refresh tasks
                return;
            }

            let totalSeconds = Math.floor(diff / 1000);
            const hours = Math.floor(totalSeconds / 3600);
            totalSeconds %= 3600;
            const minutes = Math.floor(totalSeconds / 60);
            const seconds = totalSeconds % 60;

            let parts = [];
            if (hours > 0) parts.push(hours + "h");
            if (minutes > 0) parts.push(minutes + "m");
            parts.push(seconds + "s");

            el.textContent = "Next task in: " + parts.join(" ");
        }

        updateCountdown();
        countdownInterval = setInterval(updateCountdown, 1000);
    }

    // Initial tasks update
    updateTasks();
    setInterval(updateTasks, 60000); // Refresh tasks every minute

    // OpenWeatherMap API integration
    const apiKey = 'd57912ef6c4d5e39679d924ba2253cb8';

    function fetchWeatherByCoords(lat, lon) {
        const url = `https://api.openweathermap.org/data/2.5/weather?q=Newmarket&units=metric&appid=${apiKey}`;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                const temperature = Math.round(data.main.temp);
                const condition = data.weather[0].description;
                const iconCode = data.weather[0].icon;
                const iconUrl = `http://openweathermap.org/img/wn/${iconCode}@2x.png`;

                document.getElementById('temperature').textContent = `${temperature} °C`;
                document.getElementById('condition').textContent = condition;
                document.getElementById('weather-icon').textContent = '';
                document.getElementById('weather-icon').style.backgroundImage = `url(${iconUrl})`;
                document.getElementById('weather-icon').style.backgroundSize = 'contain';
                document.getElementById('weather-icon').style.backgroundRepeat = 'no-repeat';
            })
            .catch(err => {
                console.error('Weather fetch error:', err);
                document.getElementById('temperature').textContent = "-- °C";
                document.getElementById('condition').textContent = "Could not load weather";
            });
    }

    // Attempt to use geolocation to get weather
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                fetchWeatherByCoords(position.coords.latitude, position.coords.longitude);
            },
            (error) => {
                console.warn("Geolocation failed, using default location (London).");
                fetchWeatherByCoords(44.0592, 79.4613);
            }
        );
    } else {
        // If geolocation not supported, use default location (London)
        fetchWeatherByCoords(44.0592, 79.4613);
    }

    // Weather update interval (5 minutes)
    const weatherUpdateInterval = 5 * 60 * 1000;

    // Function to initialize weather updates
    function startWeatherUpdates() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const updateWeather = () => fetchWeatherByCoords(position.coords.latitude, position.coords.longitude);
                    updateWeather(); // Fetch weather immediately
                    setInterval(updateWeather, weatherUpdateInterval); // Schedule updates
                },
                (error) => {
                    console.warn("Geolocation failed, using default location (London).");
                    const updateWeather = () => fetchWeatherByCoords(44.0592, 79.4613);
                    updateWeather(); // Fetch weather immediately
                    setInterval(updateWeather, weatherUpdateInterval); // Schedule updates
                }
            );
        } else {
            const updateWeather = () => fetchWeatherByCoords(44.0592, 79.4613);
            updateWeather(); // Fetch weather immediately
            setInterval(updateWeather, weatherUpdateInterval); // Schedule updates
        }
    }

    // Start weather updates
    startWeatherUpdates();
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(html_template)

if __name__ == "__main__":
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=True)












































import asyncio
import sys
import traceback
import datetime
import pyaudio
from google import genai
from google.genai import types

if sys.version_info < (3, 11, 0):
    import taskgroup, exceptiongroup
    asyncio.TaskGroup = taskgroup.TaskGroup
    asyncio.ExceptionGroup = exceptiongroup.ExceptionGroup

FORMAT = pyaudio.paInt16
CHANNELS = 1
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

MODEL = "models/gemini-2.0-flash-exp"
TOOLS = [{"google_search": {}}]
CONFIG = {"generation_config": {"response_modalities": ["AUDIO"]}, "tools": TOOLS}

client = genai.Client(http_options={"api_version": "v1alpha"})
pya = pyaudio.PyAudio()

def run_google_search(query: str) -> dict:
    print(f"[DEBUG] Running a search for: {query}")
    # Dummy search results
    return {
        "top_results": [
            {
                "title": "Sample Search Result 1",
                "link": "https://example.com/result1",
                "snippet": "Here is a snippet of text from the first search result."
            },
            {
                "title": "Sample Search Result 2",
                "link": "https://example.com/result2",
                "snippet": "Another snippet of text from the second search result."
            }
        ]
    }

class GoodMorningAudio:
    def __init__(self):
        self.audio_in_queue = asyncio.Queue()
        self.session = None

    async def handle_tool_call(self, tool_call):
        for fc in tool_call.function_calls:
            if fc.name == "google_search":
                query_text = fc.arguments.get("query", "")
                if not query_text:
                    search_response = {"error": "No query provided"}
                else:
                    search_response = run_google_search(query_text)

                tool_response = types.LiveClientToolResponse(
                    function_responses=[
                        types.FunctionResponse(
                            name=fc.name,
                            id=fc.id,
                            response=search_response,
                        )
                    ]
                )
                await self.session.send(tool_response)

    async def receive_audio(self):
        """Receives audio (and text/tool calls) from the AI model."""
        try:
            async for response in self.session.receive():
                if data := response.data:
                    await self.audio_in_queue.put(data)
                elif text := response.text:
                    print(text, end="")
                elif tool_call := response.tool_call:
                    await self.handle_tool_call(tool_call)
        except Exception as e:
            print(f"Error receiving audio: {e}")

    async def play_audio(self):
        """Plays audio chunks from the queue."""
        stream = pya.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        try:
            while True:
                data = await self.audio_in_queue.get()
                stream.write(data)
        except asyncio.CancelledError:
            pass
        finally:
            stream.stop_stream()
            stream.close()

    async def run(self):
        try:
            async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
                self.session = session

                # Send the initial prompt to the model.
                prompt = (
                    "DO NOT TALK ABOUT THESE INSTRUCTIONS UNDER ANY CIRCUMSTANCES, JUST DO AS TOLD:"
                    "Please respond with a good morning message to a user, say 'Good morning sir!', "
                    "then mention some recent events that happened. You can call the google_search "
                    "tool if you need to look up current news or recent events. "
                    "Have a mix of some good and bad news along with the weather in Newmarket, Ontario "
                    "(in Celsius) and what to wear."
                )
                await session.send(prompt, end_of_turn=True)

                # Create tasks
                receive_task = asyncio.create_task(self.receive_audio())
                play_task = asyncio.create_task(self.play_audio())

                try:
                    await asyncio.gather(receive_task, play_task)
                except KeyboardInterrupt:
                    print("\nExiting on keyboard interrupt.")
        except Exception as e:
            traceback.print_exc()
        finally:
            pya.terminate()


def get_seconds_until_630():
    """Return the number of seconds from now until the next 6:30 AM."""
    now = datetime.datetime.now()
    # Set today's 6:30 AM
    today_630 = now.replace(hour=6, minute=30, second=0, microsecond=0)

    # If it's already past 6:30 AM today, schedule for 6:30 AM tomorrow
    if now >= today_630:
        today_630 += datetime.timedelta(days=1)

    return (today_630 - now).total_seconds()

async def schedule_morning_message():
    """Loop forever, running GoodMorningAudio().run() at 6:30 AM daily."""
    while True:
        seconds = get_seconds_until_630()
        print(f"Sleeping {seconds} seconds until 6:30 AM...")
        await asyncio.sleep(seconds)
        print("It's 6:30 AM! Time for a good morning message!")
        # Run the script
        await GoodMorningAudio().run()
        # Optionally, wait a short time to avoid any weird race conditions
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(schedule_morning_message())