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
            print(self.player_id)
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
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']

        if message_type == 'public_chat':
            await ChatMixin.handle_public_chat(self, text_data_json)
