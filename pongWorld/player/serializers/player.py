from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.utils import OpenApiTypes
from django.db.models import Q

from ..models import Player
from friends.models import Friend
from blocks.models import Block

class PlayerSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        profile_img = serializers.ImageField(use_url=True)
        fields = ["nickname", "profile_img", "intro"]

class PlayerSerializer(serializers.ModelSerializer):
    is_online = serializers.SerializerMethodField()
    ranking = serializers.SerializerMethodField()

    class Meta:
        model = Player
        profile_img = serializers.ImageField(use_url=True)
        fields = ["id", "nickname", "email", "profile_img", "intro", "ranking", "matches", "wins", "total_score", "is_online"]
        extra_kwargs = {
            "id": {"read_only": True},
            "email": {"read_only": True},
            "ranking": {"read_only": True},
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

    def get_ranking(self, obj) -> int:
        
        player_score = obj.total_score
        # 특정 플레이어보다 높은 점수를 가진 플레이어 수를 계산합니다.
        higher_rank_count = Player.objects.filter(total_score__gt=player_score).count()

        # 특정 플레이어의 순위를 계산합니다.
        player_rank = higher_rank_count + 1

        return player_rank

    @extend_schema_field(OpenApiTypes.INT)
    def get_id(self, obj):
        return id

class PlayerProfileSerializer(serializers.ModelSerializer):
    is_online = serializers.SerializerMethodField()
    ranking = serializers.SerializerMethodField()
    friend_status = serializers.SerializerMethodField()
    is_blocking = serializers.SerializerMethodField()

    class Meta:
        model = Player
        profile_img = serializers.ImageField(use_url=True)
        fields = ["id", "nickname", "email", "profile_img", "intro", "ranking", "matches", "wins", "total_score", "is_online",  "friend_status", "is_blocking"]
        extra_kwargs = {
            "id": {"read_only": True},
            "email": {"read_only": True},
            "ranking": {"read_only": True},
            "matches": {"read_only": True},
            "wins": {"read_only": True},
            "total_score": {"read_only": True},
            "updated_at": {"read_only": True},
        }

    def get_is_online(self, obj) -> bool:
        return obj.online_count > 0

    def get_ranking(self, obj) -> int:
        
        player_score = obj.total_score
        # 특정 플레이어보다 높은 점수를 가진 플레이어 수를 계산합니다.
        higher_rank_count = Player.objects.filter(total_score__gt=player_score).count()

        # 특정 플레이어의 순위를 계산합니다.
        player_rank = higher_rank_count + 1

        return player_rank

    def get_friend_status(self, obj) -> int:
        me = self.context['request'].user
        try:
            friend = Friend.objects.get(Q(follower=me, followed=obj) | Q(follower=obj, followed=me))
            if friend.are_we_friend:
                return 2  # friend
            else:
                return 1  # send request
        except Friend.DoesNotExist:
            return 0  # None

    def get_is_blocking(self, obj) -> bool:
        user = self.context['request'].user
        try:
            block = Block.objects.get(blocker=user, blocked=obj)
            return True # block
        except Block.DoesNotExist:
            return False  # unblock

class SearchPlayerSerializer(serializers.ModelSerializer):
    is_online = serializers.SerializerMethodField()
    friend_status = serializers.SerializerMethodField()
    is_blocking = serializers.SerializerMethodField()
    friend_id = serializers.SerializerMethodField()

    class Meta:
        model = Player
        profile_img = serializers.ImageField(use_url=True)
        fields = ["id", "nickname", "profile_img", "is_online", "friend_status", "is_blocking", "friend_id"]

    def get_is_online(self, obj) -> bool:
        return obj.online_count > 0

    def get_friend_status(self, obj) -> int:
        me = self.context['request'].user
        try:
            friend = Friend.objects.get(Q(follower=me, followed=obj) | Q(follower=obj, followed=me))
            if friend.are_we_friend:
                return 2  # friend
            else:
                return 1  # send request
        except Friend.DoesNotExist:
            return 0  # None

    def get_is_blocking(self, obj) -> bool:
        user = self.context['request'].user
        try:
            block = Block.objects.get(blocker=user, blocked=obj)
            return True # block
        except Block.DoesNotExist:
            return False  # unblock

    def get_friend_id(self, obj) -> int:
        me = self.context['request'].user
        try:
            friend = Friend.objects.get(Q(follower=me, followed=obj) | Q(follower=obj, followed=me))
            return friend.id
        except Friend.DoesNotExist:
            return 0  # None
