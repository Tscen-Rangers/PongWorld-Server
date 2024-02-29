from rest_framework.generics import ListAPIView
from rest_framework.pagination import CursorPagination
from django.db.models import Q

from ..models import ChatRoom, Message
from ..serializers import ChatRoomSerializer, MessageSerializer

class ChatRoomList(ListAPIView):
    serializer_class = ChatRoomSerializer

    def get_queryset(self):
        player_id = self.request.user.id
        return ChatRoom.objects.filter(Q(user1_id=player_id) | Q(user2_id=player_id)).order_by('-last_send_time')

class CustomPagination(CursorPagination):
    page_size = 50
    ordering = 'created_at'
class MessageList(ListAPIView):
    serializer_class = MessageSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        chatroom_id = self.kwargs['chatroom_id']
        return Message.objects.filter(chatroom_id=chatroom_id)
