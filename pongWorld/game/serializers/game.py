from rest_framework import serializers
from player.models import Player 
from game.models import Game, Tournament
from django.utils import timezone
import humanize
from typing import Optional
from config.utils import CommonUtils


class PlayerSerializer(serializers.ModelSerializer):

    player_profile_img = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = ['nickname', 'player_profile_img', 'total_score']

    def get_player_profile_img(self, player):
        if player.profile_img:
            # Get the absolute URL using build_absolute_uri
            return CommonUtils.get_full_url(player.profile_img.url)
        return None
        
class GameRoomSerializer(serializers.ModelSerializer):

    player1 = PlayerSerializer()
    player2 = PlayerSerializer()

    class Meta:
        model = Game
        fields = ['id', 'speed', 'status', 'player1', 'player2']

    def to_representation(self, instance):
        data = super().to_representation(instance)

        players_data = []
        player_data = data.get('player1')
        players_data.append(player_data)
        player_data = data.get('player2')
        players_data.append(player_data)

        data['players'] = players_data
        del data['player1']
        del data['player2']

        return data

class TournamentRoomSerializer(serializers.ModelSerializer):
    
    player1 = PlayerSerializer()
    player2 = PlayerSerializer()
    player3 = PlayerSerializer()
    player4 = PlayerSerializer()

    class Meta:
        model = Tournament
        fields = ['id', 'player1', 'player2', 'player3', 'player4']

    def to_representation(self, instance):
        data = super().to_representation(instance)

        players_data = []
        player_data = data.get('player1')
        players_data.append(player_data)
        player_data = data.get('player2')
        players_data.append(player_data)
        player_data = data.get('player3')
        players_data.append(player_data)
        player_data = data.get('player4')
        players_data.append(player_data)

        data['players'] = players_data
        del data['player1']
        del data['player2']
        del data['player3']
        del data['player4']

        return data

class GameSerializer(serializers.ModelSerializer):

    player1 = PlayerSerializer()
    player2 = PlayerSerializer()
    who_is_user = serializers.SerializerMethodField()
    is_win = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = ['player1', 'player2', 'player1_score', 'player2_score', 'who_is_user', 'is_win', 'date']

    def get_who_is_user(self, obj):
        user_id = self.context.get('user_id', None)

        if user_id is None:
            return None
        if obj.player1.id == user_id:
            return 'player1'
        elif obj.player2.id == user_id:
            return 'player2'
        raise ValueError("Invalid user_id")
        
    def get_is_win(self, obj):
        user_id = self.context.get('user_id', None)

        if user_id is None:
            return None
        if user_id == obj.winner.id:
            return 1 # 승리
        else:
            return 0    # 패배
        raise ValueError("Invalid user_id")

    def get_date(self, obj):
        time_diff = timezone.now() - obj.created_at

        # 날짜를 사람이 읽기 쉬운 형태로 변환
        humanized_time = humanize.naturaltime(time_diff)

        return humanized_time