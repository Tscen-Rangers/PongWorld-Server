from rest_framework import generics
from rest_framework.pagination import CursorPagination
from django.http import Http404

from ..models import Player
from ..serializers import PlayerSerializer

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

