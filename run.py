import asyncio
import websockets
import json
from dotenv import load_dotenv
from tts_utils import tts_async
from llm_utils import create_llm_instance

load_dotenv()
import sys

if len(sys.argv) < 2:
    raise ValueError("Model name must be provided as a command-line argument")

model_name = sys.argv[1]
llm_instance = create_llm_instance(model_name, debug=False)

# Global initialization of COM and speech object
import win32com.client
global_speaker = win32com.client.Dispatch("SAPI.SpVoice")
global_speaker.Voice = global_speaker.GetVoices().Item(0)

async def a_call_llm(websocket, data):

    prompt = llm_instance.get_prompt_from_messages(data)
    all_chunks = ""
    buffer = ""
 
    capturing_speaker = False
    speaker = ""
    capturing_text = False
    at_least_one_chunk_has_been_sent = False
    text = ""
    capturing_command = False
    command = ""
 
    await websocket.send("<|begin_of_text|>")
    await asyncio.sleep(0)
    for chunk in llm_instance.llm._stream(prompt):
        chunk_text = chunk.text
        print(chunk_text)
        # Clean and manage the buffer
        chunk_text = chunk_text.replace('","', '').replace(',"', '').replace('",', '').replace('"', '').replace('{', '').replace('}', '').replace(':', '').replace('=', '').replace('```', '')
        all_chunks += chunk_text
 
        buffer += chunk_text
        if (chunk_text.strip() == "_"
            and buffer != "_speaker" and buffer != "_text" and buffer != "_command"):
            buffer = "_"
            continue

        if buffer == "_speaker":
            capturing_speaker = True
            buffer = ""  # Reset buffer after detecting keyword
            continue
        elif buffer == "_text":
            capturing_speaker = False
            capturing_text = True
            buffer = ""  # Reset buffer after detecting keyword
            continue
        elif buffer == "_command":
            capturing_text = False
            capturing_command = True
            buffer = ""  # Reset buffer after detecting keyword
            continue

        # Accumulate content into the response or command based on the current state
        if capturing_speaker:
            speaker += chunk_text
        elif capturing_text:
            at_least_one_chunk_has_been_sent = True
            text += chunk_text
            await websocket.send(chunk_text)
            await asyncio.sleep(0)
        elif capturing_command:
            command += chunk_text

    if not at_least_one_chunk_has_been_sent:
        await websocket.send(all_chunks)
        await asyncio.sleep(0)

    print(all_chunks)

    import threading
    threading.Thread(target=tts_async, args=(global_speaker, text,)).start()

    print(f'FINAL command=|{command}|')
    if command:
        await websocket.send(f"<|command|>{command}")
        await asyncio.sleep(0)

    await websocket.send("<|end_of_text|>")
    await asyncio.sleep(0)

async def websocket_handler(websocket, path):
    async for message in websocket:
        data = json.loads(message)
        print(json.dumps(data, indent=4))
        await a_call_llm(websocket, data)

start_server = websockets.serve(websocket_handler, "localhost", 8765)
print("llm-server ready!")

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
