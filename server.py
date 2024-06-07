import asyncio
import websockets


async def handler(websocket, path):
    while True:
        message = await websocket.recv()
        print(f"Received message: {message}")
        await websocket.send(f"Message received: {message}")


async def main():
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()  # run forever

if name == "main":
    asyncio.run(main())
