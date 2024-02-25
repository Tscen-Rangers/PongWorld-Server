from django.urls import path
from . import views

urlpatterns = [
    path('<int:player_id>/rooms/', views.ChatRoomList.as_view()),
    path('<int:chatroom_id>/messages/', views.MessageList.as_view()),
]