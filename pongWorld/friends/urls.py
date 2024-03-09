from django.urls import path
from . import views

app_name = "friends"

urlpatterns = [
    path("request/<int:followed_id>/", views.FriendReqResView.as_view({'post': 'request_friend'}), name="request_friend"),
    path("response/<int:friend_id>/", views.FriendReqResView.as_view({'patch': 'response_friend', 'delete': 'response_friend'}), name="response_friend"),
    path("request/send/", views.FriendReqResView.as_view({'get': 'send_req_list'}), name="send_req_list"),
    path("request/receive/", views.FriendReqResView.as_view({'get': 'receive_req_list'}), name="receive_req_list"),
    path("request/receive/count", views.FriendReqResView.as_view({'get': 'get_friend_request_count'}), name="get_friend_request_count"),
    path("", views.FriendReqResView.as_view({'get': 'friends_list'}), name="friends_list"),
]