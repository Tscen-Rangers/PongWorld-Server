import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from game.models import Game, Tournament
from player.models import Player
from urllib.parse import parse_qs
from django.db.models import Min
from ..serializers import GameRoomSerializer, TournamentRoomSerializer, PlayerSerializer
from .common_utils import start_game, get_player, save_game_by_id
from .game_consumers import GameConsumer

class PvPMatchConsumer(AsyncWebsocketConsumer): # PvP Game

    async def connect(self):
        await self.accept()
        query_string = self.scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)
        player_id = query_params.get('player_id', [None])[0]
        self.player_id = int(player_id)
        if self.player_id is not None:
            self.player = await get_player(self.player_id)
    
    async def random_matching(self, data):
        self.game_speed = data['game_speed']

        await self.get_accessible_game()
        if self.accessible_game_id is None:     # 입장 가능한 퀵매치 방이 없을 때 퀵매치 방 생성
            await self.create_quick_match_room()
        else:          # 입장 가능한 퀵매치 방이 있을 때 입장
            self.game_id = self.accessible_game_id
            self.game = await save_game_by_id(self)
            await self.join_game()
        await self.send_game_info()
        await self.check_matching_complete()

    async def send_request(self, data):
        try:
            self.game_speed = data['game_speed']
            player2_id = data['player2_id']
            self.player2 = await self.check_player2(player2_id)
            await self.create_friend_match_room()
            self.player_group_name = f'player_{self.player2.id}'
            await self.channel_layer.group_send(
                self.player_group_name,
                {
                    'type': 'match_request_message',
                    'message': "You have a request for a game competition.",
                    'opponent': self.player.id,
                    'game_id': self.game.id,
                    'mode': self.game_speed,
                },
            )
            await self.send_game_info()

        except ValueError as e:
            error_message = json.dumps({"error": str(e)}, ensure_ascii=False)
            await self.send(text_data=error_message)
            await self.close()

    async def receive(self, text_data):
        data = json.loads(text_data)
        match_mode = data['match_mode']
        await self.match_modes[match_mode](self, data)

    match_modes = {
        'random': random_matching,
        'send_request': send_request
    }

    async def send_game_info(self):
        self.game_group_name = f'game_{self.game.id}'
        serializer_data = await self.get_serializer_data()
        await self.channel_layer.group_add(self.game_group_name, self.channel_name)
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'game_info',
                'data': serializer_data
            }
        )

    async def game_info(self, event):
        data = event['data']

        await self.send(text_data=json.dumps({
            'data': data
        }))

    @database_sync_to_async
    def get_accessible_game(self):
        self.accessible_game_id = Game.objects.filter(
            speed=self.game_speed,
            status=0,
            player2__isnull=True).aggregate(Min('id'))['id__min']

    @database_sync_to_async
    def create_quick_match_room(self):
        self.game = Game.objects.create(
            player1=self.player,
            mode=0,
            speed=self.game_speed,
            status=0)

    @database_sync_to_async
    def create_friend_match_room(self):
        self.game = Game.objects.create(
            player1=self.player,
            player2=self.player2,
            mode=1,
            speed=self.game_speed,
            status=0)

    @database_sync_to_async
    def get_serializer_data(self):
        serializer = GameRoomSerializer(self.game)
        return serializer.data

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
                    'message': "The match has been completed. The game will start soon!",
                }, 
            )
            self.pvp_game = await start_game(self)

    async def check_player2(self, player2_id):
        if player2_id == self.player_id:
            raise ValueError('You cannot send an invitation to yourself.')
        try:
            player2 = await get_player(player2_id)
        except Player.DoesNotExist:
            raise ValueError('The user does not exist.')
        return player2
    
    async def game_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message,
        },
        ))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.game_group_name, self.channel_name)

