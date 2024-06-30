import asyncio
import websockets
import json
from mimetypes import guess_type
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from tts_utils import tts_async

load_dotenv()
llm = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("API_KEY"),
    temperature=0.0,
    model_kwargs={"top_p":0.1},
    max_tokens=1000,
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()],
)

# Global initialization of COM and speech object
import win32com.client
global_speaker = win32com.client.Dispatch("SAPI.SpVoice")
global_speaker.Voice = global_speaker.GetVoices().Item(0)

async def a_call_llm(websocket, data):

    prompt = get_gpt4_prompt_from_messages(data)
    command = ""
    all_chunks = ""
    buffer = ""
    text = ""
    capturing_response = False
    capturing_command = False
    at_least_one_chunk_has_been_sent = False

    await websocket.send("<|begin_of_text|>")
    for chunk in llm._stream(prompt):
        chunk_text = chunk.text
        # print(chunk_text)

        # Clean and manage the buffer
        chunk_text = chunk_text.replace('","', '').replace(',"', '').replace('",', '').replace('"', '').replace('{', '').replace('}', '').replace(':', '').replace('=', '').replace('```', '')
        all_chunks += chunk_text

        buffer += chunk_text
        if (chunk_text.strip() == "_"
            and buffer != "_text" and buffer != "_command"
            and buffer != "_text_" and buffer != "_command_"):
            buffer = "_"
            continue

        if (buffer == "_text" or buffer == "_command"):
            continue

        # Check and transition based on keywords
        if buffer == "_text_":
            capturing_response = True
            buffer = ""  # Reset buffer after detecting keyword
            continue

        elif buffer == "_command_":
            capturing_response = False
            capturing_command = True
            buffer = ""  # Reset buffer after detecting keyword
            continue

        # Accumulate content into the response or command based on the current state
        if capturing_response:
            at_least_one_chunk_has_been_sent = True
            text += chunk_text
            print(chunk_text)
            await websocket.send(chunk_text)
        elif capturing_command:
            command += chunk_text

    if not at_least_one_chunk_has_been_sent:
        await websocket.send(all_chunks)

    print(all_chunks)

    import threading
    threading.Thread(target=tts_async, args=(global_speaker, text,)).start()

    print(f'FINAL command=|{command}|')
    if command:
        await websocket.send(f"<|command|>{command}")

    await websocket.send("<|end_of_text|>")

async def websocket_handler(websocket, path):
    async for message in websocket:
        data = json.loads(message)
        print(json.dumps(data, indent=4))
        await a_call_llm(websocket, data)

start_server = websockets.serve(websocket_handler, "localhost", 8765)
print("llm-server ready!")

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
