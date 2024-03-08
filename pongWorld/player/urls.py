from django.urls import path
from . import views

app_name = "player"

urlpatterns = [
    path('online/', views.OnlinePlayerListView.as_view()),
    path('', views.PlayerRetrieveUpdateDestroyView.as_view(), name="player_detail"),
    path('profile/<int:user_id>/', views.PlayerProfileView.as_view({'get': 'get_player_profile'}), name="player_profile"),
]