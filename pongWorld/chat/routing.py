from django.urls import path

from . import consumers

chat_websocket_urlpatterns = [
    path('ws/chat/public/', consumers.PublicChatConsumer.as_asgi()),
]