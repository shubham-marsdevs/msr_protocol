import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MSRConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = "msr_data"
        self.room_group_name = f"msr_{self.room_name}"

        # Join the WebSocket group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave the WebSocket group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Handle incoming messages from WebSocket (if needed)
        pass

    async def send_data(self, data):
        # Send data to WebSocket
        await self.send(text_data=json.dumps({
            'data': data
        }))
