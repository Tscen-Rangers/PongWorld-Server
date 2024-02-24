from django.urls import path

from . import consumers

chat_websocket_urlpatterns = [
    path('ws/chat/public/', consumers.PublicChatConsumer.as_asgi()),
    path('ws/chat/private/<int:user_id_1>/<int:user_id_2>/', consumers.PrivateChatConsumer.as_asgi()),
]