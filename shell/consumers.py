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

        if command == 'stop':
            if self.command_process:
                # Find the PID of the running process inside the pod and kill it
                find_pid_command = f"kubectl exec -it {pod_name} -n {namespace} -- pkill -f '{self.current_command}'"
                subprocess.run(find_pid_command, shell=True)
                await self.send(text_data=json.dumps({'message': 'Command stopped'}))
            return

        self.current_command = command

        # Check if the command is 'ping' and if '-c' is missing
        if command.startswith('ping') and '-c' not in command:
            command += ' -c 4'

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
