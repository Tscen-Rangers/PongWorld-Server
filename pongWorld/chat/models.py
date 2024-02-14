from django.db import models
from player.models import Player

class ChatRoom(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_room"

    def __str__(self):
        return f"ChatRoom {self.id}"

class JoinChatRoom(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="joined_chat")
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="joined_player")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "join_chat"

    def __str__(self):
        return f"Player {self.player.nickname} joined {self.chatroom.id}"

class Message(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="message")
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="message")
    content = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "message"

    def __str__(self):
        return f"Send by {self.player.email}"

    def last_3_recent_messages(room_id):
        return Message.objects.filter(room_id=room_id).order_by('created_at')[:3]

class UnreadMessage(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="unread_message")
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="unread_message")
    unread_count = models.PositiveIntegerField()
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "unread_message"

    def __str__(self):
        return f"There is {self.unread_count} unread message"
