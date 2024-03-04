from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/connection/', consumers.ConnectConsumer.as_asgi()),
]