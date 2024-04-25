import asyncio
import websockets
import json
import base64
from mimetypes import guess_type
import speech_recognition as sr
import wave
import pyaudio
from io import BytesIO
from langchain_community.llms import Ollama
from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
import win32com.client

import torch
print(torch.cuda.is_available())

# Initialize LlamaCpp with the model
llm = Ollama(
    model="llama3",
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
    verbose=True,
    # stop=["\n", "<|im_end|>"],
    stop=["<|eot_id|>"],
)

import pythoncom
import win32com.client

# Global initialization of COM and speech object
global_speaker = win32com.client.Dispatch("SAPI.SpVoice")

def speak_async(response):
    pythoncom.CoInitialize()
    try:
        # Debugging output
        print("Attempting to stop any ongoing speech...")
        global_speaker.Speak("", 2)  # Attempt to stop any ongoing speech
        print("Attempting to speak new response...")
        global_speaker.Speak(response)
        print("Speaking complete.")
    except Exception as e:
        print(f"An error occurred in speak_async: {e}")
    finally:
        pythoncom.CoUninitialize()  # Clean up COM initialization


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
    print("Calling LLM with data:", data)
    
    system = None
    # Extract system prompt
    for message in data['messages']:
        if message['role'] == 'system':
            system = message['content']
            break  # Assuming there's only one system prompt
    if not system:
        system = "You are a helpful assistant that casually chats with the user."

    prompt  = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system}<|eot_id|>\n"

    # Extract user text prompts
    for message in data['messages']:
        if message['role'] == 'user':
            for item in message['content']:
                if item['type'] == 'text':
                    prompt += f"<|start_header_id|>user<|end_header_id|>\n{item['text']}<|eot_id|>"
    prompt += "<|start_header_id|>assistant<|end_header_id|>"
    print(prompt)

    # Invoke the LlamaCpp model with the prompt and stream the result to the websocket client
    command = ""
    buffer = ""
    text = ""
    capturing_response = False
    capturing_command = False

    await websocket.send("<|begin_of_text|>")
    for chunk in llm._stream(prompt):
        print("***************************************")
        chunk_text = chunk.text
        print(f"chunk_text=|{chunk_text}|")

        # Clean and manage the buffer
        chunk_text = chunk_text.replace('","', '').replace(',"', '').replace('",', '').replace('"', '').replace('{', '').replace('}', '').replace(':', '').replace('=', '')
        print(f"chunk_text=|{chunk_text}| SANITIZED")
        buffer += chunk_text
        print(f"buffer=|{buffer}|")
        if (chunk_text.strip() == "_"
            and buffer != "_text" and buffer != "_command"
            and buffer != "_text_" and buffer != "_command_"):
            buffer = "_"
            continue

        if (buffer == "_text" or buffer == "_command"):
            print(' if (buffer == "_text" or buffer == "_command"):')
            continue

        # Check and transition based on keywords
        if buffer == "_text_":
            print(' if buffer == "_text":')
            capturing_response = True
            buffer = ""  # Reset buffer after detecting keyword
            continue

        elif buffer == "_command_":
            print(' elif "_command_" in buffer:')
            capturing_response = False
            capturing_command = True
            buffer = ""  # Reset buffer after detecting keyword
            continue

        # Accumulate content into the response or command based on the current state
        if capturing_response:
            print(' if capturing_response:')
            text += chunk_text
            print(f'text=|{text}|')
            await websocket.send(chunk_text)
        elif capturing_command:
            print(' elif capturing_command:')
            command += chunk_text
            print(f'command=|{command}|')

    import threading
    threading.Thread(target=speak_async, args=(text,)).start()


    print(f'FINAL command=|{command}|')
    if command:
        await websocket.send(f"<|command|>{command}")

    await websocket.send("<|end_of_text|>")
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

# Remember to properly uninitialize COM when your application exits
# pythoncom.CoUninitialize()

start_server = websockets.serve(websocket_handler, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
