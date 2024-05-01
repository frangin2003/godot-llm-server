import asyncio
import websockets
import json
from langchain_community.llms import Ollama
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
from prompt_utils import get_llama3_prompt_from_messages

llm = Ollama(
    model="llama3",
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
    verbose=True,
    # stop=["\n", "<|im_end|>"],
    stop=["<|eot_id|>"],
)

import win32com.client

# Global initialization of COM and speech object
global_speaker = win32com.client.Dispatch("SAPI.SpVoice")

# Simulated LLM function
async def a_call_llm(websocket, data):
    # print("Calling LLM with data:", data)
    
    prompt = get_llama3_prompt_from_messages(data, True)
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

    # import threading
    #  no speak
    # threading.Thread(target=tts_async, args=(text,)).start()

    if not at_least_one_chunk_has_been_sent:
        await websocket.send(all_chunks)

    print(f'FINAL command=|{command}|')
    if command:
        await websocket.send(f"<|command|>{command}")

    await websocket.send("<|end_of_text|>")

async def websocket_handler(websocket, path):
    async for message in websocket:
        data = json.loads(message)
        await a_call_llm(websocket, data)

start_server = websockets.serve(websocket_handler, "localhost", 8765)
print("llm-server ready!")

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
