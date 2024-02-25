import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone


from chat.models import ChatRoom, Message
from player.models import Player

class PublicChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'chat_public'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data_json = json.loads(text_data)
        message = data_json['message']

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "public.message", "message": message}
        )

    async def public_message(self, event):
        message = event["message"]

        await self.send(text_data=json.dumps({"message": message}, ensure_ascii=False))

class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.sender_id = self.scope['url_route']['kwargs']['sender_id']
        receiver_id = self.scope['url_route']['kwargs']['receiver_id']

        self.chatroom_id, created = await self.get_or_create_chatroom(receiver_id)
        if not created:
            await self.reset_unread_count()

        self.room_group_name = f'chat_private_{self.chatroom_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()
        await self.send(text_data=json.dumps({
            "chatroom_id": self.chatroom_id
        }))

    @database_sync_to_async
    def get_or_create_chatroom(self, receiver_id):
        sorted_ids = sorted([self.sender_id, receiver_id])

        try:
            user1 = Player.objects.get(id=sorted_ids[0])
            user2 = Player.objects.get(id=sorted_ids[1])

            chatroom, created = ChatRoom.objects.get_or_create(
                user1=user1, user2=user2,
                defaults={
                    'last_sender': user1,
                    'unread_count': 0,
                    'updated_at': timezone.now()
                }
            )
            return chatroom.id, created
        except Player.DoesNotExist:
            pass

    @database_sync_to_async
    def reset_unread_count(self):
        try:
            chatroom = ChatRoom.objects.get(id=self.chatroom_id)
            sender = Player.objects.get(id=self.sender_id)
            if chatroom.last_sender != sender:
                chatroom.unread_count = 0
                chatroom.save()
        except Player.DoesNotExist:
            pass
        except ChatRoom.DoesNotExist:
            pass

    async def disconnect(self, close_code):
        await self.reset_unread_count()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data_json = json.loads(text_data)

        result = await self.new_message(data_json)

        await self.channel_layer.group_send(
            self.room_group_name, result
        )

    async def private_message(self, event):
        user_id = event['user_id']
        nickname = event['nickname']
        message = event['message']

        await self.send(text_data=json.dumps({
                "user_id": user_id,
                "nickname": nickname,
                "message": message,
            }, ensure_ascii=False))

    @database_sync_to_async
    def new_message(self, data_json):
        user_id = data_json['user_id']
        chatroom_id = data_json['chatroom_id']
        message = data_json['message']

        try:
            user = Player.objects.get(id=user_id)
            chatroom = ChatRoom.objects.get(id=chatroom_id)
            Message.objects.create(
                chatroom = chatroom,
                sender = user,
                message = message,
                is_read = False
            )

            return {
                "type": "private.message",
                "user_id": user_id,
                "nickname": user.nickname,
                "message": message
            }
        except Player.DoesNotExist:
            pass
        except ChatRoom.DoesNotExist:
            pass