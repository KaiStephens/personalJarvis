import asyncio
import sys
import traceback
import pyaudio
from accessKey import weather_city
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
pya_instance = pyaudio.PyAudio()

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
        finally:
            await self.audio_in_queue.put(None)

    async def play_audio(self):
        stream = pya_instance.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        try:
            while True:
                data = await self.audio_in_queue.get()
                if data is None:
                    break
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

                prompt = (
                    "Please respond with a good morning message to a user, say 'Good morning sir!', "
                    "then mention some recent events in the world of techonology and stocks. You can call the google_search tool if you need "
                    "to look up current news or recent events."
                    f"Talk about the weather in {weather_city} and what to wear for the day"
                )
                await session.send(prompt, end_of_turn=True)

                receive_task = asyncio.create_task(self.receive_audio())
                play_task = asyncio.create_task(self.play_audio())

                await asyncio.gather(receive_task, play_task)
        except Exception as e:
            traceback.print_exc()
        finally:
            pya_instance.terminate()

def start():
    if __name__ == "__main__":
        try:
            asyncio.run(GoodMorningAudio().run())
        except KeyboardInterrupt:
            print("\nProgram interrupted by user. Exiting...")

start()