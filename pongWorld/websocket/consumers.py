import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from chat.socket.mixins import ChatMixin
from game.socket.match_consumers import GameMixin

online_users = set()

class ConnectConsumer(AsyncWebsocketConsumer, ChatMixin, GameMixin):
    async def connect(self):
        global online_users
        self.user = self.scope['user']

        if self.user.is_authenticated:
            self.player_id = self.user.id
            online_users.add(self.player_id)

            self.online_users_group = 'online_users'
            self.player_group = f'player_{self.player_id}'
            await self.channel_layer.group_add(self.online_users_group, self.channel_name)
            await self.channel_layer.group_add(self.player_group, self.channel_name)

            await self.accept()

            await self.send_online_users()
            await self.channel_layer.group_send(
                self.online_users_group,
                {
                    'type': 'user.online',
                    'user_id': self.player_id
                }
            )
        else:
            await self.close()

    async def user_online(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_online',
            'user_id': event['user_id']
        }))
    async def user_offline(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_offline',
            'user_id': event['user_id']
        }))

    async def send_online_users(self):
        await self.send(text_data=json.dumps({
            'online_users': list(online_users)
        }))

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(self.online_users_group, self.channel_name)
            await self.channel_layer.group_discard(self.player_group, self.channel_name)
            online_users.remove(self.player_id)
            await self.channel_layer.group_send(
                self.online_users_group,
                {
                    'type': 'user.offline',
                    'user_id': self.player_id
                }
            )

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
        elif message_type == 'invite_game':
            await GameMixin.handle_pvp_game(self, text_data_json)

    async def send_error_message(self, message):
        await self.send(text_data=json.dumps({
            "error": message
        }, ensure_ascii=False))
