import json
import asyncio
import subprocess
from channels.generic.websocket import AsyncWebsocketConsumer

class ShellConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.command_process = None
        await self.accept()

    async def disconnect(self, close_code):
        if self.command_process:
            self.command_process.kill()

    async def receive(self, text_data):
        data = json.loads(text_data)
        pod_name = data.get('pod_name')
        namespace = data.get('namespace')
        command = data.get('command')

        if not pod_name or not namespace or not command:
            await self.send(text_data=json.dumps({'error': 'Invalid pod name, namespace, or command'}))
            return

        command_list = ['kubectl', 'exec', '-it', pod_name, '-n', namespace, '--'] + command.split()

        self.command_process = await asyncio.create_subprocess_exec(
            *command_list,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        while True:
            line = await self.command_process.stdout.readline()
            if line:
                await self.send(text_data=json.dumps({'command_output': line.decode('utf-8')}))
            else:
                break

        await self.command_process.wait()
        self.command_process = None
