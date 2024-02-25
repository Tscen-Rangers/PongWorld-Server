from django.urls import path

from chat.socket import consumers

chat_websocket_urlpatterns = [
    path('ws/chat/public/', consumers.PublicChatConsumer.as_asgi()),
    path('ws/chat/private/<int:sender_id>/<int:receiver_id>/', consumers.PrivateChatConsumer.as_asgi()),
]