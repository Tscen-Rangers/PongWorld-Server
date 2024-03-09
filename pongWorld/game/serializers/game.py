from rest_framework import serializers
from player.models import Player 
from game.models import Game, Tournament
from django.utils import timezone
from django.contrib.humanize.templatetags import humanize


class PlayerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Player
        fields = ['nickname', 'profile_img', 'total_score']

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
    is_win = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = ['player1', 'player2', 'player1_score', 'player2_score', 'is_win', 'date']

    def get_is_win(self, obj):
        me = self.context['request'].user
        if me == obj.winner:
            return 1 # 승리
        return 0    # 패배

    def get_date(self, obj):
        time_diff = timezone.now() - obj.created_at

        # 날짜를 사람이 읽기 쉬운 형태로 변환
        humanized_time = humanize.naturaltime(time_diff)

        return humanized_time