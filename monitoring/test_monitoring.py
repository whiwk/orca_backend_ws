import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://10.30.1.221:8010/ws/monitoring/"
    async with websockets.connect(uri) as websocket:
        # Send initial data to start the monitoring command
        message = json.dumps({
            'pod_name': 'oai-nr-ue-level1-user1-76964dbbd7-x5x9b',  # Replace with your actual pod name
            'namespace': 'user1',  # Replace with your actual namespace
        })
        await websocket.send(message)
        
        # Listen for messages from the server
        while True:
            try:
                response = await websocket.recv()
                data = json.loads(response)
                print(f"Received: {data}")
            except websockets.ConnectionClosed:
                print("Connection closed")
                break

# Replace 'your_pod_name' and 'your_namespace' with actual values
asyncio.get_event_loop().run_until_complete(test_websocket())
