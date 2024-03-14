from django.urls import path
from . import views

app_name = "game"

urlpatterns = [
    path('', views.GameView.as_view({'get': 'get_game_home_view'}), name="get_game_home_view"),
]