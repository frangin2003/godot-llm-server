import asyncio
import websockets
import json
import queue
import threading
import signal
from dotenv import load_dotenv
from tts_utils import tts_async
from llm_utils import create_llm_instance
from db_utils import init_db, save_prompt

load_dotenv()
import sys

if len(sys.argv) < 2:
    raise ValueError("Port must be provided as a command-line argument")
if len(sys.argv) < 3:
    raise ValueError("Model name must be provided as a command-line argument")

port = sys.argv[1]
model_name = sys.argv[2]
capture_enabled = len(sys.argv) > 3 and sys.argv[3] == "capture"

if capture_enabled:
    init_db()

llm_instance = create_llm_instance(model_name, debug=True)
queue_sentences = queue.Queue()
queue_speak = queue.Queue()

game_socket = None
monitor_socket = None

async def a_call_llm(websocket, data):
    print("a_call_llm: Start processing data")
    if monitor_socket:
        await monitor_socket.send("")
        await monitor_socket.send(data)

    prompt = llm_instance.get_prompt_from_messages(data)
    if monitor_socket:
        await monitor_socket.send(prompt)
    all_chunks = ""
    all_chunks_text = ""
    buffer = ""
 
    capturing_speaker = False
    speaker_id = ""
    capturing_text = False
    at_least_one_chunk_has_been_sent = False
    text = ""
    capturing_command = False
    command = ""
 
    if game_socket:
        await game_socket.send("")
        await asyncio.sleep(0)
    for chunk in llm_instance.llm._stream(prompt):
        chunk_text = chunk.text
        print(f"Received chunk: {chunk_text}")
        all_chunks_text += chunk_text
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
            print("Capturing speaker")
            continue
        elif buffer == "_text":
            capturing_speaker = False
            capturing_text = True
            buffer = ""  # Reset buffer after detecting keyword
            print("Capturing text")
            continue
        elif buffer == "_command":
            capturing_text = False
            capturing_command = True
            buffer = ""  # Reset buffer after detecting keyword
            print("Capturing command")
            continue

        # Accumulate content into the response or command based on the current state
        if capturing_speaker:
            speaker_id += chunk_text
        elif capturing_text:
            at_least_one_chunk_has_been_sent = True
            text += chunk_text
            # if "." in chunk_text:
            #     sentences = text.split(".")
            #     if len(sentences) > 1:
            #         last_sentence = sentences[-2] + "."  # Include the period
            #         queue_sentences.append(last_sentence)
            if game_socket:
                await game_socket.send(chunk_text)
                await asyncio.sleep(0)
        elif capturing_command:
            command += chunk_text

    if not at_least_one_chunk_has_been_sent:
        if game_socket:
            await game_socket.send(all_chunks)
            await asyncio.sleep(0)

    print(f"All chunks: {all_chunks}")

    if capture_enabled:
        save_prompt(data, all_chunks_text)

    # Store the event loop from the main thread
    loop = asyncio.get_running_loop()

    # Create a callback function to send the runtime via websocket
    async def send_runtime_callback(runtime, speaker_id):
        if game_socket:
            await game_socket.send(f"<|speak|>{speaker_id}|{runtime:.2f}")

    # Create a wrapper function that uses the stored loop
    def tts_callback(runtime, speaker_id):
        asyncio.run_coroutine_threadsafe(
            send_runtime_callback(runtime, speaker_id), 
            loop  # Use the stored loop instead of trying to get a new one
        )

    # Start TTS thread with the callback
    threading.Thread(
        target=tts_async, 
        args=(text, ''.join(filter(str.isdigit, speaker_id)), tts_callback)
    ).start()

    if command:
        if command and command[0].isdigit():
            command = ''.join(filter(str.isdigit, command))
        else:
            command = command.strip()
        print(f'FINAL command=|{command}|')
        if game_socket:
            await game_socket.send(f"<|command|>{''.join(filter(str.isalnum, command))}")
            await asyncio.sleep(0)

    if game_socket:
        await game_socket.send("")
        await asyncio.sleep(0)
    print("a_call_llm: Finished processing data")

def queue_sentences_listener():
    while True:
        sentence = queue_sentences.get()  # Block until an item is available
        if sentence is None:
            break  # Exit if None is received
        print(f"Processing sentence from queue: {sentence}")
        # Create an event to wait for the TTS to finish
        tts_finished = threading.Event()
        
        def tts_callback():
            tts_finished.set()
        
        # Call tts_async with the callback
        threading.Thread(target=tts_async, args=(None, sentence, '1', tts_callback)).start()
        
        # Wait for the TTS to finish before processing the next sentence
        tts_finished.wait()

# Start the queue_sentences_listener in a separate thread
# queue_sentences_listener_thread = threading.Thread(target=queue_sentences_listener, daemon=True)
# queue_sentences_listener_thread.start()

async def websocket_handler(websocket, path):
    global game_socket, monitor_socket
    try:
        print("websocket_handler: New connection established")
        # Get client type
        init_message = await websocket.recv()
        client_type = json.loads(init_message).get('client')
        
        if client_type == 'game':
            game_socket = websocket
        elif client_type == 'monitor':
            monitor_socket = websocket
            
        async for message in websocket:
            try:
                data = json.loads(message)
                await a_call_llm(websocket, data)
            except Exception as e:
                print(f"Error processing message: {e}")
                import traceback
                traceback.print_exc()
    finally:
        if websocket == game_socket:
            game_socket = None
        elif websocket == monitor_socket:
            monitor_socket = None
        print("websocket_handler: Connection closed")

def signal_handler(signum, frame):
    print(f"Received signal {signum}. Shutting down gracefully...")
    # Perform any cleanup here
    asyncio.get_event_loop().stop()

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def main():
    try:
        start_server = websockets.serve(websocket_handler, "localhost", port)
        print("llm-server ready!")
        print(f"port={port}")
        print(f"model_name={model_name}")

        await start_server
        print("Server started and running")
        
        try:
            await asyncio.Future()  # Run forever
        except asyncio.CancelledError:
            print("Server received cancellation")
        except Exception as e:
            print(f"Unexpected error in main loop: {e}")
            import traceback
            traceback.print_exc()
    except Exception as e:
        print(f"Fatal error in main: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Server stopped")

if __name__ == "__main__":
    asyncio.run(main())