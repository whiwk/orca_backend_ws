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
            await self.monitoring_task

    async def receive(self, text_data):
        data = json.loads(text_data)
        pod_name = data.get('pod_name')
        namespace = data.get('namespace')

        if not pod_name or not namespace:
            await self.send(text_data=json.dumps({'error': 'Invalid pod name or namespace'}))
            return

        # Start the monitoring task
        if self.monitoring_task:
            self.monitoring_task.cancel()
            await self.monitoring_task

        self.monitoring_task = asyncio.create_task(self.monitor_logs(pod_name, namespace))

    async def monitor_logs(self, pod_name, namespace):
        process = None
        try:
            while True:
                command_list = ['kubectl', 'exec', pod_name, '-n', namespace, '--', 'cat', 'nrL1_UE_stats-0.log']
                print(f"Running command: {' '.join(command_list)}")  # Debug: print the command

                process = await asyncio.create_subprocess_exec(
                    *command_list,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                while True:
                    line = await process.stdout.readline()
                    if line:
                        print(f"Received line: {line.decode('utf-8')}")  # Debug: print each line received
                        await self.send(text_data=json.dumps({'monitoring_output': line.decode('utf-8')}))
                    else:
                        break

                    # Check periodically if the task has been cancelled
                    if self.monitoring_task.cancelled():
                        break

                await process.wait()

                if self.monitoring_task.cancelled():
                    break

                # Sleep for 5 seconds before the next execution
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            if process:
                process.kill()
                await process.wait()
            raise
        except Exception as e:
            await self.send(text_data=json.dumps({'error': str(e)}))
            print(f"Error: {e}")  # Debug: print the error
        finally:
            if process and not process.returncode:
                process.kill()
                await process.wait()

if __name__ == "__main__":
    # This is a testing stub to run the consumer directly
    import sys
    from channels.testing import WebsocketCommunicator
    from django.conf import settings

    settings.configure()
    consumer = MonitoringConsumer()

    async def test_consumer():
        communicator = WebsocketCommunicator(consumer, "/testws/")
        connected, subprotocol = await communicator.connect()
        assert connected
        await communicator.send_json_to({
            "pod_name": "test-pod",
            "namespace": "default"
        })
        response = await communicator.receive_json_from()
        print(response)

    asyncio.run(test_consumer())
