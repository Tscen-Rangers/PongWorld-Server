from rest_framework import serializers
from player.models import Player 
from game.models import Game, Tournament


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
        fields = ['player1', 'player2', 'player3', 'player4']

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