class TournamentMatchConsumer(AsyncWebsocketConsumer):     # tournament

    players_queue = []
    tournament_tmp_id = 1
    tournament_group_name = None
    current_round = 1

    async def connect(self):
        # if await is_unregistered_player():  # TODO 로그인 후 구현
        # else:
        await self.enter_tournament_room() 

    async def enter_tournament_room(self):
        try:
            await self.accept()

            query_string = self.scope['query_string'].decode('utf-8')
            query_params = parse_qs(query_string)
            player_id = query_params.get('player_id', [None])[0]
            self.player_id = int(player_id)
            if self.player_id is not None:
                try:
                    self.player = await get_player(self.player_id)
                except Player.DoesNotExist:
                    raise Exception('The user does not exist.')
            if self.player in self.players_queue:
                raise ValueError("Your matching is already in progress.")

            if not self.players_queue:
                TournamentMatchConsumer.tournament_group_name = f'tournament_{TournamentMatchConsumer.tournament_tmp_id}'
            self.players_queue.append(self.player)
            await self.channel_layer.group_add(TournamentMatchConsumer.tournament_group_name, self.channel_name)
            await self.send_queue_length()
            
            if len(self.players_queue) == 4:
                self.tournament = await self.create_tournament_room()
                serializer_data = await self.get_serializer_data()
                await self.channel_layer.group_send(
                    TournamentMatchConsumer.tournament_group_name,
                    {
                        'type': 'game_info',
                        'data': serializer_data
                    }
                )
                await self.send_matching_complete()
                self.players_queue.clear()
                TournamentMatchConsumer.tournament_tmp_id += 1

        except ValueError as e:
            error_message = json.dumps({"error": str(e)}, ensure_ascii=False)
            await self.send(text_data=error_message)
        except Exception as e:
            await self.send(text_data=json.dumps({"error": "[" + e.__class__.__name__ + "] " + str(e)}))
            await self.close()

    async def game_info(self, event):
        data = event['data']

        await self.send(text_data=json.dumps({
            'data': data,
        }))

    async def disconnect(self, close_code):
        if self.player in self.players_queue:
            self.players_queue.remove(self.player)
            await self.channel_layer.group_discard(TournamentMatchConsumer.tournament_group_name, self.channel_name)
            await self.send_queue_length()

    @database_sync_to_async
    def create_tournament_room(self):
        tournament = Tournament.objects.create(
            player1=self.players_queue[0],
            player2=self.players_queue[1],
            player3=self.players_queue[2],
            player4=self.players_queue[3],
            status=0
        )
        self.players_queue.clear()
        return tournament

    @database_sync_to_async
    def get_serializer_data(self):
        serializer = TournamentRoomSerializer(self.tournament)
        return serializer.data

    async def send_queue_length(self):
        await self.channel_layer.group_send(
            TournamentMatchConsumer.tournament_group_name,
            {
                'type': 'queue_length',
                'participants_num': len(self.players_queue)
            }
        )

    async def queue_length(self, event):
        await self.send(text_data=json.dumps({"participants_num": event["participants_num"]}))

    async def send_matching_complete(self):
        setattr(self.tournament, 'status', 1)
        await database_sync_to_async(self.tournament.save)()
        await self.channel_layer.group_send(
            self.tournament_group_name,
            {
                'type': 'game_message',
                'message': "The match has been completed. The game will start soon!",
            },
        )

    async def semi_final(self, data):
        tournament_id = data['tournament_id']
        self.tournament = await database_sync_to_async(Tournament.objects.get)(id=tournament_id)

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
        elif current_player_role == 'player3' or current_player_role == 'player4':
            self.tournament_semi_group_name = f'tournament_{self.tournament.id}_B'
        await self.send_opponent_info()

    async def send_opponent_info(self):
        if self.tournament_semi_group_name == f'tournament_{self.tournament.id}_A':
            player1 = self.tournament.player1
            player2 = self.tournament.player2
        else:
            player1 = self.tournament.player3
            player2 = self.tournament.player4
        try:    
            await self.channel_layer.group_add(self.tournament_semi_group_name, self.channel_name)
            await self.start_semi_final(player1, player2, 0)
        except Exception as e:
            print(f"Exception in send_opponent_info: {e}")

    async def start_semi_final(self, player1, player2, speed):
        self.round1 = GameConsumer(player1, player2, speed)
        game_state = self.round1.get_game_state()
        await self.channel_layer.group_send(
            self.tournament_semi_group_name,
            {
                'type': 'game_info',
                'data': game_state
            },
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        tournament_mode = data['tournament_mode']
        await self.tournament_modes[tournament_mode](self, data)

    tournament_modes = {
        'semi_final': semi_final
    }

    async def game_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message,
        },ensure_ascii=False 
        ))

class PlayerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        query_string = self.scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)
        player_id = query_params.get('player_id', [None])[0]
        self.player_id = int(player_id)
        self.player_group_name = f'player_{self.player_id}'
        await self.channel_layer.group_add(self.player_group_name, self.channel_name)

    async def match_request_message(self, event):
        message = event['message']
        opponent = event.get('opponent', None)
        game_id = event.get('game_id', None)
        mode = event.get('mode', None)

        response_data = {
            'message': message,
            'opponent': opponent,
            'game_id': game_id,
            'mode': mode
        }

        await self.send(text_data=json.dumps(response_data))

    async def game_competition(self, data):
        self.game_id = data['game_id']
        self.game_group_name = f'game_{self.game_id}'
        accepted = data['accepted']
        self.game = await save_game_by_id(self)

        if accepted:
            await self.channel_layer.group_add(self.game_group_name, self.channel_name)
            setattr(self.game, 'status', 1)
            await database_sync_to_async(self.game.save)()
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_message',
                    'message': "The match has been completed. The game will start soon!",
                }, 
            )
            await database_sync_to_async(lambda: start_game(self))()

        else:
            await database_sync_to_async(self.game.delete)()
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_message',
                    'message': "The match has been rejected.",
                }, 
            )
            await self.close()

    async def receive(self, text_data):
        data = json.loads(text_data)
        reply_type = data['reply_type']
        await self.reply_types[reply_type](self, data)

    reply_types = {
        'game_competition': game_competition
    }

    async def game_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({ 'message': message, }))
