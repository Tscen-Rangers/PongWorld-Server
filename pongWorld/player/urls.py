from django.urls import path
from . import views

app_name = "player"

urlpatterns = [
    path('online/', views.OnlinePlayerListView.as_view()),
    path('', views.PlayerRetrieveUpdateDestroyView.as_view(), name="player_detail"),
    path('all/', views.SearchUsers.as_view({'get': 'get_all_users'}), name="get_all_users"),
    path('all/<str:name>/', views.SearchUsers.as_view({'get': 'get_users'}), name="get_users"),
    path('profile/', views.PlayerProfileView.as_view({'get': 'get_my_profile'}), name="my_profile"),
    path('profile/<int:user_id>/<int:game_record_type>/', views.PlayerProfileView.as_view({'get': 'get_player_profile'}), name="player_profile"),
]