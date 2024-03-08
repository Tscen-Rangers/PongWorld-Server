from django.urls import path
from . import views

app_name = "player"

urlpatterns = [
    path('online/', views.OnlinePlayerListView.as_view())
    path('', views.PlayerRetrieveUpdateDestroyView.as_view(), name="player_detail"),
    path("friends/request/<int:followed_id>/", views.FriendReqResView.as_view({'post': 'request_friend'}), name="request_friend"),
    path("friends/response/<int:friend_id>/", views.FriendReqResView.as_view({'patch': 'response_friend', 'delete': 'response_friend'}), name="response_friend"),
    path("friends/", views.FriendReqResView.as_view({'get': 'list'}), name="player_friends"),
]