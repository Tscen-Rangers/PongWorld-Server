from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from player.models import Player
from friends.models import Friend
from chat.models import ChatRoom
from ..models import Block
from ..serializers import BlockSerializer
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import extend_schema

class BlocksView(viewsets.ModelViewSet):
    serializer_class = BlockSerializer

    @extend_schema(request=None)
    def block_user(self, request, to_block_id):
        me = request.user
        if to_block_id is not None:
            try:
                to_block = Player.objects.get(id=to_block_id)
            except Player.DoesNotExist:
                return Response({'error': 'Player does not exist'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Player ID is missing'}, status=status.HTTP_400_BAD_REQUEST)

        if me == to_block:
            return Response({'error': 'Cannot block yourself'}, status=status.HTTP_400_BAD_REQUEST)

        # 이미 block 했는지 확인
        if Block.objects.filter(blocker=me.id, blocked=to_block.id).exists():
            return Response({'error': 'Already blocked'}, status=status.HTTP_409_CONFLICT)
        
        block_instance = Block(blocker=me, blocked=to_block)
        block_instance.save()
        friend_query = Q(
            (Q(follower=me.id) & Q(followed=to_block.id)) |
            (Q(follower=to_block.id) & Q(followed=me.id))
        )
        try:
            friend_instance = Friend.objects.get(friend_query)
            friend_instance.delete()
        except ObjectDoesNotExist:
            pass

        chatroom_query = Q(user1_id=me.id) & Q(user2_id=to_block.id) | Q(user1_id=to_block.id) & Q(user2_id=me.id)
        try:
            chatroom_instance = ChatRoom.objects.get(chatroom_query)
            if chatroom_instance.user1 == me:
                chatroom_instance.is_user1_in = False
            else:
                chatroom_instance.is_user2_in = False
            chatroom_instance.save()
        except ObjectDoesNotExist:
            pass

        return Response({'message': f'You blocked user {to_block.nickname}.'}, status=status.HTTP_201_CREATED)

    @extend_schema(request=None)
    def unblocked_user(self, request, blocked_id):
        me = request.user
        if blocked_id is not None:
            try:
                blocked = Player.objects.get(id=blocked_id)
            except Player.DoesNotExist:
                return Response({'error': 'Player does not exist'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Blocked ID is missing'}, status=status.HTTP_400_BAD_REQUEST)

        # block 한 상태인지 확인
        if not Block.objects.filter(blocker=me.id, blocked=blocked.id).exists():
            return Response({'error': 'No record of blocking'}, status=status.HTTP_409_CONFLICT)
        
        blocks = Block.objects.get(blocker=me, blocked=blocked)
        blocks.delete()

        return Response({'message': f'You unblocked user {blocked.nickname}.'}, status=status.HTTP_204_NO_CONTENT)

class SearchBlockingView(viewsets.ModelViewSet):
    serializer_class = BlockSerializer

    @extend_schema(operation_id='search_friends')
    def get_blockings(self, request, name):
        me = request.user

        blocks = Block.objects.filter(blocked__nickname__icontains=name).order_by('blocked__nickname')

        serializer = self.get_serializer(blocks, many=True)
    
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=None)
    def get_all_blockings(self, request):
        me = request.user

        blocks = Block.objects.filter(blocker=me).order_by('blocked__nickname')

        # 가져온 객체들을 시리얼라이즈
        serializer = self.get_serializer(blocks, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
