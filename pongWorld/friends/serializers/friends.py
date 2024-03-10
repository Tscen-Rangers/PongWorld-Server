from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ..models import Friend
from player.models import Player

class UserSerializer(serializers.ModelSerializer):

    is_online = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = ['id', 'nickname', 'profile_img', 'is_online']

    def get_is_online(self, obj) -> bool:
        return obj.online_count > 0

class FriendSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    # TODO 게임 신청 보낼 수 있는 상태인지 추가

    class Meta:
        model = Friend
        fields = ['id', 'user', 'are_we_friend']

    @extend_schema_field(UserSerializer(many=False))
    def get_user(self, obj):
        request = self.context.get('request')
        if request:
            user_id = request.user.id
            if obj.follower.id == user_id:
                return UserSerializer(obj.followed).data
            elif obj.followed.id == user_id:
                return UserSerializer(obj.follower).data
        return None
