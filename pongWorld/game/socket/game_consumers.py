from .game_config import *
from ..serializers import PlayerSerializer
from player.models import Player
from channels.db import database_sync_to_async
import asyncio
import random
import math

# 세로 : 490
# 가로 : 660
# 공 지름 : 15
# 패들 가로 : 11
# 패들 세로 : 60

class GameConsumer:
    def __init__(self, consumer_instance):
        self.channel_layer = consumer_instance.channel_layer
        self.ball_position = [0, 0]
        self.player1_paddle_position = [-WALL_WIDTH_HALF, 0]
        self.player2_paddle_position = [WALL_WIDTH_HALF, 0]
        self.top_wall_y = WALL_HEIGHT_HALF
        self.bottom_wall_y = -WALL_HEIGHT_HALF
        self.speed = consumer_instance.speed
        self.player1_score = 0
        self.player2_score = 0
        self.ball_dx = self.speed
        self.ball_dy = self.speed
        self.add_ball_speed = self.speed / 5
        self.init_ball_position = True
        self.slow_ball_speed = True     # 처음에 공 느리게(패들에 닿기 전)

    def init_game(self, consumer_instance):
        self.game = consumer_instance.game
        self.game_group_name = consumer_instance.game_group_name
        self.player1 = self.game.player1
        self.player2 = self.game.player2
    
    async def calculate_ball_state(self):

        if self.init_ball_position == True:
            self.init_ball_position = False
            await asyncio.sleep(2)

        # 공의 위치 업데이트
        self.ball_position[0] += self.ball_dx
        self.ball_position[1] += self.ball_dy

        # 상단 및 하단 벽과의 충돌 처리
        if self.ball_position[1] - BALL_RADIUS < -WALL_HEIGHT_HALF or self.ball_position[1] + BALL_RADIUS > WALL_HEIGHT_HALF:
            self.ball_dy *= -1  # y축 방향 반전
            self.add_ball_speed *= -1

        # 패들과의 충돌 처리(x축 기준으로 동일한 위치이면서 y축기준으로 높이의 범위안에 들어오면 충돌로 간주)
        
        ## 왼쪽 패들 충돌
        if self.ball_position[0] - BALL_RADIUS < -WALL_WIDTH_HALF + PADDLE_WIDTH_HALF and \
        -PADDLE_HEIGHT_HALF < self.ball_position[1] - self.player1_paddle_position[1] < PADDLE_HEIGHT_HALF:
            self.ball_dx = abs(self.ball_dx)  # x축 방향 반전
            
            if self.slow_ball_speed == True:    # 처음에 느렸던 공 속도 원래대로
                self.ball_dx *= 2
                self.ball_dy *= 2
                self.slow_ball_speed = False
            else: # 속도 증가
                self.ball_dx += abs(self.add_ball_speed)
                self.ball_dy += self.add_ball_speed

            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_message',
                    'message_type': 'HIT_THE_BALL',
                    'message': "Player1 hit the ball"
                }
            )


        ## 오른쪽 패들 충돌
        if self.ball_position[0] + BALL_RADIUS > WALL_WIDTH_HALF - PADDLE_WIDTH_HALF and \
        -PADDLE_HEIGHT_HALF < self.ball_position[1] - self.player2_paddle_position[1] < PADDLE_HEIGHT_HALF:
            self.ball_dx = -abs(self.ball_dx)  # x축 방향 반전

            if self.slow_ball_speed == True:    # 처음에 느렸던 공 속도 원래대로
                self.ball_dx *= 2
                self.ball_dy *= 2
                self.slow_ball_speed = False
            else: # 속도 증가
                self.ball_dx -= abs(self.add_ball_speed)
                self.ball_dy += self.add_ball_speed

            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_message',
                    'message_type': 'HIT_THE_BALL',
                    'message': "Player2 hit the ball"
                }
            )

        # 좌우 벽과의 충돌 처리
        if self.ball_position[0] - BALL_RADIUS < -WALL_WIDTH_HALF or \
        self.ball_position[0] + BALL_RADIUS > WALL_WIDTH_HALF:
            # 점수 업데이트 및 공 위치 초기화 로직
            ## 왼쪽 벽 충돌
            if self.ball_position[0] - BALL_RADIUS < -WALL_WIDTH_HALF:
                self.player2_score += 1  # player2 점수 증가
                message_type = "PLAYER2_GET_SCORE"
                player_id = self.player2.id
            ## 오른쪽 벽 충돌
            elif self.ball_position[0] + BALL_RADIUS > WALL_WIDTH_HALF:
                self.player1_score += 1  # player1 점수 증가
                message_type = "PLAYER1_GET_SCORE"
                player_id = self.player1.id
            ### 공 위치 초기화
            self.ball_position = [0, random.randint(-100, 100)]
            self.init_ball_position = True
            if (self.player1_score + self.player2_score) % 2 == 0:
                self.ball_dx = self.speed
            else:
                self.ball_dx = -self.speed
            self.ball_dy = self.speed  * random.choice([-1, 1])
            self.slow_ball_speed = True 
        
            # 게임 스코어 전송
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_info',
                    'message_type': message_type,
                    'data': self.get_score(player_id)
                }
            )
            
            ## 스코어 충족으로 인한 게임종료
            if self.player1_score == SCORE_LIMIT or self.player2_score == SCORE_LIMIT:
                setattr(self.game, 'player1_score', self.player1_score)
                setattr(self.game, 'player2_score', self.player2_score)
                setattr(self.game, 'status', 2)
                # player1이 승리했을 때
                if self.player1_score == SCORE_LIMIT:
                    setattr(self.game, 'winner', self.player1)
                    setattr(self.player1, 'wins', self.player1.wins + 1)
                    player1_new_rating, player2_new_rating = self.calculate_new_ratings(self.player1.total_score, self.player2.total_score)
                # player2가 승리했을 때
                elif self.player2_score == SCORE_LIMIT:
                    setattr(self.game, 'winner', self.player2)
                    setattr(self.player2, 'wins', self.player2.wins + 1)
                    player2_new_rating, player1_new_rating = self.calculate_new_ratings(self.player2.total_score, self.player1.total_score)
                winner = self.game.winner
                await database_sync_to_async(self.game.save)()
                
                # 점수 저장 전 현재 랭킹 가져오기
                player1_ranking = self.get_ranking(self.player1, self.player1.total_score)
                player2_ranking = self.get_ranking(self.player2, self.player2.total_score)
                
                # new rating 저장
                if player1_new_rating < 0:
                    player1_new_rating = 0
                elif player2_new_rating < 0:
                    player2_new_rating = 0
                    
                # new ranking 반영
                player1_new_ranking = self.get_ranking(self.player1, player1_new_rating)
                player2_new_ranking = self.get_ranking(self.player2, player2_new_rating)
                
                # 게임 결과 전송
                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        'type': 'game_info',
                        'message_type': 'GAME_OVER',
                        'data': self.get_game_result(winner, player1_new_rating, player2_new_rating, 
                                                     player1_ranking, player1_new_ranking, player2_ranking, player2_new_ranking)
                    }
                )
                
                setattr(self.player1, 'total_score', player1_new_rating)
                setattr(self.player2, 'total_score', player2_new_rating)
                setattr(self.player1, 'matches', self.player1.matches + 1)
                setattr(self.player2, 'matches', self.player2.matches + 1)
                await database_sync_to_async(self.player1.save)()
                await database_sync_to_async(self.player2.save)()

                return False 
        
        return True

    def calculate_new_ratings(self, winner_rating, loser_rating, k_factor=32): # k_factor 임의 조정
        expected_win = self.expected_result(winner_rating, loser_rating)
        change_in_rating = k_factor * (1 - expected_win)
        
        winner_new_rating = winner_rating + change_in_rating
        loser_new_rating = loser_rating - change_in_rating

        return int(round(winner_new_rating)), int(round(loser_new_rating))

    def expected_result(self, player_rating, opponent_rating):
        return 1 / (1 + math.pow(10, (opponent_rating - player_rating) / 400))

    def get_ranking(self, player, player_score):
        # 특정 플레이어보다 높은 점수를 가진 플레이어 수를 계산합니다.
        higher_rank_count = Player.objects.filter(total_score__gt=player_score, is_superuser=False).exclude(id=player.id).count()
        
        # 특정 플레이어의 순위를 계산합니다.
        player_rank = higher_rank_count + 1

        return player_rank
        
    async def change_paddle_position(self, player_id, y_coordinate):
        # 플레이어 1의 패들 위치 업데이트
        if player_id == self.player1.id:
            self.player1_paddle_position[1] = y_coordinate
            message_type = "CHANGE_PLAYER1_PADDLE_POSTITION"

        # 플레이어 2의 패들 위치 업데이트
        elif player_id == self.player2.id:
            self.player2_paddle_position[1] = y_coordinate
            message_type = "CHANGE_PLAYER2_PADDLE_POSTITION"

        # 패들 위치 업데이트 후 게임 상태를 전송
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'game_info',
                'message_type': message_type,
                'data': self.get_paddle_position(player_id)  # 게임 상태 데이터
            }
        )
    
    async def start_game_loop(self):
        while True:
            try:
                # 공의 상태를 계산 중입니다.
                if not await self.calculate_ball_state():
                    break
                # 패들 위치 업데이트 후 게임 상태를 전송합니다.
                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        'type': 'game_info',
                        'message_type': 'BALL_POSITION',
                        'data': self.get_ball_position()  
                    }
                )
                await asyncio.sleep(0.016) # 60FPS로 설정
                
            except Exception as e:
                print(f"Error in game_loop: {e}")  # 게임 루프 실행 중 오류가 발생한 경우 오류 메시지를 출력

    async def game_info(self, event):
        data = event['data']
        message_type = event['message_type']

        await self.send(text_data=json.dumps({
            'type': message_type,
            'data': data,
        }))

    # ---------------------------------- data format ---------------------------------- #

    def get_game_state(self):
        game_state = {
            'player1': {
                'info': PlayerSerializer(self.player1).data,
                'position': list(self.player1_paddle_position),
                'score': self.player1_score,
            },
            'player2': {
                'info': PlayerSerializer(self.player2).data,
                'position': list(self.player2_paddle_position),
                'score': self.player2_score,
            },
            'ball': {
                'position': list(self.ball_position),
                'radius': BALL_RADIUS,
            },
            'walls': {
                'top': self.top_wall_y,
                'bottom': self.bottom_wall_y,
            },
            'speed': self.speed,
        }
        return game_state

    def get_ball_position(self):
        ball_position = {
            'position': list(self.ball_position)
        }
        return ball_position

    def get_score(self, player_id):
        if player_id == self.player1.id:
            score = {
                'score': self.player1_score
            }
        elif player_id == self.player2.id:
            score = {
                'score': self.player2_score
            }
        return score

    def get_game_result(self, winner, player1_new_rating, player2_new_rating, 
                        player1_ranking, player1_new_ranking, player2_ranking, player2_new_ranking):
        game_result = {
            'winner': PlayerSerializer(winner).data,
            'new_rating' : {
                'player1': {
                    'original': self.player1.total_score,
                    'new': player1_new_rating,
                    'difference': player1_new_rating - self.player1.total_score,
                },
                'player2': {
                    'original': self.player2.total_score,
                    'new': player2_new_rating,
                    'difference': player2_new_rating - self.player2.total_score,
                },
            },
            'new_ranking' : {
                'player1': {
                    'original': player1_ranking,
                    'new': player1_new_ranking,
                    'difference': player1_new_ranking - player1_ranking
                },
                'player2': {
                    'original': player2_ranking,
                    'new': player2_new_ranking,
                    'difference': player2_new_ranking - player2_ranking
                },
            }
        }
        return game_result

    def get_paddle_position(self, player_id):
        if player_id == self.player1.id:
            paddle_position = {
                'position': list(self.player1_paddle_position),
            }
        elif player_id == self.player2.id:
            paddle_position = {
                'position': list(self.player2_paddle_position),
            }
        return paddle_position

