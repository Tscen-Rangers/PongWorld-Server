import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone


class ConnectConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name1 = 'online_users'
        self.room_group_name2 = f'player_{self.player_id}'


        await self.channel_layer.group_add(self.room_group_name1, self.channel_name)
        await self.channel_layer.group_add(self.room_group_name2, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name1, self.channel_name)
        await self.channel_layer.group_discard(self.room_group_name2, self.channel_name)
