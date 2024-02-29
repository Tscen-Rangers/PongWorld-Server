import json
from .game_consumers import GameConsumer
from player.models import Player
from game.models import Game, Tournament
from channels.db import database_sync_to_async

async def start_game(consumer_instance):
    consumer_instance.pvp_game = GameConsumer(consumer_instance.game.player1, consumer_instance.game.player2, consumer_instance.game_speed)
    await send_game_state(consumer_instance)

async def send_game_state(consumer_instance):
    game_state = consumer_instance.pvp_game.get_game_state()
    await consumer_instance.channel_layer.group_send(
        consumer_instance.game_group_name,
        {
            'type': 'game_info',
            'data': game_state
        },
    )

@database_sync_to_async
def get_player(player_id):
    return Player.objects.get(id=player_id)

@database_sync_to_async
def save_game_by_id(consumer_instance):
    return Game.objects.get(id=consumer_instance.game_id)
    