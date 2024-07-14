import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://10.30.1.221:8020/ws/protocolstack/"
    async with websockets.connect(uri) as websocket:
        # Send initial data to start the tcpdump command
        message = json.dumps({
            'pod_name': 'oai-du-level1-user1-865645d8f4-xjg8r',  # Replace with your actual pod name
            'namespace': 'user1'  # Replace with your actual namespace
        })
        await websocket.send(message)
        
        # Listen for messages from the server
        while True:
            try:
                response = await websocket.recv()
                response_data = json.loads(response)
                if 'data' in response_data:
                    print(response_data['data'])
                elif 'message' in response_data:
                    print(response_data['message'])
                elif 'error' in response_data:
                    print(response_data['error'])
            except websockets.ConnectionClosed:
                print("Connection closed")
                break

asyncio.get_event_loop().run_until_complete(test_websocket())
