from django.urls import path
from . import views

urlpatterns = [
    path('rooms/', views.ChatRoomList.as_view()),
    path('<int:chatroom_id>/leave/', views.LeaveChatRoom.as_view()),
    path('<int:chatroom_id>/messages/', views.MessageList.as_view()),
]