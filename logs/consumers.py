# logs/consumers.py

import json
import asyncio
import subprocess
from channels.generic.websocket import AsyncWebsocketConsumer

class LogsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.monitoring_task = None
        await self.accept()

    async def disconnect(self, close_code):
        if self.monitoring_task:
            self.monitoring_task.cancel()

    async def receive(self, text_data):
        data = json.loads(text_data)
        self.pod_name = data.get('pod_name')
        self.namespace = data.get('namespace')

        if not self.pod_name or not self.namespace:
            await self.send(text_data=json.dumps({'error': 'Invalid pod name or namespace'}))
            return

        # Start the monitoring task
        if self.monitoring_task:
            self.monitoring_task.cancel()

        self.monitoring_task = asyncio.create_task(self.monitor_logs())

    async def monitor_logs(self):
        cmd = [
            "kubectl", "logs", self.pod_name,
            "-n", self.namespace,
            "--timestamps"
        ]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            async for line in process.stdout:
                await self.send(text_data=line.decode('utf-8'))
        except asyncio.CancelledError:
            # Handle task cancellation
            if process:
                process.kill()

        await process.wait()
