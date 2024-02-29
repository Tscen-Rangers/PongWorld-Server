from rest_framework import generics
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
