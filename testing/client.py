import asyncio
import websockets
import json

async def connect_to_server():
    async with websockets.connect("ws://localhost:8765") as websocket:
        # Send a JSON object with a prompt property equals "hi"
        await websocket.send(json.dumps({"client":"monitor", "user": "hi"}))
        while True:
            chunk = await websocket.recv()
            print(chunk, end="")

asyncio.run(connect_to_server())
