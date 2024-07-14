import asyncio
import websockets
import json

async def test_logs_consumer():
    uri = "ws://10.30.1.221:8020/ws/logs/"  # Replace with your actual WebSocket URL

    async with websockets.connect(uri) as websocket:
        print("WebSocket connection established")

        # Define the message to send
        message = {
            "pod_name": "oai-cu-level1-user1-cb4b4dcb6-p7vc8",  # Replace with your actual pod name
            "namespace": "user1"  # Replace with your actual namespace
        }

        # Send the message
        await websocket.send(json.dumps(message))
        print(f"Sent: {json.dumps(message)}")

        try:
            while True:
                # Receive the message
                response = await websocket.recv()
                print(f"Received: {response}")

        except websockets.ConnectionClosed:
            print("WebSocket connection closed")

# Run the test
asyncio.get_event_loop().run_until_complete(test_logs_consumer())
