from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.shortcuts import get_object_or_404

from ..models import ChatRoom, Message
from ..serializers import ChatRoomSerializer, MessageSerializer

class ChatRoomList(ListAPIView):
    serializer_class = ChatRoomSerializer

    def get_queryset(self):
        player_id = self.request.user.id
        return ChatRoom.objects.filter(Q(user1_id=player_id) & Q(is_user1_in=True) | Q(user2_id=player_id) & Q(is_user2_in=True)).order_by('-last_send_time')

    def get_serializer_context(self):
        return {'request': self.request}

class LeaveChatRoom(APIView):
    def post(self, request, chatroom_id):
        user = request.user
        chatroom = get_object_or_404(ChatRoom, pk=chatroom_id)

        if chatroom.user1 == user:
            chatroom.is_user1_in = False
        else:
            chatroom.is_user2_in = False
        chatroom.save()
        return Response({"message": "You have successfully left the chat room."}, status=status.HTTP_200_OK)




class CustomPagination(CursorPagination):
    page_size = 50
    ordering = '-created_at'
class MessageList(ListAPIView):
    serializer_class = MessageSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        chatroom_id = self.kwargs['chatroom_id']
        chatroom = ChatRoom.objects.get(pk = chatroom_id)

        if chatroom.user1 == user and chatroom.is_user1_in:
            participate_time = chatroom.user1_participate_time
        elif chatroom.user2 == user and chatroom.is_user2_in:
            participate_time = chatroom.user2_participate_time
        else:
            return Message.objects.none()

        return Message.objects.filter(chatroom_id=chatroom_id, created_at__gte=participate_time)
