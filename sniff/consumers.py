import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orca_backend_ws.settings')
django.setup()

import json
import asyncio
import signal
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer

class SniffConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.sniffing_process = None
        self.pcap_process = None
        self.pcap_filepath = None
        await self.accept()
        signal.signal(signal.SIGTERM, self.handle_termination)
        signal.signal(signal.SIGINT, self.handle_termination)

    async def disconnect(self, close_code):
        await self.cleanup()

    async def receive(self, text_data):
        data = json.loads(text_data)
        pod_name = data.get('pod_name')
        namespace_name = data.get('namespace')

        if not pod_name or not namespace_name:
            await self.send(text_data=json.dumps({'error': 'Invalid pod name or namespace'}))
            return

        component = '-'.join(pod_name.split('-')[1:3])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pcap_filename = f"{namespace_name}_{component}_{timestamp}.pcap"
        pcap_directory = 'home'
        os.makedirs(pcap_directory, exist_ok=True)
        self.pcap_filepath = f"{pcap_directory}/{pcap_filename}"

        sniff_command = [
            'kubectl', 'exec', '-it', pod_name, '-n', namespace_name, '-c', 'tcpdump', '--',
            'tshark', '-i', 'f1', 'sctp or udp port 2152'
        ]

        pcap_command = [
            'kubectl', 'exec', '-it', pod_name, '-n', namespace_name, '-c', 'tcpdump', '--',
            'tshark', '-i', 'f1', '-w', self.pcap_filepath, 'sctp or udp port 2152'
        ]

        self.sniffing_process = await asyncio.create_subprocess_exec(
            *sniff_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        self.pcap_process = await asyncio.create_subprocess_exec(
            *pcap_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            while True:
                chunk = await self.sniffing_process.stdout.readline()
                if chunk:
                    formatted_output = chunk.decode('utf-8').strip()
                    await self.send(text_data=json.dumps({'data': formatted_output}))
                else:
                    break

            await self.sniffing_process.wait()
            self.sniffing_process = None

            await self.pcap_process.wait()
            self.pcap_process = None

        except asyncio.CancelledError:
            await self.cleanup()

    async def cleanup(self):
        if self.sniffing_process:
            self.sniffing_process.terminate()
            await self.sniffing_process.wait()
            self.sniffing_process = None

        if self.pcap_process:
            self.pcap_process.terminate()
            await self.pcap_process.wait()
            self.pcap_process = None

    def handle_termination(self, signum, frame):
        asyncio.create_task(self.cleanup())
