from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import Friend
from player.models import Player
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

    @extend_schema(request=None)
    def send_req_list(self, request):
        user = request.user  # 현재 요청을 보낸 사용자

        # 현재 사용자를 follower로 갖는 Friend 객체들을 가져옴
        followers = Friend.objects.filter(follower=user, are_we_friend=False)

        # 가져온 객체들을 시리얼라이즈
        serializer = self.get_serializer(followers, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=None)
    def receive_req_list(self, request):
        user = request.user  # 현재 요청을 보낸 사용자

        # 현재 사용자를 followed로 갖는 Friend 객체들을 가져옴
        followeds = Friend.objects.filter(followed=user, are_we_friend=False)

        # 가져온 객체들을 시리얼라이즈
        serializer = self.get_serializer(followeds, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=None)
    def friends_list(self, request):
        user = request.user  # 현재 요청을 보낸 사용자

        # 현재 사용자를 follower로 갖는 Friend 객체들을 가져옴
        friends = Friend.objects.filter(are_we_friend=True)

        # 가져온 객체들을 시리얼라이즈
        serializer = self.get_serializer(friends, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=None)
    def get_friend_request_count(self, request):
        user = request.user  # 현재 요청을 보낸 사용자

        # 현재 사용자를 followed로 갖는 Friend 객체들을 가져옴
        followeds = Friend.objects.filter(followed=user, are_we_friend=False)

        followeds_count = followeds.count()

        return Response({'request_cnt': followeds_count}, status=status.HTTP_200_OK)

