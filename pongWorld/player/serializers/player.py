from rest_framework import serializers

from ..models import Player
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.utils import OpenApiTypes


class PlayerSerializer(serializers.ModelSerializer):
    is_online = serializers.SerializerMethodField()

    class Meta:
        model = Player
        profile_img = serializers.ImageField(use_url=True)
        fields = ["id", "nickname", "email", "profile_img", "intro", "matches", "wins", "total_score", "is_online"]
        extra_kwargs = {
            "id": {"read_only": True},
            "email": {"read_only": True},
            "matches": {"read_only": True},
            "wins": {"read_only": True},
            "total_score": {"read_only": True},
            "updated_at": {"read_only": True},
        }

        def validate_nickname(self, value):
            instance_id = self.instance.id if self.instance else None

            if Player.objects.filter(nickname=value).exclude(id=instance_id).exists():
                raise serializers.ValidationError("This nickname already exists.")

    def get_is_online(self, obj):
        return obj.online_count > 0

    @extend_schema_field(OpenApiTypes.INT)
    def get_id(self, obj):
        return id