import asyncio
import websockets
import json

async def process_message(websocket, message):
    try:
        print(f"\nReceived message: {message}")
        data = json.loads(message)
        print(f"Parsed JSON data: {data}")
        
        # Extract the user message from the nested structure
        user_messages = [msg for msg in data.get('messages', []) if msg.get('role') == 'user']
        if not user_messages:
            print("No user message found")
            return
            
        # Get the last user message content
        user_content = user_messages[-1].get('content', [])
        if not user_content:
            print("No content in user message")
            return
            
        # Get the text content and parse it as JSON
        text_content = next((item['text'] for item in user_content if item.get('type') == 'text'), None)
        if not text_content:
            print("No text content found")
            return
            
        print(f"Processing text content: {text_content}")
        response_data = json.loads(text_content)
        
        # Extract text if present
        if "_text" in response_data:
            text = response_data["_text"]
            print(f"Processing text: {text}")
            # Send text word by word with delay
            words = text.split()
            for word in words:
                print(f"Sending word: {word}")
                await websocket.send(word + " ")
                await asyncio.sleep(0.03)  # 30ms delay
        
        # Send action if present
        if "_action" in response_data:
            action = response_data["_action"]
            action_message = f"<|action|>{action}"
            print(f"Sending action: {action_message}")
            await websocket.send(action_message)

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        await websocket.send(message)
    except Exception as e:
        print(f"Error in process_message: {e}")
        import traceback
        traceback.print_exc()

async def websocket_handler(websocket):
    print(f"New connection established from {websocket.remote_address}")
    try:
        async for message in websocket:
            await process_message(websocket, message)
    except websockets.exceptions.ConnectionClosed:
        print("Connection closed normally")
    except Exception as e:
        print(f"Error in websocket_handler: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"Connection from {websocket.remote_address} closed")

async def main():
    port = 7500
    print(f"Starting echo server on port {port}...")
    server = await websockets.serve(websocket_handler, "localhost", port)
    print(f"Echo server running on ws://localhost:{port}")
    await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shutting down due to keyboard interrupt...")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()