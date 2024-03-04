import json

from channels.db import database_sync_to_async
from django.utils import timezone

class ChatMixin:
    async def handle_public_chat(self, text_data_json):
        user = self.user
        message = text_data_json['message']

        await self.channel_layer.group_send(
            self.online_users_group, {
                "type": "public.message",
                "user_id": user.id,
                "nickname": user.nickname,
                "message": message,
                "time": timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
        )

    async def public_message(self, event):
        user_id = event['user_id']
        nickname = event['nickname']
        message = event['message']
        time = event['time']

        await self.send(text_data=json.dumps({
            "user_id": user_id,
            "nickname": nickname,
            "message": message,
            "time": time,
        }, ensure_ascii=False))
