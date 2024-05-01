import asyncio
import websockets
import json
from mimetypes import guess_type
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from prompt_utils import get_gpt4_prompt_from_messages
from tts_utils import tts_async

load_dotenv()
llm = ChatOpenAI(
    model="gpt-4-turbo",
    api_key=os.getenv("API_KEY"),
    temperature=0.2,
    top_p=0.1,
    # top_k=50,
    max_tokens=1000,
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()],
)

async def a_call_llm(websocket, data):
    # print("Calling LLM with base64 data URL:", data['messages'][1]['content'][1]['image']['url'])
    
    # prompt = [
    #     HumanMessage(content=[
    #         {"type": "text", "text": "Let's play a game. Think of a country and give me a clue. The clue must be specific enough that there is only one correct country. I will try pointing at the country on a map."},
    #     ]),
    #     SystemMessage(content=[{"type": "text", "text": "Alright, here's your clue: This country is renowned for being the birthplace of both the ancient Olympic Games and democracy. Where would you point on the map?"}]),
    #     # HumanMessage(content=[
    #     #     {"type": "text", "text": "Is it Greece?"},
    #     # ]),
    #     HumanMessage(content=[
    #         {"type": "image_url", "image_url": { "url" : data['messages'][1]['content'][1]['image']['url']} },
    #     ])
    # ]

    prompt = get_gpt4_prompt_from_messages(data)
    command = ""
    all_chunks = ""
    buffer = ""
    text = ""
    capturing_response = False
    capturing_command = False
    at_least_one_chunk_has_been_sent = False

    # return

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

    # import threading
    #  no speak
    # threading.Thread(target=tts_async, args=(text,)).start()


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
