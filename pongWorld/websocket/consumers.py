import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import F
from django.db.models import Q
from django.utils import timezone

from chat.socket.mixins import ChatMixin
from game.socket.match_consumers import GameMixin
from blocks.models import Block
from player.models import Player
from config.utils import CommonUtils

class ConnectConsumer(AsyncWebsocketConsumer, ChatMixin, GameMixin):
    async def connect(self):
        self.user = self.scope['user']

        if self.user.is_authenticated:
            self.player_id = self.user.id

            self.chatroom = None
            self.online_users_group = 'online_users'
            self.player_group = f'player_{self.player_id}'
            await self.channel_layer.group_add(self.online_users_group, self.channel_name)
            await self.channel_layer.group_add(self.player_group, self.channel_name)

            await self.accept()

            await self.update_user_connection()
            await self.channel_layer.group_send(
                self.online_users_group,
                {
                    'type': 'user.online',
                    'user_id': self.player_id,
                    'nickname': self.user.nickname,
                    'profile_img': CommonUtils.get_full_url(self.user.profile_img.url)
                }
            )
        else:
            await self.close()

    @database_sync_to_async
    def update_user_connection(self):
        Player.objects.filter(id=self.user.id).update(online_count=F('online_count')+1)
        Player.objects.filter(id=self.user.id).update(last_login_time=timezone.now())

    @database_sync_to_async
    def update_user_disconnection(self):
        Player.objects.filter(id=self.user.id).update(online_count=F('online_count')-1)
        user = Player.objects.get(id=self.user.id)

    @database_sync_to_async
    def is_user_offline(self):
        user = Player.objects.get(id=self.user.id)
        return user.online_count == 0
    
    async def user_online(self, event):
        user_id = event['user_id']
        if await self.is_blocked_user(user_id):
            return

        await self.send(text_data=json.dumps({
            'type': 'user_online',
            'user_id': user_id,
            'nickname': event['nickname'],
            'profile_img': event['profile_img']
        }))
    async def user_offline(self, event):
        user_id = event['user_id']
        if await self.is_blocked_user(user_id):
            return
        await self.send(text_data=json.dumps({
            'type': 'user_offline',
            'user_id': user_id,
            'nickname': event['nickname'],
            'profile_img': event['profile_img']
        }))

    async def disconnect(self, close_code):
        if self.user.is_authenticated:

            await self.update_user_disconnection()
            await self.channel_layer.group_discard(self.online_users_group, self.channel_name)
            await self.channel_layer.group_discard(self.player_group, self.channel_name)
            if await self.is_user_offline():
                await self.channel_layer.group_send(
                    self.online_users_group,
                    {
                        'type': 'user.offline',
                        'user_id': self.player_id,
                        'nickname': self.user.nickname,
                        'profile_img': CommonUtils.get_full_url(self.user.profile_img.url)
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


    # 내가 블락한 유저인지
    @database_sync_to_async
    def is_blocked_user(self, user_id):
        return Block.objects.filter(Q(blocker=self.user.id) & Q(blocked=user_id)).exists()

    # 내가 상대 유저에게 블락되었는지
    @database_sync_to_async
    def am_i_blocked_by_user(self, user_id):
        return Block.objects.filter(Q(blocker=user_id) & Q(blocked=self.user.id)).exists()

    # 상호차단 상태 확인 (둘 중 하나만 블락했어도 True)
    @database_sync_to_async
    def check_mutual_block_status(self, user_id):
        return Block.objects.filter(
            Q(blocker=self.user.id, blocked=user_id) |
            Q(blocker=user_id, blocked=self.user.id)
        ).exists()
