from drf_spectacular.utils import extend_schema
from rest_framework import generics, viewsets, status
from rest_framework.pagination import CursorPagination
from django.http import Http404
from rest_framework.response import Response
from django.core.files.storage import default_storage
import os
from django.conf import settings

from ..models import Player
from ..serializers import PlayerSettingSerializer, PlayerSerializer, SearchPlayerSerializer
from game.models import Game
from game.serializers import GameSerializer


class PlayerSettingView(viewsets.ModelViewSet):
    serializer_class = PlayerSettingSerializer

    def get_queryset(self):
        return Player.objects.filter(id=self.request.user.id)

    def get_user_info(self, request):
        try:
            user_id = request.user.id
            user = Player.objects.get(id=user_id)
            serializer = self.get_serializer(user, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Player.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)

    def set_user_info(self, request, pk):
        try:
            user = self.get_queryset()

            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # 업데이트된 정보를 시리얼라이즈하여 반환
            updated_user = Player.objects.get(id=user_id)
            updated_serializer = self.get_serializer(updated_user, context={'request': request})
            return Response(updated_serializer.data, status=status.HTTP_200_OK)
        except Player.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
            
    def withdraw(self, request):
        try:
            user_id = request.user.id
            user = Player.objects.get(id=user_id)

            # delete user profile image from media
            profile_img_path = str(user.profile_img)
            full_profile_img_path = os.path.join(settings.MEDIA_ROOT, profile_img_path)
            if full_profile_img_path and default_storage.exists(full_profile_img_path):
                default_storage.delete(full_profile_img_path)

            user.delete()

            return Response({'message': 'User successfully withdrawn'}, status=status.HTTP_200_OK)
        except Player.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
class CustomPlayerPagination(CursorPagination):
    page_size = 30
    ordering = '-last_login_time'
class OnlinePlayerListView(generics.ListAPIView):
    serializer_class = PlayerSerializer
    pagination_class = CustomPlayerPagination

    def get_queryset(self):
        user_id = self.request.user.id
        return Player.objects.filter(online_count__gt=0).exclude(id=user_id)

class PlayerProfileView(viewsets.ModelViewSet):
    serializer_class = PlayerSerializer

    @extend_schema(operation_id='get_my_profile')
    def get_my_profile(self, request):
        me = request.user

        current_user = Player.objects.get(id=me.id)
        serializer = PlayerSerializer(current_user)
        games = (Game.objects.filter(player1=me) | Game.objects.filter(player2=me)) & Game.objects.filter(status=2)
        if games.exists():  # 게임이 하나도 없을 때 예외 처리
            games = games.order_by('-created_at')[:3]
            game_serializer = GameSerializer(games, many=True, context={'request': request, 'user_id': current_user.id})
            games_data = game_serializer.data
        else:
            return Response({'player': serializer.data, 'games': 'No game'}, status=status.HTTP_200_OK)

        return Response({'player': serializer.data, 'games': games_data}, status=status.HTTP_200_OK)

    @extend_schema(operation_id='get_player_profile')
    def get_player_profile(self, request, user_id, game_record_type):
        me = request.user

        if user_id is not None:
            try:
                user = Player.objects.get(id=user_id)
                serializer = PlayerSerializer(user, context={'request': request})
            except Player.DoesNotExist:
                return Response({'error': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'User ID is missing'}, status=status.HTTP_400_BAD_REQUEST)

        if game_record_type == 0: # total
            games = (Game.objects.filter(player1=user) | Game.objects.filter(player2=user)) & Game.objects.filter(status=2)
            if games.exists():  # 게임이 하나도 없을 때 예외 처리
                games = games.order_by('-created_at')[:3]
                game_serializer = GameSerializer(games, many=True, context={'request': request, 'user_id': user_id})
                games_data = game_serializer.data
            else:
                return Response({'player': serializer.data, 'games': 'No game'}, status=status.HTTP_200_OK)
        elif game_record_type == 1: # with me
            games = (Game.objects.filter(player1=me, player2=user) | Game.objects.filter(player1=user, player2=me)) & Game.objects.filter(status=2)
            if games.exists():  # 게임이 하나도 없을 때 예외 처리
                games = games.order_by('-created_at')[:3]
                game_serializer = GameSerializer(games, many=True, context={'request': request, 'user_id': user_id})
                games_data = game_serializer.data
            else:
                return Response({'player': serializer.data, 'games': 'No game'}, status=status.HTTP_200_OK)
    
        return Response({'player': serializer.data, 'games': games_data}, status=status.HTTP_200_OK)


class SearchUserView(viewsets.ModelViewSet):
    serializer_class = SearchPlayerSerializer

    @extend_schema(operation_id='search_players_by_name')
    def get_users(self, request, name):
        me = request.user

        # 'name'을 포함한 nickname을 가진 플레이어들을 쿼리
        users = Player.objects.filter(nickname__icontains=name, is_superuser=False).exclude(id=me.id).order_by('nickname')

        serializer = SearchPlayerSerializer(users, many=True, context={'request': request})
    
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(operation_id='search_players')
    def get_all_users(self, request):
        me = request.user

        users = Player.objects.filter(is_superuser=False).exclude(id=me.id).order_by('nickname')

        serializer = SearchPlayerSerializer(users, many=True, context={'request': request})
    
        return Response(serializer.data, status=status.HTTP_200_OK)






        

        

        

