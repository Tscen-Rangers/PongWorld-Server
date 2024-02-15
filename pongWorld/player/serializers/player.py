from rest_framework import serializers

from ..models import Player
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.utils import OpenApiTypes


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ["id", "nickname", "email", "profile_img", "intro", "matches", "wins", "total_score"]
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
        }

    @extend_schema_field(OpenApiTypes.INT)
    def get_id(self, obj):
        return id