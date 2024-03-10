from rest_framework import serializers

from ..models import Block
from friends.serializers import UserSerializer

class BlockSerializer(serializers.ModelSerializer):
    blocked = UserSerializer()
    # TODO 게임 신청 보낼 수 있는 상태인지 추가

    class Meta:
        model = Block
        fields = ['id', 'blocked']
