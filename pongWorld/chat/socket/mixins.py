import json

from channels.db import database_sync_to_async
from django.utils import timezone

from chat.models import ChatRoom, Message
from player.models import Player

class ChatMixin:
    async def handle_public_chat(self, text_data_json):
        user = self.user
        message = text_data_json.get('message')
        if message is None:
            await self.send_error_message("Message not provided")
            return

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
            "type": "public_chat",
            "user_id": user_id,
            "nickname": nickname,
            "message": message,
            "time": time,
        }, ensure_ascii=False))

    async def handle_private_chat(self, text_data_json):
        status = text_data_json.get('status')
        if status is None:
            await self.send_error_message("Status not provided")
            return

        if status == 'enter':
            await self.enter_private_chat(text_data_json)
        elif status == 'leave':
            await self.leave_private_chat()
        elif status == 'message':
            await self.message_private_chat(text_data_json)

    async def enter_private_chat(self, text_data_json):
        receiver_id = text_data_json.get('receiver_id')
        if receiver_id is None:
            await self.send_error_message("Receiver id not provided")
            return

        self.chatroom, created = await self.get_or_create_chatroom(receiver_id)
        if self.chatroom is None:
            await self.send_error_message("Chatroom creation failed.")
            return
        if not created:
            await self.reset_unread_count()

        self.private_room_group = f'chat_private_{self.chatroom.id}'
        await self.channel_layer.group_add(self.private_room_group, self.channel_name)

    async def leave_private_chat(self):
        await self.channel_layer.group_discard(self.private_room_group, self.channel_name)
        self.chatroom = None

    async def message_private_chat(self, text_data_json):
        result = await self.new_message(text_data_json)
        if result is None:
            await self.send_error_message("Message not provided")
            return

        await  self.channel_layer.group_send(
            self.private_room_group, result
        )

    async def private_message(self, event):
        user_id = event['user_id']
        nickname = event['nickname']
        message = event['message']
        time = event['time']

        await self.send(text_data=json.dumps({
                "type": "private_chat",
                "user_id": user_id,
                "nickname": nickname,
                "message": message,
                "time": time,
            }, ensure_ascii=False))
        await self.reset_unread_count()

    @database_sync_to_async
    def get_or_create_chatroom(self, receiver_id):
        sorted_ids = sorted([self.user.id, receiver_id])

        try:
            user1 = Player.objects.get(id=sorted_ids[0])
            user2 = Player.objects.get(id=sorted_ids[1])

            chatroom, created = ChatRoom.objects.get_or_create(
                user1=user1, user2=user2,
                defaults={
                    'last_sender': user1,
                    'unread_count': 0,
                    'last_send_time': timezone.now()
                }
            )
            return chatroom, created
        except Player.DoesNotExist:
            return None, False
        except Exception:
            return None, False

    @database_sync_to_async
    def reset_unread_count(self):
        chatroom = self.chatroom
        sender = self.user
        if chatroom.last_sender != sender:
            chatroom.unread_count = 0
            chatroom.save()

    @database_sync_to_async
    def new_message(self, data_json):
        message = data_json.get('message')
        if message is None:
            return None

        user = self.user
        chatroom = self.chatroom
        new_message = Message.objects.create(
            chatroom = chatroom,
            sender = user,
            message = message,
        )
        formatted_date = new_message.created_at.strftime('%Y-%m-%d %H:%M:%S')

        return {
            "type": "private.message",
            "user_id": user.id,
            "nickname": user.nickname,
            "message": message,
            "time": formatted_date
        }
