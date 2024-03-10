from rest_framework import serializers

from ..models import Player
from friends.models import Friend
from blocks.models import Block
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.utils import OpenApiTypes

from django.db.models import Q


class PlayerSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        profile_img = serializers.ImageField(use_url=True)
        fields = ["nickname", "profile_img", "intro"]

class PlayerSerializer(serializers.ModelSerializer):
    is_online = serializers.SerializerMethodField()

    class Meta:
        model = Player
        profile_img = serializers.ImageField(use_url=True)
        fields = ["id", "nickname", "email", "profile_img", "intro", "matches", "wins", "total_score", "is_online"]
        extra_kwargs = {
            "id": {"read_only": True},
            "email": {"read_only": True},
            "matches": {"read_only": True},
            "wins": {"read_only": True},
            "total_score": {"read_only": True},
            "updated_at": {"read_only": True},
        }

        def validate_nickname(self, value):
            instance_id = self.instance.id if self.instance else None

            if Player.objects.filter(nickname=value).exclude(id=instance_id).exists():
                raise serializers.ValidationError("This nickname already exists.")

    def get_is_online(self, obj) -> bool:
        return obj.online_count > 0

    @extend_schema_field(OpenApiTypes.INT)
    def get_id(self, obj):
        return id

class SearchPlayerSerializer(serializers.ModelSerializer):
    is_online = serializers.SerializerMethodField()
    friend_status = serializers.SerializerMethodField()
    is_blocking = serializers.SerializerMethodField()

    class Meta:
        model = Player
        profile_img = serializers.ImageField(use_url=True)
        fields = ["id", "nickname", "profile_img", "is_online", "friend_status", "is_blocking"]

    def get_is_online(self, obj):
        return obj.online_count > 0

    def get_friend_status(self, obj):
        me = self.context['request'].user
        try:
            friend = Friend.objects.get(Q(follower=me, followed=obj) | Q(follower=obj, followed=me))
            if friend.are_we_friend:
                return 2  # friend
            else:
                return 1  # send request
        except Friend.DoesNotExist:
            return 0  # None

    def get_is_blocking(self, obj):
        user = self.context['request'].user
        try:
            block = Block.objects.get(blocker=user, blocked=obj)
            return True # block
        except Block.DoesNotExist:
            return False  # unblock