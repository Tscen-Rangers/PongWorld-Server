from .game_config import *
from ..serializers import PlayerSerializer
from channels.db import database_sync_to_async
import asyncio
import random


# 세로 : 4.9
# 가로 : 6.8
# 공 지름 : 0.2
# 패들 가로 : 0.2
# 패들 세로 : 1.0

class GameConsumer:
    def __init__(self, consumer_instance):
        self.channel_layer = consumer_instance.channel_layer
        self.game = consumer_instance.game
        self.game_group_name = consumer_instance.game_group_name
        self.player1 = self.game.player1
        self.player2 = self.game.player2
        self.ball_position = [0, 0]
        self.player1_paddle_position = [-WALL_WIDTH_HALF, 0]
        self.player2_paddle_position = [WALL_WIDTH_HALF, 0]
        self.top_wall_y = WALL_HEIGHT_HALF
        self.bottom_wall_y = -WALL_HEIGHT_HALF
        self.speed = consumer_instance.game.speed
        self.player1_score = 0
        self.player2_score = 0
        self.score_limit = 10
        self.ball_dx = self.speed / 120
        self.ball_dy = self.speed / 120
    
    async def calculate_ball_state(self):

        # 공의 위치 업데이트
        self.ball_position[0] += self.ball_dx
        self.ball_position[1] += self.ball_dy

        # 상단 및 하단 벽과의 충돌 처리
        if self.ball_position[1] - BALL_RADIUS < -WALL_HEIGHT_HALF or self.ball_position[1] + BALL_RADIUS > WALL_HEIGHT_HALF:
            self.ball_dy *= -1  # y축 방향 반전

        # 패들과의 충돌 처리(x축 기준으로 동일한 위치이면서 y축기준으로 높이의 범위안에 들어오면 충돌로 간주)
        
        ## 왼쪽 패들 충돌
        if self.ball_position[0] - BALL_RADIUS < -WALL_WIDTH_HALF + PADDLE_WIDTH_HALF and \
        -PADDLE_HEIGHT_HALF < self.ball_position[1] - self.player1_paddle_position[1] < PADDLE_HEIGHT_HALF:
            self.ball_dx = abs(self.ball_dx)  # x축 방향 반전

        ## 오른쪽 패들 충돌
        if self.ball_position[0] + BALL_RADIUS > WALL_WIDTH_HALF - PADDLE_WIDTH_HALF and \
        -PADDLE_HEIGHT_HALF < self.ball_position[1] - self.player2_paddle_position[1] < PADDLE_HEIGHT_HALF:
            self.ball_dx = -abs(self.ball_dx)  # x축 방향 반전

        # 좌우 벽과의 충돌 처리
        if self.ball_position[0] - BALL_RADIUS < -WALL_WIDTH_HALF or \
        self.ball_position[0] + BALL_RADIUS > WALL_WIDTH_HALF:
            await asyncio.sleep(2)
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
            ### 공, 패들 위치 초기화
            self.ball_position = [0, 0]
            self.player1_paddle_position = [-WALL_WIDTH_HALF, 0]
            self.player2_paddle_position = [WALL_WIDTH_HALF, 0]
            self.ball_dx = -self.ball_dx  # 공의 방향을 반대로 변경
            self.ball_dy *= random.choice([-1, 1])

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
            if self.player1_score == self.score_limit or self.player2_score == self.score_limit:
                setattr(self.game, 'player1_score', self.player1_score)
                setattr(self.game, 'player2_score', self.player2_score)
                setattr(self.game, 'status', 2)
                # player1이 승리했을 때
                if self.player1_score == self.score_limit:
                    setattr(self.game, 'winner', self.player1)
                # player2가 승리했을 때
                elif self.player2_score == self.score_limit:
                    setattr(self.game, 'winner', self.player2)
                # 게임 결과 전송
                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        'type': 'game_info',
                        'message_type': 'GAME_OVER',
                        'data': self.get_game_result()
                    }
                )
                await database_sync_to_async(self.game.save)()
                return False 
        
        return True
        
    async def calculate_paddle_status(self, player_id, key_code):
        move_speed = self.speed / 10 # 패들의 이동 속도
        message_type = None

        # 플레이어 1의 패들 위치 업데이트
        if player_id == self.player1.id:
            if key_code == 38:  # 위쪽 화살표
                new_paddle_pos = self.player1_paddle_position[1] + move_speed
            elif key_code == 40:  # 아래쪽 화살표
                new_paddle_pos = self.player1_paddle_position[1] - move_speed
            else:
                return  # 다른 키 입력은 무시

            # 패들이 게임 영역 내에 있는지 확인
            if self.bottom_wall_y < new_paddle_pos - 0.5 and new_paddle_pos + 0.5 < self.top_wall_y:
                self.player1_paddle_position[1] = new_paddle_pos
                message_type = "CHANGE_PLAYER1_PADDLE_POSTITION"

        # 플레이어 2의 패들 위치 업데이트
        elif player_id == self.player2.id:
            if key_code == 38:  # 위쪽 화살표
                new_paddle_pos = self.player2_paddle_position[1] + move_speed
            elif key_code == 40:  # 아래쪽 화살표
                new_paddle_pos = self.player2_paddle_position[1] - move_speed
            else:
                return  # 다른 키 입력은 무시

            # 패들이 게임 영역 내에 있는지 확인
            if self.bottom_wall_y < new_paddle_pos - 0.5 and new_paddle_pos + 0.5 < self.top_wall_y:
                self.player2_paddle_position[1] = new_paddle_pos
                message_type = "CHANGE_PLAYER2_PADDLE_POSTITION"

        # 패들 위치 업데이트 후 게임 상태를 전송
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'game_info',  # common_utils.py에서 처리할 수 있는 메시지 타입
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

    def get_game_result(self):
        game_result = {
            'winner': PlayerSerializer(self.game.winner).data,
        }
        return game_result