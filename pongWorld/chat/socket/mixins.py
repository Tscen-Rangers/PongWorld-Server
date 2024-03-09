import json

from channels.db import database_sync_to_async
from django.db import transaction
from django.db.models import F
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
                "created_at": timezone.now().isoformat(),
            }
        )

    async def public_message(self, event):
        user_id = event['user_id']
        nickname = event['nickname']
        message = event['message']
        created_at = event['created_at']

        await self.send(text_data=json.dumps({
            "type": "public_chat",
            "user_id": user_id,
            "nickname": nickname,
            "message": message,
            "created_at": created_at,
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
        self.chat_receiver_id = text_data_json.get('receiver_id')
        if self.chat_receiver_id is None:
            await self.send_error_message("Receiver id not provided")
            return

        self.chatroom, created = await self.get_or_create_chatroom(self.chat_receiver_id)
        if self.chatroom is None:
            await self.send_error_message("Chatroom creation failed.")
            return
        if not created:
            await self.reset_unread_count()

        self.private_room_group = f'chat_private_{self.chatroom.id}'
        await self.channel_layer.group_add(self.private_room_group, self.channel_name)
        await self.send(text_data=json.dumps({
            "chatroom_id": self.chatroom.id
        }))
        await self.reset_unread_count()

    async def leave_private_chat(self):
        await self.reset_unread_count()
        await self.channel_layer.group_discard(self.private_room_group, self.channel_name)
        self.chatroom = None
        self.chat_receiver_id = None

    async def message_private_chat(self, text_data_json):
        result = await self.new_message(text_data_json)
        if result is None:
            await self.send_error_message("Message not provided")
            return

        await self.update_chatroom()

        await  self.channel_layer.group_send(
            self.private_room_group, result
        )

        receiver_group = f'player_{self.chat_receiver_id}'

        if self.chatroom.user1 == self.user:
            unread_count = self.chatroom.msg_count_1
        else:
            unread_count = self.chatroom.msg_count_2

        await self.channel_layer.group_send(
            receiver_group, {
                "type": "send.unread.count",
                "chatroom_id": self.chatroom.id,
                "sender_id": self.user.id,
                "sender_nickname": self.user.nickname,
                "unread_count": unread_count
            }
        )

    async def send_unread_count(self, event):
        await self.send(text_data=json.dumps({
            "type": "unread_count",
            "chatroom_id": event['chatroom_id'],
            "sender_id": event['sender_id'],
            "sender_nickname": event['sender_nickname'],
            "unread_count": event['unread_count']
        }))

    async def private_message(self, event):
        user_id = event['user_id']
        nickname = event['nickname']
        message = event['message']
        created_at = event['created_at']

        await self.send(text_data=json.dumps({
                "type": "private_chat",
                "user_id": user_id,
                "nickname": nickname,
                "message": message,
                "created_at": created_at,
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
    def reset_unread_count_sync(self):
        with transaction.atomic():
            chatroom = ChatRoom.objects.select_for_update().get(id=self.chatroom.id)

            if chatroom.user1 == self.user:
                chatroom.msg_count_2 = 0
            else :
                chatroom.msg_count_1 = 0
            chatroom.save()
    async def reset_unread_count(self):
        await self.reset_unread_count_sync()

    @database_sync_to_async
    def update_chatroom_sync(self):
        with transaction.atomic():
            chatroom = ChatRoom.objects.select_for_update().get(id=self.chatroom.id)
            chatroom.last_send_time = timezone.now()
            if chatroom.user1 == self.user:
                chatroom.msg_count_1 = F('msg_count_1') + 1
            else:
                chatroom.msg_count_2 = F('msg_count_2') + 1
            chatroom.save()

    async def update_chatroom(self):
        await self.update_chatroom_sync()

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

        return {
            "type": "private.message",
            "user_id": user.id,
            "nickname": user.nickname,
            "message": message,
            "created_at": new_message.created_at.isoformat()
        }
