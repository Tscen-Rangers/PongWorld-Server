import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from chat.socket.mixins import ChatMixin


class ConnectConsumer(AsyncWebsocketConsumer, ChatMixin):
    async def connect(self):
        self.user = self.scope['user']

        if self.user.is_authenticated:
            self.player_id = self.user.id
            self.online_users_group = 'online_users'
            self.player_group = f'player_{self.player_id}'

            await self.channel_layer.group_add(self.online_users_group, self.channel_name)
            await self.channel_layer.group_add(self.player_group, self.channel_name)

            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(self.online_users_group, self.channel_name)
            await self.channel_layer.group_discard(self.player_group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            text_data_json = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_error_message("Invalid JSON received")
            return
        message_type = text_data_json.get('type')
        if message_type is None:
            await self.send_error_message("Message type not provided")
            return

        if message_type == 'public_chat':
            await ChatMixin.handle_public_chat(self, text_data_json)
        elif message_type == 'private_chat':
            await ChatMixin.handle_private_chat(self, text_data_json)

    async def send_error_message(self, message):
        await self.send(text_data=json.dumps({
            "error": message
        }, ensure_ascii=False))