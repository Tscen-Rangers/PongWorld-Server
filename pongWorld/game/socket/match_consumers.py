import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from urllib.parse import parse_qs
from django.db.models import Min
import asyncio

from ..serializers import GameRoomSerializer, TournamentRoomSerializer, PlayerSerializer
from .common_utils import start_game, get_player, save_game_by_id, get_pvp_serializer_data, send_game_info
from game.models import Game, Tournament
from player.models import Player
from .game_consumers import GameConsumer, TournamentGame
from config.utils import CommonUtils

class RandomMatchConsumer(AsyncWebsocketConsumer): # Random PvP Game
    rooms = {}

    async def connect(self):
        self.user = self.scope['user']

        if self.user.is_authenticated:
            self.player = self.user
            await self.accept()
        else:
            await self.close()
    
    async def random_matching(self, data):
        self.speed = data['speed']

        await self.get_accessible_game()
        if self.accessible_game_id is None:     # 입장 가능한 퀵매치 방이 없을 때 퀵매치 방 생성
            await self.create_quick_match_room()
        else:          # 입장 가능한 퀵매치 방이 있을 때 입장
            self.game_id = self.accessible_game_id
            self.game = await save_game_by_id(self)
            await self.join_game()
        self.game_group_name = f'game_{self.game.id}'
        await self.channel_layer.group_add(self.game_group_name, self.channel_name)
        # await send_game_info(self)
        await self.check_matching_complete()

    async def move_paddle(self, data):
        if self.game.id in RandomMatchConsumer.rooms:
            asyncio.create_task(RandomMatchConsumer.rooms[self.game.id].change_paddle_position(self.player.id, data['y_coordinate']))  # 백그라운드에서 실행

    async def end_game(self, data):
        await self.channel_layer.group_discard(self.game_group_name, self.channel_name)
        if self.game.id in RandomMatchConsumer.rooms:
            del RandomMatchConsumer.rooms[self.game.id]
        await self.close()

    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data['command']
        await self.commands[command](self, data)

    commands = {
        'participant': random_matching,
        'move_paddle': move_paddle,
        'end_game': end_game,
    }

    async def game_info(self, event):
        data = event['data']
        message_type = event['message_type']

        await self.send(text_data=json.dumps({
            'type': message_type,
            'data': data,
        }))

    @database_sync_to_async
    def get_accessible_game(self):
        self.accessible_game_id = Game.objects.filter(
            speed=self.speed,
            status=0,
            player2__isnull=True).aggregate(Min('id'))['id__min']

    @database_sync_to_async
    def create_quick_match_room(self):
        self.game = Game.objects.create(
            player1=self.player,
            mode=0,
            speed=self.speed)

    async def join_game(self):
        try:
            player1 = await sync_to_async(self.game.__getattribute__)('player1_id')
            player2 = await sync_to_async(self.game.__getattribute__)('player2_id')

            if player1 is None:
                self.game.player1 = self.player
                await database_sync_to_async(self.game.save)()
            elif player2 is None:
                if player1 == self.player.id:
                    raise Exception("Your matching is already in progress.")
                self.game.player2 = self.player
                await database_sync_to_async(self.game.save)()
        except Exception as e:
            await self.send(text_data=json.dumps({"error": str(e)}))
            await self.close()

    async def check_matching_complete(self):
        if self.game.player1 is not None and self.game.player2 is not None:
            setattr(self.game, 'status', 1)
            await database_sync_to_async(self.game.save)()
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_message',
                    'message_type': 'SUCCESS_RANDOM_MATCHING',
                    'message': "The match has been completed. The game will start soon!",
                }, 
            )
            self.socket_message = 'START_RANDOM_GAME'
            if self.game.id not in RandomMatchConsumer.rooms:
                RandomMatchConsumer.rooms[self.game.id] = GameConsumer(self)
            await start_game(self)
    
    async def game_message(self, event):
        message_type = event['message_type']
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': message_type,
            'message': message,
        },
        ))

    async def disconnect(self, close_code):
        await database_sync_to_async(self.game.refresh_from_db)()
        if self.player == self.game.player1 and self.game.status == 0:
            await database_sync_to_async(self.game.delete)()