class TournamentGame(GameConsumer):
    def __init__(self, consumer_instance, player1, player2):
        super().__init__(consumer_instance)
        self.tournament = consumer_instance.tournament
        self.tournament_group_name = consumer_instance.tournament_group_name
        self.player1 = player1
        self.player2 = player2
        self.winner = None

    # 준결승
    async def start_tournament_semi_final_loop(self, consumer_instance):
        self.game_group_name = consumer_instance.tournament_semi_group_name
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'game_info',
                'message_type': 'START_TOURNAMENT_SEMI_FINAL',
                'data': self.get_game_state()  
            }
        )
        await asyncio.sleep(3)  
        while True:
            try:
                # 공의 상태를 계산 중입니다.
                if not await self.calculate_tournament_ball_state():
                    break
                # 패들 위치 업데이트 후 게임 상태를 전송합니다.
                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        'type': 'game_info',
                        'message_type': 'BALL_POSITION',
                        'data': self.get_ball_position()  
                    }
                )
                await asyncio.sleep(0.016) # 60FPS로 설정                
            except Exception as e:
                print(f"Error in semi_final_loop: {e}")  # 게임 루프 실행 중 오류가 발생한 경우 오류 메시지를 출력
        
        return self.winner
    
    # 결승
    async def start_tournament_final_loop(self, consumer_instance):
        self.game_group_name = consumer_instance.tournament_final_group_name
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'game_info',
                'message_type': 'START_TOURNAMENT_FINAL',
                'data': self.get_game_state()  
            }
        )
        await asyncio.sleep(3)  
        while True:
            try:
                # 공의 상태를 계산 중입니다.
                if not await self.calculate_tournament_ball_state():
                    break
                # 패들 위치 업데이트 후 게임 상태를 전송합니다.
                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        'type': 'game_info',
                        'message_type': 'BALL_POSITION',
                        'data': self.get_ball_position()  
                    }
                )
                await asyncio.sleep(0.016) # 60FPS로 설정
                
            except Exception as e:
                print(f"Error in final_loop: {e}")  # 게임 루프 실행 중 오류가 발생한 경우 오류 메시지를 출력

    async def calculate_tournament_ball_state(self):

        if self.init_ball_position == True:
            self.init_ball_position = False
            await asyncio.sleep(2)

        # 공의 위치 업데이트
        self.ball_position[0] += self.ball_dx
        self.ball_position[1] += self.ball_dy

        # 상단 및 하단 벽과의 충돌 처리
        if self.ball_position[1] - BALL_RADIUS < -WALL_HEIGHT_HALF or self.ball_position[1] + BALL_RADIUS > WALL_HEIGHT_HALF:
            self.ball_dy *= -1  # y축 방향 반전
            self.add_ball_speed *= -1

        # 패들과의 충돌 처리(x축 기준으로 동일한 위치이면서 y축기준으로 높이의 범위안에 들어오면 충돌로 간주)
        
        ## 왼쪽 패들 충돌
        if self.ball_position[0] - BALL_RADIUS < -WALL_WIDTH_HALF + PADDLE_WIDTH_HALF and \
        -PADDLE_HEIGHT_HALF < self.ball_position[1] - self.player1_paddle_position[1] < PADDLE_HEIGHT_HALF:
            self.ball_dx = abs(self.ball_dx)  # x축 방향 반전
            
            if self.slow_ball_speed == True:    # 처음에 느렸던 공 속도 원래대로
                self.ball_dx *= 2
                self.ball_dy *= 2
                self.slow_ball_speed = False
            else: # 속도 증가
                self.ball_dx += abs(self.add_ball_speed)
                self.ball_dy += self.add_ball_speed

            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_message',
                    'message_type': 'HIT_THE_BALL',
                    'message': "Player1 hit the ball"
                }
            )


        ## 오른쪽 패들 충돌
        if self.ball_position[0] + BALL_RADIUS > WALL_WIDTH_HALF - PADDLE_WIDTH_HALF and \
        -PADDLE_HEIGHT_HALF < self.ball_position[1] - self.player2_paddle_position[1] < PADDLE_HEIGHT_HALF:
            self.ball_dx = -abs(self.ball_dx)  # x축 방향 반전

            if self.slow_ball_speed == True:    # 처음에 느렸던 공 속도 원래대로
                self.ball_dx *= 2
                self.ball_dy *= 2
                self.slow_ball_speed = False
            else: # 속도 증가
                self.ball_dx -= abs(self.add_ball_speed)
                self.ball_dy += self.add_ball_speed

            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_message',
                    'message_type': 'HIT_THE_BALL',
                    'message': "Player2 hit the ball"
                }
            )

        # 좌우 벽과의 충돌 처리
        if self.ball_position[0] - BALL_RADIUS < -WALL_WIDTH_HALF or \
        self.ball_position[0] + BALL_RADIUS > WALL_WIDTH_HALF:
            # 점수 업데이트 및 공 위치 초기화 로직
            ## 왼쪽 벽 충돌
            if self.ball_position[0] - BALL_RADIUS < -WALL_WIDTH_HALF:
                self.player2_score += 1  # player2 점수 증가
                message_type = "PLAYER2_GET_SCORE"
                player_id = self.player2.id
            ## 오른쪽 벽 충돌
            elif self.ball_position[0] + BALL_RADIUS > WALL_WIDTH_HALF:
                self.player1_score += 1  # player1 점수 증가
                message_type = "PLAYER1_GET_SCORE"
                player_id = self.player1.id
            ### 공 위치 초기화
            self.ball_position = [0, random.randint(-100, 100)]
            self.init_ball_position = True
            if (self.player1_score + self.player2_score) % 2 == 0:
                self.ball_dx = self.speed
            else:
                self.ball_dx = -self.speed
            self.ball_dy = self.speed  * random.choice([-1, 1])
            self.slow_ball_speed = True 

            # 게임 스코어 전송
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_info',
                    'message_type': message_type,
                    'data': self.get_score(player_id)
                }
            )
            
        ## 스코어 충족으로 인한 게임종료
        if self.player1_score == SCORE_LIMIT or self.player2_score == SCORE_LIMIT:
            if self.player1_score == SCORE_LIMIT:
                self.winner = self.player1
            elif self.player2_score == SCORE_LIMIT:
                self.winner = self.player2

            # 결승전 끝났을 때
            if self.game_group_name == f'tournament_{self.tournament.id}_final':
                setattr(self.tournament, 'status', 1)
                setattr(self.tournament, 'winner', self.winner)
                await database_sync_to_async(self.tournament.save)()

                winner_ranking = self.get_ranking(self.winner, self.winner.total_score)

                # new rating 반영
                winner_new_rating = self.winner.total_score + 420
                
                # new ranking 반영
                winner_new_ranking = self.get_ranking(self.winner, winner_new_rating)
                
                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        'type': 'game_info',
                        'message_type': 'END_OF_FINAL',
                        'data': self.get_final_result(self.winner, winner_new_rating, winner_ranking, winner_new_ranking)
                    }
                )
                
                # new rating 저장
                setattr(self.winner, 'total_score', winner_new_rating)
                await database_sync_to_async(self.winner.save)()

            # 준결승 종료
            else:
                if self.game_group_name == f'tournament_{self.tournament.id}_A':
                    winner_message_type = 'GAME_RESULT_A'
                    end_game_message_type = 'END_OF_SEMI_FINAL_A'
                elif self.game_group_name == f'tournament_{self.tournament.id}_B':
                    winner_message_type = 'GAME_RESULT_B'
                    end_game_message_type = 'END_OF_SEMI_FINAL_B'

                # 게임 결과 전송
                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        'type': 'game_info',
                        'message_type': winner_message_type,
                        'data': self.get_semi_final_result(self.winner)
                    }
                )

                # 게임 결과 전송
                await self.channel_layer.group_send(
                    self.tournament_group_name,
                    {
                        'type': 'game_message',
                        'message_type': end_game_message_type,
                        'message': "The semi-final match is over."
                    }
                )

            return False
        
        return True
    
    def get_semi_final_result(self, winner):
        game_result = {
            'winner': PlayerSerializer(winner).data,
        }
        return game_result
    
    def get_final_result(self, winner, winner_new_rating, winner_ranking, winner_new_ranking):
        game_result = {
            'winner': PlayerSerializer(winner).data,
            'new_rating' : {
                'winner': {
                    'original': self.winner.total_score,
                    'new': winner_new_rating,
                    'difference': 420,
                }
            },
            'new_ranking' : {
                'winner': {
                    'original': winner_ranking,
                    'new': winner_new_ranking,
                    'difference': winner_new_ranking - winner_ranking
                }
            }
        }
        return game_result