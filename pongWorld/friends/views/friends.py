from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from django.db.models import Q, F, CharField, Case, Value, When

from ..models import Friend
from player.models import Player
from blocks.models import Block
from ..serializers import FriendSerializer

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
                return Response({'error': 'Player does not exist'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Followed ID is missing'}, status=status.HTTP_400_BAD_REQUEST)

        # 신청하는 사용자와 수락하는 사용자가 같은지 확인
        if follower == followed:
            return Response({'error': 'Cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)

        # 차단 된 상태면 친추 신청이 안감
        if Block.objects.filter(blocker=followed, blocked=follower.id).exists():
            return Response({'message': 'Cannot follow. Follower blocked by followed.'}, status=status.HTTP_201_CREATED)

        # 이미 친구인지 확인
        if (Friend.objects.filter(follower=follower.id, followed=followed.id, are_we_friend=True).exists()) or \
            Friend.objects.filter(follower=followed.id, followed=follower.id, are_we_friend=True).exists():
            return Response({'error': 'Already friend'}, status=status.HTTP_409_CONFLICT)
        elif Friend.objects.filter(follower=follower.id, followed=followed.id, are_we_friend=False).exists() or \
            Friend.objects.filter(follower=followed.id, followed=follower.id, are_we_friend=False).exists():
            return Response({'error': 'Already sent a friend request'}, status=status.HTTP_409_CONFLICT)

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
                return Response({'error': 'Friend does not exist'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Invalid friend request'}, status=status.HTTP_400_BAD_REQUEST)

        # 나에게 온 친구 신청이 아닐 때
        if friend.followed != followed:
            return Response({'error': 'You do not have permission to accept friend applications'}, status=status.HTTP_403_FORBIDDEN)

        # 이미 친구인지 확인
        if friend.are_we_friend:
            return Response({'error': 'Already friends'}, status=status.HTTP_409_CONFLICT)

        # 수락 or 삭제
        if request.method == "PATCH":
            # 친구 신청을 수락하고 상태를 업데이트
            friend.are_we_friend = True
            friend.save()
            return Response({'message': 'Friend request accepted'}, status=status.HTTP_204_NO_CONTENT)
        elif request.method == "DELETE":
            # 친구 신청 삭제
            friend.delete()
            return Response({'message': 'Friend request rejected'}, status=status.HTTP_204_NO_CONTENT)

    @extend_schema(request=None)
    def send_req_list(self, request):
        user = request.user  # 현재 요청을 보낸 사용자

        # 현재 사용자를 follower로 갖는 Friend 객체들을 가져옴
        followers = Friend.objects.filter(follower=user, are_we_friend=False).order_by('-created_at')

        # 가져온 객체들을 시리얼라이즈
        serializer = self.get_serializer(followers, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=None)
    def receive_req_list(self, request):
        user = request.user  # 현재 요청을 보낸 사용자

        # 현재 사용자를 followed로 갖는 Friend 객체들을 가져옴
        followeds = Friend.objects.filter(followed=user, are_we_friend=False).order_by('-created_at')

        # 가져온 객체들을 시리얼라이즈
        serializer = self.get_serializer(followeds, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=None)
    def get_friend_request_count(self, request):
        user = request.user  # 현재 요청을 보낸 사용자

        # 현재 사용자를 followed로 갖는 Friend 객체들을 가져옴
        followeds = Friend.objects.filter(followed=user, are_we_friend=False)

        followeds_count = followeds.count()

        return Response({'request_cnt': followeds_count}, status=status.HTTP_200_OK)

    @extend_schema(request=None)
    def delete_friend(self, request, friend_id):
        me = request.user
        if friend_id is not None:
            try:
                friend = Friend.objects.get(id=friend_id)
            except Friend.DoesNotExist:
                return Response({'error': 'Friend does not exist'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Invalid friend request'}, status=status.HTTP_400_BAD_REQUEST)

        # 삭제할 수 있는 권한이 없을 때
        if friend.follower != me and friend.followed != me:
            return Response({'error': 'You do not have permission to delete friend'}, status=status.HTTP_403_FORBIDDEN)

        friend.delete()
        return Response({'message': 'Friend deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


class SearchFriendsView(viewsets.ModelViewSet):
    serializer_class = FriendSerializer

    @extend_schema(operation_id='search_friends')
    def get_friends(self, request, name):
        me = request.user

        friends = Friend.objects.filter(
            Q(follower=me, followed__nickname__icontains=name, are_we_friend=True) |
            Q(followed=me, follower__nickname__icontains=name, are_we_friend=True)
        ).annotate(
            friend_nickname=Case(
                When(follower__nickname__icontains=name, then='follower__nickname'),
                When(followed__nickname__icontains=name, then='followed__nickname'),
                output_field=CharField()
            )
        ).order_by('friend_nickname')

        serializer = self.get_serializer(friends, many=True)
    
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=None)
    def get_all_friends(self, request):
        me = request.user  # 현재 요청을 보낸 사용자

        friends = Friend.objects.filter(are_we_friend=True).annotate(
            other_person_nickname=Case(
                When(follower=me, then=F('followed__nickname')),
                When(followed=me, then=F('follower__nickname')),
                output_field=CharField()
            )
        ).order_by('other_person_nickname')

        # 가져온 객체들을 시리얼라이즈
        serializer = self.get_serializer(friends, many=True)
    
        return Response(serializer.data, status=status.HTTP_200_OK)


        