class TournamentMatchConsumer(AsyncWebsocketConsumer):     # tournament
    rooms = {}

    players_queue = []
    tournament_tmp_id = 1
    tournament_tmp_group_name = None

    async def connect(self):
        self.user = self.scope['user']

        if self.user.is_authenticated:
            self.player = self.user
            await self.enter_tournament_room() 
        else:
            await self.close()

    async def enter_tournament_room(self):
        try:
            await self.accept()
            self.user = self.scope['user']

            if self.user.is_authenticated:
                self.player = self.user

            if self.player in self.players_queue:
                raise ValueError("Your matching is already in progress.")

            if not self.players_queue:
                TournamentMatchConsumer.itournament_tmp_group_name = f'tournament_tmp_{TournamentMatchConsumer.tournament_tmp_id}'
            self.players_queue.append(self.player)
            await self.channel_layer.group_add(TournamentMatchConsumer.itournament_tmp_group_name, self.channel_name)
            await self.send_queue_length()
            
            if len(self.players_queue) == 4:
                self.tournament = await self.create_tournament_room()
                serializer_data = await self.get_serializer_data()
                await self.channel_layer.group_send(
                    TournamentMatchConsumer.itournament_tmp_group_name,
                    {
                        'type': 'game_info',
                        'message_type': 'TOURNAMENT_PARTICIPANTS',
                        'data': serializer_data
                    }
                )
                await self.send_matching_complete()
                TournamentMatchConsumer.tournament_tmp_id += 1

        except ValueError as e:
            error_message = json.dumps({"error": str(e)}, ensure_ascii=False)
            await self.send(text_data=error_message)
        except Exception as e:
            await self.send(text_data=json.dumps({"error": "[" + e.__class__.__name__ + "] " + str(e)}))
            await self.close()

    async def game_info(self, event):
        data = event['data']
        message_type = event['message_type']

        await self.send(text_data=json.dumps({
            'type': message_type,
            'data': data,
        }))

    async def disconnect(self, close_code):
        if self.player in self.players_queue:
            self.players_queue.remove(self.player)
            await self.channel_layer.group_discard(TournamentMatchConsumer.itournament_tmp_group_name, self.channel_name)
            await self.send_queue_length()

    async def end_tournament(self, data):
        if hasattr(self, 'tournament_final_group_name'):
            await self.channel_layer.group_discard(self.tournament_final_group_name, self.channel_name)
            if self.tournament_semi_group_name in TournamentMatchConsumer.rooms:
                del TournamentMatchConsumer.rooms[self.tournament_semi_group_name]
        if hasattr(self, 'tournament_final_group_name') and self.tournament_final_group_name in TournamentMatchConsumer.rooms:
            del TournamentMatchConsumer.rooms[self.tournament_final_group_name]
        if hasattr(self, 'tournament_semi_group_name'):
            await self.channel_layer.group_discard(self.tournament_semi_group_name, self.channel_name)
        await self.close()

    @database_sync_to_async
    def create_tournament_room(self):
        tournament = Tournament.objects.create(
            player1=self.players_queue[0],
            player2=self.players_queue[1],
            player3=self.players_queue[2],
            player4=self.players_queue[3]
        )
        self.players_queue.clear()
        return tournament

    @database_sync_to_async
    def get_serializer_data(self):
        serializer = TournamentRoomSerializer(self.tournament)
        return serializer.data

    async def send_queue_length(self):
        await self.channel_layer.group_send(
            TournamentMatchConsumer.itournament_tmp_group_name,
            {
                'type': 'queue_length',
                'participants_num': len(self.players_queue)
            }
        )

    async def queue_length(self, event):
        await self.send(text_data=json.dumps({"participants_num": event["participants_num"]}))

    async def send_matching_complete(self):
        await self.channel_layer.group_send(
            TournamentMatchConsumer.itournament_tmp_group_name,
            {
                'type': 'game_message',
                'message_type': 'SUCCESS_SEMI_FINAL_MATCHING',
                'message': "The match has been completed. The game will start soon!",
            },
        )

    async def semi_final(self, data):
        tournament_id = data['tournament_id']
        self.tournament = await database_sync_to_async(Tournament.objects.get)(id=tournament_id)
        self.tournament_group_name = f'tournament_{self.tournament.id}'
        await self.channel_layer.group_add(self.tournament_group_name, self.channel_name)

        players = {
            'player1': await database_sync_to_async(lambda: self.tournament.player1)(),
            'player2': await database_sync_to_async(lambda: self.tournament.player2)(),
            'player3': await database_sync_to_async(lambda: self.tournament.player3)(),
            'player4': await database_sync_to_async(lambda: self.tournament.player4)(),
        }
        current_player_role = None

        for role, player in players.items():
            if player.id == self.player.id:
                current_player_role = role
                break

        if current_player_role == 'player1' or current_player_role == 'player2':
            self.tournament_semi_group_name = f'tournament_{self.tournament.id}_A'
            player1 = self.tournament.player1
            player2 = self.tournament.player2
        elif current_player_role == 'player3' or current_player_role == 'player4':
            self.tournament_semi_group_name = f'tournament_{self.tournament.id}_B'
            player1 = self.tournament.player3
            player2 = self.tournament.player4
        await self.channel_layer.group_add(self.tournament_semi_group_name, self.channel_name)
        self.speed = 1
        await asyncio.sleep(1)
        await self.start_semi_final(self.tournament_semi_group_name, player1, player2)

    async def start_semi_final(self, tournament_group, player1, player2):
        if tournament_group not in TournamentMatchConsumer.rooms:
            TournamentMatchConsumer.rooms[tournament_group] = TournamentGame(self, player1, player2)
        else:
            return
        
        TournamentMatchConsumer.rooms[tournament_group].winner = asyncio.create_task(TournamentMatchConsumer.rooms[tournament_group].start_tournament_semi_final_loop(self))
        
    async def final(self, data):
        try:
            if self.player == TournamentMatchConsumer.rooms[self.tournament_semi_group_name].winner:
                self.tournament_final_group_name = f'tournament_{self.tournament.id}_final'
                await self.channel_layer.group_add(self.tournament_final_group_name, self.channel_name)

                player1 = TournamentMatchConsumer.rooms[f'tournament_{self.tournament.id}_A'].winner
                player2 = TournamentMatchConsumer.rooms[f'tournament_{self.tournament.id}_B'].winner

                await asyncio.sleep(1)
                # 준결승 A, B팀 모두 끝난 후 결승 시작
                if self.tournament_final_group_name not in TournamentMatchConsumer.rooms and player1 and player2:
                    self.speed = 2
                    TournamentMatchConsumer.rooms[self.tournament_final_group_name] = TournamentGame(self, player1, player2)
                    asyncio.create_task(TournamentMatchConsumer.rooms[self.tournament_final_group_name].start_tournament_final_loop(self))
            else:
                raise Exception('You cannot start final round. You are not winner.')
        except Exception as e:
            await self.send(text_data=json.dumps({"error": "[" + e.__class__.__name__ + "] " + str(e)}))

    async def move_paddle(self, data):
        if hasattr(self, 'tournament_final_group_name') and self.tournament_final_group_name in TournamentMatchConsumer.rooms:
            asyncio.create_task(TournamentMatchConsumer.rooms[self.tournament_final_group_name].change_paddle_position(self.player.id, data['y_coordinate']))
        elif self.tournament_semi_group_name in TournamentMatchConsumer.rooms:
            asyncio.create_task(TournamentMatchConsumer.rooms[self.tournament_semi_group_name].change_paddle_position(self.player.id, data['y_coordinate']))

    async def receive(self, text_data):
        data = json.loads(text_data)
        tournament_mode = data['tournament_mode']
        await self.tournament_modes[tournament_mode](self, data)

    tournament_modes = {
        'semi_final': semi_final,
        'final': final,
        'move_paddle': move_paddle,
        'end_tournament': end_tournament
    }

    async def game_message(self, event):
        message_type = event['message_type']
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': message_type,
            'message': message,
        },
        ))

