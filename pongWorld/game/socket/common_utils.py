import json
from .game_consumers import GameConsumer
from player.models import Player
from game.models import Game, Tournament
from channels.db import database_sync_to_async
from ..serializers import GameRoomSerializer

async def start_game(consumer_instance):
    consumer_instance.pvp_game = GameConsumer(consumer_instance.game.player1, consumer_instance.game.player2, consumer_instance.game.speed)
    await send_game_state(consumer_instance)

async def send_game_state(consumer_instance):
    game_state = consumer_instance.pvp_game.get_game_state()
    data = {
        'type': consumer_instance.socket_message,
        'game_state': game_state
    }
    await consumer_instance.channel_layer.group_send(
        consumer_instance.game_group_name,
        {
            'type': 'game_info',
            'data': data
        },
    )

@database_sync_to_async
def get_player(player_id):
    return Player.objects.get(id=player_id)

@database_sync_to_async
def save_game_by_id(consumer_instance):
    return Game.objects.get(id=consumer_instance.game_id)

@database_sync_to_async
def get_pvp_serializer_data(consumer_instance):
    serializer = GameRoomSerializer(consumer_instance.game)
    return serializer.data
    
async def send_game_info(consumer_instance):
        consumer_instance.game_group_name = f'game_{consumer_instance.game.id}'
        serializer_data = await get_pvp_serializer_data(consumer_instance)
        await consumer_instance.channel_layer.group_add(consumer_instance.game_group_name, consumer_instance.channel_name)
        await consumer_instance.channel_layer.group_send(
            consumer_instance.game_group_name,
            {
                'type': 'game_info',
                'data': serializer_data
            }
        )