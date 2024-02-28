from rest_framework import serializers

class InputSerializer(serializers.Serializer):
    code = serializers.CharField()