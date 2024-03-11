from django.db import models
from player.models import Player
from config.models import TimestampBaseModel

class ChatRoom(TimestampBaseModel):
    user1 = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='user1_chat_room')
    user2 = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='user2_chat_room')
    msg_count_1 = models.IntegerField(default=0) # user1이 보낸 메시지 수 (unread)
    msg_count_2 = models.IntegerField(default=0) # user2가 보낸 메시지 수 (unread)
    last_send_time = models.DateTimeField()

    class Meta:
        db_table = "chat_room"

    def __str__(self):
        return f"ChatRoom {self.id}"

class Message(TimestampBaseModel):
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    sender = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_messages')
    message = models.CharField(max_length=300)

    class Meta:
        db_table = "message"
