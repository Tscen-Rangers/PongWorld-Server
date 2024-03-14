from rest_framework import serializers
from typing import Optional

from ..models import ChatRoom, Message

class ChatRoomSerializer(serializers.ModelSerializer):
    unread_count = serializers.SerializerMethodField()
    user1_nickname = serializers.CharField(source='user1.nickname', read_only=True)
    user2_nickname = serializers.CharField(source='user2.nickname', read_only=True)
    user1_profile_img = serializers.SerializerMethodField()
    user2_profile_img = serializers.SerializerMethodField()
    user1_is_online = serializers.SerializerMethodField()
    user2_is_online = serializers.SerializerMethodField()


    class Meta:
        model = ChatRoom
        fields = ['id', 'user1', 'user1_nickname', 'user1_profile_img', 'user1_is_online', 'user2', 'user2_nickname', 'user2_profile_img', 'user2_is_online', 'unread_count']
        read_only_fields = ['id', 'user1', 'user2', 'created_at', 'updated_at']

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

    def get_user1_profile_img(self, obj) -> Optional[str]:
        request = self.context.get('request')
        if request and obj.user1.profile_img:
            return request.build_absolute_uri(obj.user1.profile_img.url)
        else:
            return None

    def get_user2_profile_img(self, obj) -> Optional[str]:
        request = self.context.get('request')
        if request and obj.user2.profile_img:
            return request.build_absolute_uri(obj.user2.profile_img.url)
        else:
            return None

    def get_user1_is_online(self, obj) -> bool:
        return obj.user1.online_count > 0

    def get_user2_is_online(self, obj) -> bool:
        return obj.user2.online_count > 0

class MessageSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField()
    class Meta:
        model = Message
        fields = ['id', 'chatroom', 'sender', 'nickname', 'message', 'created_at']
        read_only_fields = ['id', 'chatroom', 'sender', 'nickname', 'message', 'created_at']

    def get_nickname(self, obj) -> str:
        return obj.sender.nickname
