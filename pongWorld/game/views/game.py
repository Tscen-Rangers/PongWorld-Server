from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response

from ..models import Game
from ..serializers import GameSerializer
from player.models import Player
from player.serializers import PlayerSettingSerializer

class GameView(viewsets.ModelViewSet):

    def get_game_home_view(self, request):
        top5_players = Player.objects.order_by('-total_score')[:5]
        serializer = PlayerSettingSerializer(top5_players, many=True, context={'request': request})

        games = Game.objects.filter(status=2)
        if games.exists():  # 게임이 하나도 없을 때 예외 처리
            games = games.order_by('-created_at')[:10]
            game_serializer = GameSerializer(games, many=True)
            games_data = game_serializer.data
            return Response({'ranking': serializer.data, 'games': games_data}, status=status.HTTP_200_OK)
        return Response({'ranking': serializer.data, 'games': 'No game'}, status=status.HTTP_200_OK)