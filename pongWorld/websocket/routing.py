from django.urls import path

from chat.socket import consumers

chat_websocket_urlpatterns = [
    path('ws/connection/', consumers.ConnectConsumer.as_asgi()),
]