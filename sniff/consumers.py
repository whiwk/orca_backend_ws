import json
import asyncio
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer

class SniffConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.sniffing_process = None
        self.pcap_process = None
        await self.accept()

    async def disconnect(self, close_code):
        if self.sniffing_process:
            self.sniffing_process.kill()
        if self.pcap_process:
            self.pcap_process.kill()

    async def receive(self, text_data):
        data = json.loads(text_data)
        pod_name = data.get('pod_name')
        namespace = data.get('namespace')

        if not pod_name or not namespace:
            await self.send(text_data=json.dumps({'error': 'Invalid pod name or namespace'}))
            return

        # Extract the component part from the pod name (e.g., 'cu', 'du', 'nr-ue')
        component = '-'.join(pod_name.split('-')[1:3])

        # Generate a timestamped filename for the pcap file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pcap_filename = f"{namespace}_{component}_{timestamp}.pcap"

        # Define the directory where pcap files will be saved
        pcap_directory = 'sniff'  # Change this to your desired directory path

        # Full path to the pcap file
        pcap_filepath = f"{pcap_directory}/{pcap_filename}"

        # Command to output tcpdump results directly
        sniff_command = [
            'kubectl', 'exec', '-it', pod_name, '-n', namespace, '--',
            'tcpdump', '-i', 'f1', 'sctp or udp port 2152'
        ]

        # Command to save tcpdump results to a pcap file
        pcap_command = [
            'kubectl', 'exec', '-it', pod_name, '-n', namespace, '--',
            'tcpdump', '-i', 'f1', '-w', pcap_filepath, 'sctp or udp port 2152'
        ]

        # Start the sniffing process to output results directly
        self.sniffing_process = await asyncio.create_subprocess_exec(
            *sniff_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Start the process to save results to a pcap file
        self.pcap_process = await asyncio.create_subprocess_exec(
            *pcap_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        while True:
            chunk = await self.sniffing_process.stdout.readline()  # Read line by line
            if chunk:
                # Decode and format the chunk
                formatted_output = chunk.decode('utf-8').strip()
                await self.send(text_data=json.dumps({'data': formatted_output}))
            else:
                break

        await self.sniffing_process.wait()
        self.sniffing_process = None

        await self.pcap_process.wait()
        self.pcap_process = None

        # Inform the client that the pcap file has been saved with the filename
        await self.send(text_data=json.dumps({'message': f'pcap file saved as {pcap_filepath}'}))
