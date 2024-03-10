from django.urls import path
from . import views

app_name = "friends"

urlpatterns = [
    path("follow/<int:followed_id>/", views.FriendReqResView.as_view({'post': 'request_friend'}), name="request_friend"),
    path("follow/accept/<int:friend_id>/", views.FriendReqResView.as_view({'patch': 'response_friend'}), name="aceept_friend"),
    path("follow/delete/<int:friend_id>/", views.FriendReqResView.as_view({'delete': 'response_friend'}), name="delete_friend"),
    path("following/", views.FriendReqResView.as_view({'get': 'send_req_list'}), name="send_req_list"),
    path("followed/", views.FriendReqResView.as_view({'get': 'receive_req_list'}), name="receive_req_list"),
    path("followed/count", views.FriendReqResView.as_view({'get': 'get_friend_request_count'}), name="get_friend_request_count"),
    path("", views.FriendReqResView.as_view({'get': 'friends_list'}), name="friends_list"),
    path("delete/<int:friend_id>/", views.FriendReqResView.as_view({'delete': 'delete_friend'}), name="delete_friend"),
]