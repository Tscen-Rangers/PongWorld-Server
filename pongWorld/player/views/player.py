from rest_framework import generics, viewsets, status
from rest_framework.pagination import CursorPagination
from django.http import Http404
from rest_framework.response import Response

from ..models import Player
from ..serializers import PlayerSerializer, SearchPlayerSerializer

class PlayerRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PlayerSerializer

    def get_object(self):
        try:
            user_id = self.request.user.id
            return Player.objects.get(id=user_id)
        except Player.DoesNotExist:
            raise Http404

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

    def get_player_profile(self, request, user_id):
        me = request.user

        if user_id is not None:
            try:
                user = Player.objects.get(id=user_id)
                serializer = PlayerSerializer(user)
            except Player.DoesNotExist:
                return Response({'error': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'User ID is missing'}, status=status.HTTP_400_BAD_REQUEST)

        # TODO 전적 추가할 때 내 프로필이랑 남의 프로필 나눠서 
        if me == user: # 내 프로필 볼 때 
            pass
        else:       # 남의 프로필 볼 때
            pass
        
        return Response(serializer.data, status=status.HTTP_200_OK)

class SearchUsers(viewsets.ModelViewSet):
    serializer_class = SearchPlayerSerializer

    def get_users(self, request, name):
        me = request.user

        # 'name'을 포함한 nickname을 가진 플레이어들을 쿼리
        users = Player.objects.filter(nickname__icontains=name)

        serializer = SearchPlayerSerializer(users, many=True, context={'request': request})
    
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_all_users(self, request):
        me = request.user

        users = Player.objects.filter()

        serializer = SearchPlayerSerializer(users, many=True, context={'request': request})
    
        return Response(serializer.data, status=status.HTTP_200_OK)







        

        

        

