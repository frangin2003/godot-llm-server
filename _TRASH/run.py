import asyncio
import websockets
import json
from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
import win32com.client

import torch
print(torch.cuda.is_available())

# Initialize LlamaCpp with the model
llm = LlamaCpp(
    model_path="./models/Hermes-2-Pro-Mistral-7B.Q4_K_M.gguf",
    # model_path="./models/oh-2.5-m7b-q4k-medium.gguf",
    # n_gpu_layers=1,
    n_gpu_layers=30,
    n_ctx=3584, 
    n_batch=512,
    f16_kv=True,
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
    verbose=True,
    # stop=["\n", "<|im_end|>"],
    stop=["<|im_end|>"],
)

async def handle_connection(websocket, path):
    async for message in websocket:
        try:
            print(f"Received message: {message} on path: {path}")
            # Example usage of the path to differentiate behavior
            if path == "/chat":
                # Handle chat messages
                response = "This is a chat endpoint."
                data = json.loads(message)

                user = data.get("user", "")
                audio_file_path = data.get("audio_file_path", "")
                if audio_file_path:
                    import speech_recognition as sr
                    recognizer = sr.Recognizer()
                    with sr.AudioFile(audio_file_path) as source:
                        audio_data = recognizer.record(source)
                        try:
                            user = recognizer.recognize_google(audio_data)
                            print(f"Converted speech to text: {user}")
                        except sr.UnknownValueError:
                            await websocket.send(json.dumps({"error": "Google Speech Recognition could not understand audio"}))
                        except sr.RequestError as e:
                            await websocket.send(json.dumps({"error": f"Could not request results from Google Speech Recognition service; {e}"}))
                else:
                    await websocket.send(json.dumps({"error": "No audio file path provided"}))

                system = data.get("system", "")
                if not system:
                    system = "You are a helpful assistant that casually chats with the user."

                if user:
                    prompt  = f"<|im_start|>system\n{system}<|im_end|>\n"
                    prompt += f"<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant"
                    print(prompt)
                    # Invoke the LlamaCpp model with the prompt and stream the result to the websocket client
                    first_chunk_sent = False
                    response = ""
                    await websocket.send("<|im_start|>")
                    async for chunk in llm.astream(prompt):
                        if not first_chunk_sent and chunk.strip() == "":
                            continue
                        if not first_chunk_sent:
                            chunk = chunk.lstrip()
                            first_chunk_sent = True
                        response += chunk
                        await websocket.send(chunk)
                    speaker = win32com.client.Dispatch("SAPI.SpVoice")
                    speaker.Speak(response)
                    await websocket.send("<|im_end|>")
                else:
                    await websocket.send(json.dumps({"error": "No prompt provided"}))

            elif path == "/data":
                # Handle data messages
                response = "This is a data endpoint."
                audio_bytes = data.get("audio_bytes", None)
                if audio_bytes:
                    import io
                    import wave
                    import pyaudio
                    # Convert byte array back to audio and play it
                    audio_stream = io.BytesIO(audio_bytes)
                    wave_file = wave.open(audio_stream, 'rb')
                    p = pyaudio.PyAudio()
                    stream = p.open(format=p.get_format_from_width(wave_file.getsampwidth()),
                                    channels=wave_file.getnchannels(),
                                    rate=wave_file.getframerate(),
                                    output=True)
                    data_chunk = wave_file.readframes(1024)
                    while data_chunk:
                        stream.write(data_chunk)
                        data_chunk = wave_file.readframes(1024)
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                    await websocket.send(json.dumps({"success": "Audio played successfully"}))
                else:
                    await websocket.send(json.dumps({"error": "No audio bytes provided"}))
            else:
                # Default response for unknown paths
                response = f"No specific handler for path: {path}"
                await websocket.send(response)
                # Parse the received message as JSON and extract the prompt

        except json.JSONDecodeError:
            await websocket.send(json.dumps({"error": "Invalid JSON format"}))

async def main():
    async with websockets.serve(handle_connection, "localhost", 8765):
        print("WebSocket server started on ws://localhost:8765")
        await asyncio.Future()  # Run forever

asyncio.run(main())

