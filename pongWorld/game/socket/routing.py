from django.urls import re_path
from . import match_consumers

game_websocket_urlpatterns = [
    re_path(r"ws/game/", match_consumers.PvPMatchConsumer.as_asgi()),
    re_path(r"ws/tournament/", match_consumers.TournamentMatchConsumer.as_asgi()),
]