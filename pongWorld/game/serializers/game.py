from rest_framework import serializers
from player.models import Player 
from game.models import Game 


class PlayerSerializer(serializers.ModelSerializer):

    profile_img = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = ['nickname', 'profile_img', 'total_score']

    @staticmethod
    def get_profile_img(player):
        return str(player.profile_img).split('/')[-1]

class GameRoomSerializer(serializers.ModelSerializer):

    player1 = PlayerSerializer()
    player2 = PlayerSerializer()

    class Meta:
        model = Game
        fields = ['player1', 'player2']

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