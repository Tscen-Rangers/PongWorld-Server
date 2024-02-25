from django.urls import re_path
from . import consumers

game_websocket_urlpatterns = [
    re_path(r"ws/game/", consumers.GameConsumer.as_asgi()),
    re_path(r"ws/tournament/", consumers.TournamentConsumer.as_asgi()),
]