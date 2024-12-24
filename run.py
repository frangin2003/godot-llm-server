import pythoncom
import asyncio
import websockets
import json
import queue
import threading
import signal
import traceback
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

tts_queue = queue.Queue()
tts_thread = None
should_stop = False

def tts_worker():
    pythoncom.CoInitialize()
    """Single worker thread to handle all TTS requests"""
    while not should_stop:
        try:
            # Get work from queue, timeout allows checking should_stop
            try:
                work = tts_queue.get(timeout=1)
            except queue.Empty:
                continue
                
            if work is None:
                break
                
            text, speaker_id, callback = work
            tts_async(text, speaker_id, callback)
            tts_queue.task_done()
            
        except Exception as e:
            print(f"Error in TTS worker: {e}")
            import traceback
            traceback.print_exc()

        finally:
            pythoncom.CoUninitialize()

async def a_call_llm(websocket, data):
    global tts_thread
    
    try:
        print("a_call_llm: Start processing data")
        if monitor_socket:
            await monitor_socket.send("")

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
        capturing_action = False
        action = ""
 
        if game_socket:
            await game_socket.send("")
            await asyncio.sleep(0)
        for chunk in llm_instance.llm._stream(prompt):
            chunk_text = chunk.text
            print(f"Received chunk: {chunk_text}")
            if monitor_socket:
                await monitor_socket.send(chunk_text)
            all_chunks_text += chunk_text
            # Clean and manage the buffer
            chunk_text = chunk_text.replace('","', '').replace(',"', '').replace('",', '').replace('"', '').replace('{', '').replace('}', '').replace(':', '').replace('=', '').replace('```', '')
            all_chunks += chunk_text
 
            buffer += chunk_text
            if (chunk_text.strip() == "_"
                and buffer != "_speaker" and buffer != "_text" and buffer != "_action"):
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
            elif buffer == "_action":
                capturing_text = False
                capturing_action = True
                buffer = ""  # Reset buffer after detecting keyword
                print("Capturing action")
                continue

            # Accumulate content into the response or action based on the current state
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
            elif capturing_action:
                action += chunk_text

        if not at_least_one_chunk_has_been_sent:
            if game_socket:
                await game_socket.send(all_chunks)
                await asyncio.sleep(0)

        print(f"all_chunks = {all_chunks}")
        print(f"all_chunks_text = {all_chunks_text}")
        print(f"text = {text}")

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

        # Instead of creating a new thread, queue the TTS work
        tts_queue.put((text, ''.join(filter(str.isdigit, speaker_id)), tts_callback))
        
        if action:
            if action and action[0].isdigit():
                action = ''.join(filter(str.isdigit, action))
            else:
                action = action.strip()
            print(f'FINAL action=|{action}|')
            if game_socket:
                await game_socket.send(f"<|action|>{''.join(filter(str.isalnum, action))}")
                await asyncio.sleep(0)

        if game_socket:
            await game_socket.send("")
            await asyncio.sleep(0)
        print("a_call_llm: Finished processing data")

    except Exception as e:
        print(f"Error in a_call_llm: {e}")
        import traceback
        traceback.print_exc()

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
        init_message = await websocket.recv()
        init_data = json.loads(init_message)
        client_type = init_data.get('client')
        
        if client_type == 'game':
            game_socket = websocket
        elif client_type == 'monitor':
            monitor_socket = websocket
        
        if len(init_data) > 1:
            try:
                await asyncio.sleep(0)
                data = init_data if isinstance(init_data, dict) else json.loads(init_data)
                await a_call_llm(websocket, data)
            except Exception as e:
                print(f"Error processing initial message: {e}")
                traceback.print_exc()
        
        # Process further messages for both game_socket and monitor_socket
        async for message in websocket:
            try:
                data = message if isinstance(message, dict) else json.loads(message)
                await a_call_llm(websocket, data)
            except Exception as e:
                print(f"Error processing message: {e}")
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
    global tts_thread, should_stop
    
    # Initialize shutdown event
    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    
    def handle_shutdown(signum, frame):
        loop.call_soon_threadsafe(shutdown_event.set)

    # Set up signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, handle_shutdown)

    try:
        print("Starting llm-server...")
        # Start the TTS worker thread
        should_stop = False
        tts_thread = threading.Thread(target=tts_worker, daemon=True)
        tts_thread.start()
        
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
        # Clean shutdown of TTS thread
        should_stop = True
        tts_queue.put(None)  # Signal the worker to stop
        if tts_thread and tts_thread.is_alive():
            tts_thread.join(timeout=3)
        # Close all websockets
        if game_socket:
            await game_socket.close()
        if monitor_socket:
            await monitor_socket.close()
            
        print("Shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Shutting down gracefully...")
    except Exception as e:
        print(f"Fatal error in main: {e}")
        import traceback
        traceback.print_exc()