from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from django.db.models import Q, Count

from ..models import Friend
from player.models import Player
from game.models import Game, Tournament

class UserSerializer(serializers.ModelSerializer):

    is_online = serializers.SerializerMethodField()

    class Meta:
        model = Player
        profile_img = serializers.ImageField(use_url=True)
        fields = ['id', 'nickname', 'profile_img', 'is_online']

    def get_is_online(self, obj) -> bool:
        return obj.online_count > 0

class FriendSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    is_battle_request_allowed = serializers.SerializerMethodField()

    class Meta:
        model = Friend
        fields = ['id', 'user', 'are_we_friend', 'is_battle_request_allowed']

    @extend_schema_field(UserSerializer(many=False))
    def get_user(self, obj):
        request = self.context.get('request')
        if request:
            user_id = request.user.id
            if obj.follower.id == user_id:
                return UserSerializer(obj.followed, context={'request': request}).data
            elif obj.followed.id == user_id:
                return UserSerializer(obj.follower, context={'request': request}).data
        return None

    def get_is_battle_request_allowed(self, obj):
        user_data = self.get_user(obj)
        if user_data:
            user_id = user_data['id']
            playing_game_cnt = Game.objects.filter(
                Q(player1_id=user_id) | Q(player2_id=user_id),
                ~Q(status=2)
            ).count()
            if playing_game_cnt > 0:
                return False
            
            playing_tournament_cnt = Tournament.objects.filter(
                Q(player1_id=user_id) | Q(player2_id=user_id) | Q(player3_id=user_id) | Q(player4_id=user_id),
                ~Q(status=2)
            ).count()
            if playing_tournament_cnt > 0:
                return False
            return True    # 배틀 신청 가능
        return None
        

