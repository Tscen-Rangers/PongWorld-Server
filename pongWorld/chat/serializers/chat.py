from rest_framework import serializers

from ..models import ChatRoom, Message

class ChatRoomSerializer(serializers.ModelSerializer):
    unread_count = serializers.SerializerMethodField()
    class Meta:
        model = ChatRoom
        fields = ['id', 'user1', 'user1_nickname', 'user1_profile_img', 'user2', 'user2_nickname', 'user2_profile_img', 'unread_count']
        read_only_fields = ['id', 'user1', 'user2', 'created_at', 'updated_at']

    user1_nickname = serializers.CharField(source='user1.nickname', read_only=True)
    user2_nickname = serializers.CharField(source='user2.nickname', read_only=True)
    user1_profile_img = serializers.URLField(source='user1.profile_img', read_only=True)
    user2_profile_img = serializers.URLField(source='user2.profile_img', read_only=True)

    def get_unread_count(self, obj) -> int:
        request = self.context.get('request')
        if request:
            user = request.user
        else:
            return 0
        if obj.user1 == user:
            return obj.msg_count_2
        else:
            return obj.msg_count_1
class MessageSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField()
    class Meta:
        model = Message
        fields = ['id', 'chatroom', 'sender', 'nickname', 'message', 'created_at']
        read_only_fields = ['id', 'chatroom', 'sender', 'nickname', 'message', 'created_at']

    def get_nickname(self, obj) -> str:
        return obj.sender.nickname
