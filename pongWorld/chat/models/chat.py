from django.db import models
from player.models import Player
from config.models import TimestampBaseModel

class ChatRoom(TimestampBaseModel):
    user1 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='user1_chat_room')
    user2 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='user2_chat_room')
    last_sender = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='last_sent_chat_room')
    unread_count = models.IntegerField(default=0)
    last_send_time = models.DateTimeField()

    class Meta:
        db_table = "chat_room"

    def __str__(self):
        return f"ChatRoom {self.id}"

class Message(TimestampBaseModel):
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.CharField(max_length=300)

    class Meta:
        db_table = "message"

    def __str__(self):
            return f"Send by {self.sender.nickname}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.chatroom.last_send_time = self.created_at
        if self.sender == self.chatroom.last_sender:
            self.chatroom.unread_count += 1
        else:
            self.chatroom.last_sender = self.sender
            self.chatroom.unread_count = 1
        self.chatroom.save()
