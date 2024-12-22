import asyncio
import base64
import io
import os
import sys
import traceback
import cv2
import pyaudio
import PIL.Image
import mss
import logging
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--mode",
    type=str,
    default="",
    help="pixels to stream from",
    choices=["camera", "screen"],
)

args = parser.parse_args()

logger = logging.getLogger('Live')
logger.setLevel('INFO') 

from google import genai
from google.genai import types

client = genai.Client(http_options={"api_version": "v1alpha"})

import pvporcupine
from pvrecorder import PvRecorder

current_dir = os.path.dirname(os.path.abspath(__file__))

script_path = os.path.join(current_dir, "jarvis.ppn")

from accessKey import pvporcupine_access_key


ACCESS_KEY = pvporcupine_access_key
KEYWORD_PATH = script_path

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

MODEL = "models/gemini-2.0-flash-exp"
MODE = args.mode

search_tool = {'google_search': {}}
shutdown_function = {'name': 'shutdown'}

tools = [
    search_tool,
    {'function_declarations': [shutdown_function]}
]

CONFIG = {
    "generation_config": {
        "response_modalities": ["AUDIO"]
    },
    "tools": tools
}

shutdown_event = asyncio.Event()

def shutdown():
    print("Shutdown function called. Terminating the session...")
    shutdown_event.set()

if sys.version_info < (3, 11, 0):
    import taskgroup
    import exceptiongroup
    asyncio.TaskGroup = taskgroup.TaskGroup
    asyncio.ExceptionGroup = exceptiongroup.ExceptionGroup

PRE_PROMPT = (
    "You are Jarvis, the AI assistant from Iron Man. "
    "Your task is to assist the user with any requests in a helpful, intelligent, and efficient manner."
    "When the conversation is finished, run the shutdown function. If the user has nothing else to say, run the shutdown function. If the user states that is all they need, run the shutdown function"
)

class AudioLoop:
    def __init__(self, pya_inst):
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        self.audio_stream = None
        self.pya = pya_inst
        self.model_speaking = False

    async def send_text(self):
        while True:
            text = await asyncio.to_thread(input, "message > ")
            if text.lower() == "q":
                print("Ending session from console input...")
                raise asyncio.CancelledError
            await self.session.send(text or ".", end_of_turn=True)

    def _get_frame(self, cap):
        ret, frame = cap.read()
        if not ret:
            return None
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)
        img.thumbnail([1024, 1024])

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        mime_type = "image/jpeg"
        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    async def get_frames(self):
        cap = await asyncio.to_thread(cv2.VideoCapture, 0)
        while True:
            frame = await asyncio.to_thread(self._get_frame, cap)
            if frame is None:
                break
            await asyncio.sleep(1.0)
            await self.out_queue.put(frame)
        cap.release()

    def _get_screen_capture(self):
        sct = mss.mss()
        monitor = sct.monitors[0]

        i = sct.grab(monitor)
        mime_type = "image/jpeg"
        image_bytes = mss.tools.to_png(i.rgb, i.size)
        img = PIL.Image.open(io.BytesIO(image_bytes))

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    async def get_screen(self):
        while True:
            frame = await asyncio.to_thread(self._get_screen_capture)
            if frame is None:
                break
            await asyncio.sleep(1.0)
            await self.out_queue.put(frame)

    async def send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send(msg)

    async def handle_tool_call(self, tool_call):
        for fc in tool_call.function_calls:
            if fc.name == 'shutdown':
                print("Received shutdown command from the model.")
                shutdown()
                tool_response = types.LiveClientToolResponse(
                    function_responses=[types.FunctionResponse(
                        name='shutdown',
                        id=fc.id,
                        response={'result': 'shutting down'},
                    )]
                )
                await self.session.send(tool_response)
            else:
                tool_response = types.LiveClientToolResponse(
                    function_responses=[types.FunctionResponse(
                        name=fc.name,
                        id=fc.id,
                        response={'result': 'ok'},
                    )]
                )
                await self.session.send(tool_response)

    async def receive_audio(self):
        while True:
            turn = self.session.receive()
            async for response in turn:
                if data := response.data:
                    self.model_speaking = True
                    self.audio_in_queue.put_nowait(data)
                elif text := response.text:
                    print(text, end="")
                elif tool_call := response.tool_call:
                    await self.handle_tool_call(tool_call)

            while not self.audio_in_queue.empty():
                self.audio_in_queue.get_nowait()

    async def play_audio(self):
        stream = await asyncio.to_thread(
            self.pya.open, 
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        while True:
            bytestream = await self.audio_in_queue.get()
            await asyncio.to_thread(stream.write, bytestream)

            if self.audio_in_queue.empty():
                self.model_speaking = False

    async def listen_audio(self):

        mic_info = await asyncio.to_thread(self.pya.get_default_input_device_info)
        self.audio_stream = await asyncio.to_thread(
            self.pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )

        if __debug__:
            kwargs = {"exception_on_overflow": False}
        else:
            kwargs = {}

        while True:
            if self.model_speaking:
                await asyncio.sleep(0.01)
                continue

            data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
            await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})

    async def run(self):
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                await self.session.send(PRE_PROMPT, end_of_turn=True)
                
                await self.session.send("Hello! How can I assist you today?", end_of_turn=True)

                # Start tasks
                tg.create_task(self.listen_audio())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())
                tg.create_task(self.send_realtime())

                if MODE == "camera":
                    tg.create_task(self.get_frames())
                elif MODE == "screen":
                    tg.create_task(self.get_screen())

                done, pending = await asyncio.wait(
                    [asyncio.create_task(shutdown_event.wait())],
                    return_when=asyncio.FIRST_COMPLETED
                )
                for task in pending:
                    task.cancel()

                if shutdown_event.is_set():
                    print("Shutdown event detected. Terminating the session...")
                    raise asyncio.CancelledError("Shutdown requested by user.")

        except asyncio.CancelledError:
            pass
        except ExceptionGroup as EG:
            traceback.print_exception(EG)
        finally:
            if self.audio_stream:
                self.audio_stream.close()

async def main():
    pya_instance = pyaudio.PyAudio()

    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keyword_paths=[KEYWORD_PATH]
    )
    recorder = PvRecorder(device_index=0, frame_length=porcupine.frame_length)
    recorder.start()
    print("Porcupine listener started. Say your wake word...")

    try:
        while True:
            shutdown_event.clear() 

            while True:
                pcm = recorder.read()
                result = porcupine.process(pcm)
                if result >= 0:
                    print("Wake word detected!")
                    break

            print("Starting real-time chat session...")
            session = AudioLoop(pya_instance)
            try:
                await session.run()
            except asyncio.CancelledError:
                print("Real-time session ended.\n")
                if shutdown_event.is_set():
                    print("Shutdown initiated. Exiting the main loop.")
                    break  

            print("Returning to wake-word detection...")
            print("Porcupine listener started. Say your wake word...")

    finally:
        recorder.stop()
        recorder.delete()
        porcupine.delete()
        pya_instance.terminate()

if __name__ == "__main__":
    try:
        if 'GOOGLE_API_KEY' not in os.environ:
            print("Error: GOOGLE_API_KEY environment variable not set.")
            sys.exit(1)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("User interrupted. Exiting...")