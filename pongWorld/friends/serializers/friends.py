from rest_framework import serializers

from ..models import Friend
from player.models import Player

class UserSerializer(serializers.ModelSerializer):

    is_online = serializers.SerializerMethodField()

    class Meta:
        model = Player
        profile_img = serializers.ImageField(use_url=True)
        fields = ['id', 'nickname', 'profile_img', 'is_online']

    def get_is_online(self, obj):
        return obj.online_count > 0

class FriendSerializer(serializers.ModelSerializer):

    user = serializers.SerializerMethodField()
    # TODO 게임 신청 보낼 수 있는 상태인지 추가

    class Meta:
        model = Friend
        fields = ['id', 'user', 'are_we_friend']

    def get_user(self, obj):
        request = self.context.get('request')
        if request:
            user_id = request.user.id
            if obj.follower.id == user_id:
                return UserSerializer(obj.followed, context={'request': request}).data
            elif obj.followed.id == user_id:
                return UserSerializer(obj.follower, context={'request': request}).data
        return None
