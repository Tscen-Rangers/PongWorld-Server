from rest_framework import generics, permissions

from ..models import Player
from ..serializers import PlayerSerializer


class PlayerListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny,]
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer
    pagination_class = None


class PlayerRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny,]
    http_method_names = ['patch', 'delete']
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer
    pagination_class = None
