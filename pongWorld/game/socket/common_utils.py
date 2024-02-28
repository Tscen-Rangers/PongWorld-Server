import json
from .game_consumers import PvPGameConsumer

async def start_game(consumer_instance):
    consumer_instance.pvp_game = PvPGameConsumer(consumer_instance.game.player1, consumer_instance.game.player2, consumer_instance.game_speed)
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