class GameMixin:
    rooms = {}

    async def match_request_message(self, event):
        message = event['message']
        message_type = event['message_type']
        opponent_profile_img = CommonUtils.get_full_url(event.get('opponent_profile_img', None))
        opponent_nickname = event.get('opponent_nickname', None)
        game_id = event.get('game_id', None)
        mode = event.get('mode', None)

        response_data = {
            'type': message_type,
            'message': message,
            'opponent_profile_img': opponent_profile_img,
            'opponent_nickname': opponent_nickname,
            'game_id': game_id,
            'mode': mode
        }

        await self.send(text_data=json.dumps(response_data))

    async def response_competition(self, text_data_json):
        try:
            self.game_id = text_data_json['game_id']
            self.game_group_name = f'game_{self.game_id}'
            accepted = text_data_json['accepted']
            self.game = await save_game_by_id(self)
            self.speed = self.game.speed
            await self.channel_layer.group_add(self.game_group_name, self.channel_name)

            if accepted:
                setattr(self.game, 'status', 1)
                await database_sync_to_async(self.game.save)()
                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        'type': 'game_message',
                        'message_type': 'SUCCESS_FRIEND_GAME',
                        'message': "The match has been completed. The game will start soon!",
                    }, 
                )
                self.socket_message = 'START_FRIEND_GAME'
                if self.game.id not in GameMixin.rooms:
                    GameMixin.rooms[self.game.id] = GameConsumer(self)
                await start_game(self)

            else:
                await database_sync_to_async(self.game.delete)()
                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        'type': 'game_message',
                        'message_type': 'REJECTED_FRIEND_GAME',
                        'message': "The match has been rejected.",
                    }, 
                )
                await self.channel_layer.group_discard(self.game_group_name, self.channel_name)
        except Game.DoesNotExist:
            error_message = json.dumps({"type": "INVALID_GAME", "message": "Invalid Game ID"}, ensure_ascii=False)
            await self.send(text_data=error_message)

    async def request_competition(self, text_data_json):
        try:
            self.speed = text_data_json['speed']
            player2_id = text_data_json['player2_id']
            self.player2 = await self.check_player2(player2_id)
            await self.create_friend_match_room()
            self.player_group_name = f'player_{self.player2.id}'
            await self.channel_layer.group_send(
                self.player_group_name,
                {
                    'type': 'match_request_message',
                    'message_type': 'REQUEST_MATCHING',
                    'message': "You have a request for a game competition.",
                    'opponent_profile_img': self.player.profile_img.url,
                    'opponent_nickname': self.player.nickname,
                    'game_id': self.game.id,
                    'mode': self.speed,
                },
            )
            self.game_group_name = f'game_{self.game.id}'
            await self.channel_layer.group_add(self.game_group_name, self.channel_name)
            self.socket_message = 'INVITE_GAME'
            await send_game_info(self)

        except ValueError as e:
            error_message = json.dumps({"error": str(e)}, ensure_ascii=False)
            await self.send(text_data=error_message)

    async def quit_competition(self, text_data_json):
        try:
            if self.player == self.game.player1 and self.game.status == 0:
                await database_sync_to_async(self.game.delete)()
                await self.channel_layer.group_discard(self.game_group_name, self.channel_name)
                await self.send(text_data=json.dumps({"type": "QUIT_FRIEND_GAME", "message": "Quit Game Successfully."}))
            else:   # 게임 중에 나갈 때
                await self.channel_layer.group_discard(self.game_group_name, self.channel_name)
        except Exception as e:
            await self.send(text_data=json.dumps({"error": "[" + e.__class__.__name__ + "] " + str(e)}))

    async def check_player2(self, player2_id):
        if player2_id == self.player.id:
            raise ValueError('You cannot send an invitation to yourself.')
        try:
            player2 = await get_player(player2_id)
        except Player.DoesNotExist:
            raise ValueError('The user does not exist.')
        return player2

    async def game_info(self, event):
        data = event['data']
        message_type = event['message_type']

        await self.send(text_data=json.dumps({
            'type': message_type,
            'data': data,
        }))

    async def move_paddle(self, data):
        if self.game.id in GameMixin.rooms:
            asyncio.create_task(GameMixin.rooms[self.game.id].change_paddle_position(self.player.id, data['y_coordinate']))  # 백그라운드에서 실행
    
    async def end_game(self, data):
        await self.channel_layer.group_discard(self.game_group_name, self.channel_name)
        if self.game.id in GameMixin.rooms:
            del GameMixin.rooms[self.game.id]

    async def handle_pvp_game(self, text_data_json):
        self.player = self.user
        command = text_data_json['command']
        await self.commands[command](self, text_data_json)

    commands = {
        'request': request_competition,
        'response': response_competition,
        'quit': quit_competition,
        'move_paddle': move_paddle,
        'end_game': end_game,
    }

    async def game_message(self, event):
        message_type = event['message_type']
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': message_type,
            'message': message,
        },
        ))

    @database_sync_to_async
    def create_friend_match_room(self):
        self.game = Game.objects.create(
            player1=self.player,
            player2=self.player2,
            mode=1,
            speed=self.speed)
