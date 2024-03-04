from rest_framework import serializers

from player.models import Player

class OAuthCodeSerializer(serializers.Serializer):
    code = serializers.CharField()

class OAuthPlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        profile_img = serializers.ImageField(use_url=True)
        fields = ['id', 'nickname', 'profile_img', 'intro']

class OAuthLoginURLSerializer(serializers.Serializer):
    oauth_login_url = serializers.CharField()

class OAuthCallbackSerailizer(serializers.Serializer):
    refresh_token = serializers.CharField()
    access_token = serializers.CharField()
    is_new_user = serializers.BooleanField()
    user = OAuthPlayerSerializer()