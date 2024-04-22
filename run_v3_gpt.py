import asyncio
import websockets
import json
import base64
from mimetypes import guess_type
import speech_recognition as sr
import wave
import pyaudio
from io import BytesIO
from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import StreamingStdOutCallbackHandler
import win32com.client

import torch
print(torch.cuda.is_available())

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
import os

load_dotenv()
llm = ChatOpenAI(model="gpt-4-turbo", api_key=os.getenv("API_KEY"), streaming=True, callbacks=[StreamingStdOutCallbackHandler()],)

def play_audio(base64_voice):
    try:
        # Decode the base64 string
        audio_data = base64.b64decode(base64_voice)
        
        # Write the binary data to a buffer
        buffer = BytesIO(audio_data)
        buffer.seek(0)
        
        # Use wave to open the buffer
        with wave.open(buffer, 'rb') as wf:
            p = pyaudio.PyAudio()
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getchannels(),
                            rate=wf.getframerate(),
                            output=True)

            # Read data in chunks
            data = wf.readframes(1024)
            while data:
                stream.write(data)
                data = wf.readframes(1024)

            # Stop and close the stream and PyAudio
            stream.stop_stream()
            stream.close()
            p.terminate()
    except wave.Error as e:
        print(f"Error: {e}. The file may not be a valid WAV file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Function to recognize speech from base64 audio data
def recognize_speech_from_base64(base64_voice):
    audio_data = base64.b64decode(base64_voice)
    recognize_speech_from_audio_data(audio_data)

# Function to recognize speech from audio binary data
def recognize_speech_from_audio_url(audio_url):
    with open(audio_url, 'rb') as audio_file:
        audio_data = audio_file.read()
    recognize_speech_from_audio_data(audio_data)

# Function to recognize speech from audio binary data
def recognize_speech_from_audio_data(audio_data):
    audio_file = BytesIO(audio_data)
    r = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)  # read the entire audio file
    try:
        # for testing purposes, we're using the default API key
        # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Google Speech Recognition could not understand audio"
    except sr.RequestError as e:
        return f"Could not request results from Google Speech Recognition service; {e}"

import base64

# Function to convert base64 image data to data URL
def base64_to_data_url(base64_image, mime_type='image/png'):
    return f"data:{mime_type};base64,{base64_image}"

# Function to convert binary image data to base64 and then to data URL
def binary_to_data_url(binary_image, mime_type='image/png'):
    base64_image = base64.b64encode(binary_image).decode('utf-8')
    with open('base64.txt', 'w') as file:
        file.write(base64_image)
    return base64_to_data_url(base64_image, mime_type)

# Simulated LLM function
async def a_call_llm(websocket, data):
    print("Calling LLM with base64 data URL:", data['messages'][1]['content'][1]['image']['url'])
    
    first_chunk_sent = False
    prompt = [
        HumanMessage(content=[
            {"type": "text", "text": "Let's play a game. Think of a country and give me a clue. The clue must be specific enough that there is only one correct country. I will try pointing at the country on a map."},
        ]),
        SystemMessage(content=[{"type": "text", "text": "Alright, here's your clue: This country is renowned for being the birthplace of both the ancient Olympic Games and democracy. Where would you point on the map?"}]),
        # HumanMessage(content=[
        #     {"type": "text", "text": "Is it Greece?"},
        # ]),
        HumanMessage(content=[
            {"type": "image_url", "image_url": { "url" : data['messages'][1]['content'][1]['image']['url']} },
        ])
    ]
    
    await websocket.send("<|im_start|>")
    response = ""
    for chunk in llm.stream(prompt):
        # print(chunk)
        chunk_content = chunk.content
        if not first_chunk_sent and chunk_content.strip() == "":
            continue
        if not first_chunk_sent:
            chunk_content = chunk_content.lstrip()
            first_chunk_sent = True
        response += chunk_content
        await websocket.send(chunk_content)
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    speaker.Speak(response)
    await websocket.send("<|im_end|>")
    # else:
    #     await websocket.send(json.dumps({"error": "No prompt provided"}))

async def websocket_handler(websocket, path):
    async for message in websocket:
        data = json.loads(message)
        messages = data.get('messages', [])

        for msg in messages:
            if msg['role'] == 'user':
                new_content = []
                for content in msg['content']:
                    if content['type'] == 'voice':
                        if 'url' in content['voice']:
                            audio_url = content['voice']['url']
                            text = recognize_speech_from_audio_url(audio_url)
                        else:
                            base64_voice = content['voice']['data']
                            play_audio(base64_voice)  # Optionally play the audio
                            text = recognize_speech_from_base64(base64_voice)
                        new_content.append({'type': 'text', 'text': text})
                    elif content['type'] == 'image':
                        if 'url' in content['image']:
                            image_url = content['image']['url']
                            with open(image_url, 'rb') as image_file:
                                image_binary = image_file.read()
                            data_url = binary_to_data_url(image_binary)
                        else:
                            base64_image = content['image']['data']
                            data_url = base64_to_data_url(base64_image)
                        new_content.append({'type': 'image', 'image': {'url': data_url}})
                    else:
                        new_content.append(content)
                msg['content'] = new_content

        await a_call_llm(websocket, data)
        # await websocket.send(json.dumps({"status": "processed", "data": data}))

start_server = websockets.serve(websocket_handler, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
