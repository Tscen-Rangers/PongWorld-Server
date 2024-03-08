from django.urls import path
from . import views

app_name = "friends"

urlpatterns = [
    path("friends/request/<int:followed_id>/", views.FriendReqResView.as_view({'post': 'request_friend'}), name="request_friend"),
    path("friends/response/<int:friend_id>/", views.FriendReqResView.as_view({'patch': 'response_friend', 'delete': 'response_friend'}), name="response_friend"),
    path("friends/request/send/", views.FriendReqResView.as_view({'get': 'send_req_list'}), name="send_req_list"),
    path("friends/request/receive/", views.FriendReqResView.as_view({'get': 'receive_req_list'}), name="receive_req_list"),
    path("friends/", views.FriendReqResView.as_view({'get': 'friends_list'}), name="friends_list"),
]