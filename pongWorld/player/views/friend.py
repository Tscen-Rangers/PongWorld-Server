from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import Friend, Player
from ..serializers import FriendSerializer
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

class FriendReqResView(viewsets.ModelViewSet):
    queryset = Friend.objects.all()
    serializer_class = FriendSerializer

    @extend_schema(request=None)
    def request_friend(self, request, followed_id):
        # 친구 신청 로직을 구현
        follower = request.user
        if followed_id is not None:
            try:
                followed = Player.objects.get(id=followed_id)
            except Player.DoesNotExist:
                return Response({'error': 'Player does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Followed ID is missing'}, status=status.HTTP_400_BAD_REQUEST)


        # 신청하는 사용자와 수락하는 사용자가 같은지 확인
        if follower == followed:
            return Response({'error': 'Cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)

        # 이미 친구인지 확인
        if (Friend.objects.filter(follower=follower.id, followed=followed.id, are_we_friend=True).exists()) or \
            Friend.objects.filter(follower=followed.id, followed=follower.id, are_we_friend=True).exists():
            return Response({'error': 'Already friend'}, status=status.HTTP_400_BAD_REQUEST)
        elif Friend.objects.filter(follower=follower.id, followed=followed.id, are_we_friend=False).exists() or \
            Friend.objects.filter(follower=followed.id, followed=follower.id, are_we_friend=False).exists():
            return Response({'error': 'Already sent a friend request'}, status=status.HTTP_400_BAD_REQUEST)
            
        friend_instance = Friend(follower=follower, followed=followed, are_we_friend=False)
        friend_instance.save()

        # serializer를 사용하여 response 데이터 생성
        serializer = FriendSerializer(friend_instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(request=None)
    def response_friend(self, request, friend_id):
        followed = request.user
        if friend_id is not None:
            try:
                friend = Friend.objects.get(id=friend_id)
            except Friend.DoesNotExist:
                return Response({'error': 'Friend does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Invalid friend request'}, status=status.HTTP_400_BAD_REQUEST)

        # 나에게 온 친구 신청이 아닐 때
        if friend.followed != followed:
            return Response({'error': 'You do not have permission to accept friend applications.'}, status=status.HTTP_400_BAD_REQUEST)

        # 이미 친구인지 확인
        if friend.are_we_friend:
            return Response({'error': 'Already friends'}, status=status.HTTP_400_BAD_REQUEST)

        # 수락 or 삭제
        if request.method == "PATCH":
            # 친구 신청을 수락하고 상태를 업데이트
            friend.are_we_friend = True
            friend.save()
            return Response({'message': 'Friend request accepted'}, status=status.HTTP_200_OK)
        elif request.method == "DELETE":
            # 친구 신청 삭제
            friend.delete()
            return Response({'message': 'Friend request rejected'}, status=status.HTTP_200_OK)
