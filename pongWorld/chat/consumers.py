import json

from channels.generic.websocket import AsyncWebsocketConsumer

class PublicChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'public'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "public.message", "message": message}
        )

    async def public_message(self, event):
        message = event["message"]

        await self.send(text_data=json.dumps({"message": message}))