import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer

class ProtocolStackConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.sniffing_process = None
        await self.accept()

    async def disconnect(self, close_code):
        if self.sniffing_process:
            self.sniffing_process.kill()

    async def receive(self, text_data):
        data = json.loads(text_data)
        pod_name = data.get('pod_name')
        namespace = data.get('namespace')

        if not pod_name or not namespace:
            await self.send(text_data=json.dumps({'error': 'Invalid pod name or namespace'}))
            return

        # Command to capture SCTP packets and parse them with tshark
        sniff_command = [
            'kubectl', 'exec', '-it', pod_name, '-n', namespace, '-c', 'tcpdump', '--',
            'sh', '-c', 'tshark -i f1 -Y "sctp" -T json -e sctp.srcport -e sctp.dstport -e sctp.verification_tag -e sctp.assoc_index -e sctp.port -e sctp.checksum -e sctp.checksum.status -e sctp.chunk_type -e sctp.chunk_flags -e sctp.chunk_length -e sctp.parameter_type -e sctp.parameter_length -e sctp.parameter_heartbeat_information'
        ]

        self.sniffing_process = await asyncio.create_subprocess_exec(
            *sniff_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        while True:
            chunk = await self.sniffing_process.stdout.readline()
            if chunk:
                formatted_output = chunk.decode('utf-8').strip()
                # Here, just send the raw line as received
                await self.send(text_data=json.dumps({'data': formatted_output}))
            else:
                break

        await self.sniffing_process.wait()
        self.sniffing_process = None
