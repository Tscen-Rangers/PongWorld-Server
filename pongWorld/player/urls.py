from django.urls import path
from . import views

app_name = "player"

urlpatterns = [
    path('online/', views.OnlinePlayerListView.as_view()),
    path('setting/', views.PlayerSettingView.as_view({'get': 'get_user_info'}), name="get_user_info"),
    path('setting/<int:pk>/', views.PlayerSettingView.as_view({'patch': 'partial_update'}), name="set_user_info"),
    path('withdraw/', views.PlayerSettingView.as_view({'delete': 'withdraw'}), name="user_withdraw"),
    path('search/', views.SearchUsers.as_view({'get': 'get_all_users'}), name="get_all_users"),
    path('search/<str:name>/', views.SearchUsers.as_view({'get': 'get_users'}), name="get_users"),
    path('profile/', views.PlayerProfileView.as_view({'get': 'get_my_profile'}), name="my_profile"),
    path('profile/<int:user_id>/<int:game_record_type>/', views.PlayerProfileView.as_view({'get': 'get_player_profile'}), name="player_profile"),
]