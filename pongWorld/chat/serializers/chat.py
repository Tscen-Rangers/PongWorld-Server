from rest_framework import serializers
from typing import Optional

from ..models import ChatRoom, Message

class ChatRoomSerializer(serializers.ModelSerializer):
    unread_count = serializers.SerializerMethodField()
    user1_nickname = serializers.SerializerMethodField()
    user2_nickname = serializers.SerializerMethodField()
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
            if obj.user2:
                return obj.msg_count_2
            else:
                return 0
        else:
            if obj.user1:
                return obj.msg_count_1
            else:
                return 0

    def get_user_nickname(self, user) -> Optional[str]:
        return user.nickname if user else None

    def get_user1_nickname(self, obj) -> Optional[str]:
        return self.get_user_nickname(obj.user1)

    def get_user2_nickname(self, obj) -> Optional[str]:
        return self.get_user_nickname(obj.user2)

    def get_user_profile_img(self, obj, user) -> Optional[str]:
        request = self.context.get('request')
        if request and user and user.profile_img:
            return request.build_absolute_uri(user.profile_img.url)
        return None

    def get_user1_profile_img(self, obj) -> Optional[str]:
        return self.get_user_profile_img(obj, obj.user1)

    def get_user2_profile_img(self, obj) -> Optional[str]:
        return self.get_user_profile_img(obj, obj.user2)

    def get_user_is_online(self, user) -> bool:
        return user.online_count > 0 if user else False

    def get_user1_is_online(self, obj) -> bool:
        return self.get_user_is_online(obj.user1)

    def get_user2_is_online(self, obj) -> bool:
        return self.get_user_is_online(obj.user2)

class MessageSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField()
    class Meta:
        model = Message
        fields = ['id', 'chatroom', 'sender', 'nickname', 'message', 'created_at']
        read_only_fields = ['id', 'chatroom', 'sender', 'nickname', 'message', 'created_at']

    def get_nickname(self, obj) -> Optional[str]:
        return obj.sender.nickname if obj.sender else None
