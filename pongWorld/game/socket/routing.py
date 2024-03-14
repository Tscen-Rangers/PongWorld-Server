from django.urls import re_path
from . import match_consumers

game_websocket_urlpatterns = [
    re_path(r"ws/random/", match_consumers.RandomMatchConsumer.as_asgi()),
    re_path(r"ws/tournament/", match_consumers.TournamentMatchConsumer.as_asgi()),
]