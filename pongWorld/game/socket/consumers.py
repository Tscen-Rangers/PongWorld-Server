import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from game.models import Game, Tournament
from player.models import Player
from urllib.parse import parse_qs
from django.db.models import Count, Min, Q
from ..serializers import GameRoomSerializer, TournamentRoomSerializer
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)

class GameConsumer(AsyncWebsocketConsumer): # PvP Game
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_group_name = None
        self.accessible_game_id = None


    async def connect(self):
        # if await is_unregistered_player():  # TODO 로그인 후 구현
        # else:
        await self.enter_game_room() 

    async def enter_game_room(self):
        try:
            await self.accept()

            game_id = self.scope["url_route"]["kwargs"]["game_id"]
            self.game_id = int(game_id)
            
            query_string = self.scope['query_string'].decode('utf-8')
            query_params = parse_qs(query_string)
            player_id = query_params.get('player_id', [None])[0]
            self.player_id = int(player_id)
            if self.player_id is not None:
                self.player = await self.get_player()

            if self.game_id == 0:       # 빠른 시작 (랜덤 매칭)
                await self.get_accessible_game()
                if self.accessible_game_id is None:     # 입장 가능한 퀵매치 방이 없을 때 퀵매치 방 생성
                    await self.create_quick_match_room()
                    self.game_id = self.game.id
                else:          # 입장 가능한 퀵매치 방이 있을 때 입장
                    self.game_id = self.accessible_game_id
                    await self.save_game_by_id()
                    await self.join_game()
            else:     # 게임 초대 수락
                await self.save_game_by_id()
                await self.join_game()
            self.game_group_name = f'game_{self.game_id}'
            
            serializer_data = await self.get_serializer_data()
            await self.channel_layer.group_add(self.game_group_name, self.channel_name)
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_info',
                    'data': serializer_data
                }
            )
            await self.check_matching_complete()
        except ObjectDoesNotExist:
            logger.error(f"ObjectDoesNotExist")
        except Exception as e:
            await self.send(text_data=json.dumps({"error": "[" + e.__class__.__name__ + "] " + str(e)}))
            await self.close()


    async def game_info(self, event):
        data = event['data']

        await self.send(text_data=json.dumps({
            'data': data
        }))

    @database_sync_to_async
    def get_player(self):
        return Player.objects.get(id=self.player_id)

    @database_sync_to_async
    def get_accessible_game(self):
        self.accessible_game_id = Game.objects.filter(mode=0, player2__isnull=True).aggregate(Min('id'))['id__min']

    @database_sync_to_async
    def create_quick_match_room(self):
        self.game = Game.objects.create(player1=self.player)

    @database_sync_to_async
    def save_game_by_id(self):
        self.game = Game.objects.get(id=self.game_id)

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
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_message',
                    'message': "매칭이 완료되었습니다. 곧 게임이 시작됩니다!",
                }, 
            )
    
    async def game_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message,
        },ensure_ascii=False 
        ))

class TournamentConsumer(GameConsumer):     # tournament
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tournament_group_name = None

    async def enter_game_room(self):
        try:
            await self.accept()

            query_string = self.scope['query_string'].decode('utf-8')
            query_params = parse_qs(query_string)
            player_id = query_params.get('player_id', [None])[0]
            self.player_id = int(player_id)
            if self.player_id is not None:
                self.player = await self.get_player()

            tournament_id = await self.get_accessible_tournament()
            if tournament_id is None:     # 입장 가능한 토너먼트 방이 없을 때 토너먼트 방 생성
                await self.create_tournament_room()
                self.tournament_id = self.tournament.id
            else:          # 입장 가능한 토너먼트 방이 있을 때 입장
                self.tournament_id = tournament_id
                await self.save_tournament_by_id()
                await self.join_tournament()
            self.tournament_group_name = f'tournament_{self.tournament_id}'
            
            serializer_data = await self.get_serializer_data()
            await self.channel_layer.group_add(self.tournament_group_name, self.channel_name)
            await self.channel_layer.group_send(
                self.tournament_group_name,
                {
                    'type': 'game_info',
                    'data': serializer_data
                }
            )
            await self.check_matching_complete()
        except ObjectDoesNotExist:
            logger.error(f"ObjectDoesNotExist")
        except Exception as e:
            await self.send(text_data=json.dumps({"error": "[" + e.__class__.__name__ + "] " + str(e)}))
            await self.close()

    @database_sync_to_async
    def get_accessible_tournament(self):
        tournament_id = Tournament.objects.filter(
            Q(player1__isnull=True) | Q(player2__isnull=True) | Q(player3__isnull=True) | Q(player4__isnull=True)
        ).aggregate(Min('id'))['id__min']
        return tournament_id

    @database_sync_to_async
    def create_tournament_room(self):
        self.tournament = Tournament.objects.create(player1=self.player)

    @database_sync_to_async
    def save_tournament_by_id(self):
        self.tournament = Tournament.objects.get(id=self.tournament_id)

    @database_sync_to_async
    def get_serializer_data(self):
        serializer = TournamentRoomSerializer(self.tournament)
        return serializer.data

    async def join_tournament(self):
        try:
            player1 = await sync_to_async(self.tournament.__getattribute__)('player1_id')
            player2 = await sync_to_async(self.tournament.__getattribute__)('player2_id')
            player3 = await sync_to_async(self.tournament.__getattribute__)('player3_id')
            player4 = await sync_to_async(self.tournament.__getattribute__)('player4_id')

            players = [player1, player2, player3, player4]

            if self.player.id in players:
                raise Exception("You are already a participant in this tournament.")

            for i, player_id in enumerate(players):
                if player_id is None:
                    setattr(self.tournament, f"player{i+1}", self.player)
                    await database_sync_to_async(self.tournament.save)()
                    break

        except Exception as e:
            await self.send(text_data=json.dumps({"error": str(e)}))
            await self.close()

    async def check_matching_complete(self):
        if self.tournament.player1 is not None and self.tournament.player2 is not None \
            and self.tournament.player3 is not None and self.tournament.player4 is not None:
            await self.channel_layer.group_send(
                self.tournament_group_name,
                {
                    'type': 'game_message',
                    'message': "매칭이 완료되었습니다. 곧 토너먼트가 시작됩니다!",
                }, 
            )
