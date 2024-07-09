import json
import asyncio
import subprocess
from channels.generic.websocket import AsyncWebsocketConsumer

class MonitoringConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.monitoring_task = None
        await self.accept()

    async def disconnect(self, close_code):
        if self.monitoring_task:
            self.monitoring_task.cancel()

    async def receive(self, text_data):
        data = json.loads(text_data)
        pod_name = data.get('pod_name')
        namespace = data.get('namespace')

        if not pod_name or not namespace:
            await self.send(text_data=json.dumps({'error': 'Invalid pod name or namespace'}))
            return

        # Start the monitoring task
        self.monitoring_task = asyncio.create_task(self.monitor_logs(pod_name, namespace))

    async def monitor_logs(self, pod_name, namespace):
        while True:
            try:
                command_list = ['kubectl', 'exec', '-it', pod_name, '-n', namespace, '--', 'cat', 'nrL1_UE_stats-0.log']
                process = await asyncio.create_subprocess_exec(
                    *command_list,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                while True:
                    line = await process.stdout.readline()
                    if line:
                        await self.send(text_data=json.dumps({'monitoring_output': line.decode('utf-8')}))
                    else:
                        break

                await process.wait()

                # Sleep for a short duration before the next read to simulate `watch` behavior
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                # Handle task cancellation
                if process:
                    process.kill()
                break
