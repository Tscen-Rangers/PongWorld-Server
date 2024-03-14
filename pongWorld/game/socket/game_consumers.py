from .game_config import *
from ..serializers import PlayerSerializer
from channels.db import database_sync_to_async
import asyncio

# 세로 : 4.9
# 가로 : 6.8
# 공 지름 : 0.2
# 패들 가로 : 0.2
# 패들 세로 : 1.0

class GameConsumer:
    def __init__(self, player1, player2, speed):
        self.player1 = player1
        self.player2 = player2
        self.ball_position = [0, 0]
        self.player1_paddle_position = [-WALL_WIDTH_HALF, 0]
        self.player2_paddle_postiiton = [0, WALL_WIDTH_HALF]
        self.top_wall_y = WALL_HEIGHT_HALF
        self.bottom_wall_y = -WALL_HEIGHT_HALF
        self.ball_radius = BALL_RADIUS
        self.paddle_height_half = PADDLE_HEIGHT_HALF
        self.speed = speed
        self.player1_score = 0
        self.player2_score = 0

    # def update_game_state(self, input_data):
    #     # 플레이어 입력을 기반으로 게임 상태를 업데이트합니다 (예: 패들 이동)
    #     # 볼 이동, 충돌 감지, 점수 계산 등을 수행합니다.
    
    async def calculate_ball_state(self):
        paddle_height = 1.0  # 패들의 높이
        canvas_width_half = 4.9  # 캔버스의 너비의 절반
        canvas_height_half = 6.8  # 캔버스의 높이의 절반
        ball_radius = 0.2  # 공의 반지름
        self.ball_dx = self.speed
        self.ball_dy = self.speed

        # 공의 위치 업데이트
        self.ball_position[0] += self.ball_dx
        self.ball_position[1] += self.ball_dy

        # 상단 및 하단 벽과의 충돌 처리
        if self.ball_position[1] - ball_radius < -canvas_height_half or self.ball_position[1] + ball_radius > canvas_height_half:
            self.ball_dy *= -1  # y축 방향 반전

        # 패들과의 충돌 처리(x축 기준으로 동일한 위치이면서 y축기준으로 높이의 범위안에 들어오면 충돌로 간주)
        
        ## 왼쪽 패들 충돌
        if self.ball_position[0] - ball_radius < -canvas_width_half + 0.1 and \
        -paddle_height / 2 < self.ball_position[1] - self.player1_paddle_position[1] < paddle_height / 2:
            self.ball_dx = abs(self.ball_dx)  # x축 방향 반전

        ## 오른쪽 패들 충돌
        if self.ball_position[0] + ball_radius > canvas_width_half - 0.1 and \
        -paddle_height / 2 < self.ball_position[1] - self.player2_paddle_position[1] < paddle_height / 2:
            self.ball_dx = -abs(self.ball_dx)  # x축 방향 반전

        # 좌우 벽과의 충돌 처리
        if self.ball_position[0] - ball_radius < -canvas_width_half or \
        self.ball_position[0] + ball_radius > canvas_width_half:
            # 점수 업데이트 및 공 위치 초기화 로직
            ## 왼쪽 벽 충돌
            if self.ball_position[0] - ball_radius < -canvas_width_half:
                self.player2_score += 1  # player2 점수 증가
                ### 공 위치 초기화
                self.ball_position = [0, 0]
                self.ball_dx = -self.ball_dx  # 공의 방향을 반대로 변경

            ## 오른쪽 벽 충돌
            elif self.ball_position[0] + ball_radius > canvas_width_half:
                self.player1_score += 1  # player1 점수 증가
                ### 공 위치 초기화
                self.ball_position = [0, 0]
                self.ball_dx = -self.ball_dx  # 공의 방향을 반대로 변경
            ## 스코어 충족으로 인한 게임종료
            if self.player1_score == self.score_limit or self.player2_score == self.score_limit:
                print("GAME OVER")
                setattr(self.game, 'status', 2)
                await database_sync_to_async(self.game.save)()
        
        
    async def calculate_paddle_state(self, player_id, key_code):
        move_speed = self.speed  # 패들의 이동 속도

        # 플레이어 1의 패들 위치 업데이트
        if player_id == self.player1.id:
            if key_code == 38:  # 위쪽 화살표
                new_paddle_pos = self.player1_paddle_position[1] - move_speed
            elif key_code == 40:  # 아래쪽 화살표
                new_paddle_pos = self.player1_paddle_position[1] + move_speed
            else:
                return  # 다른 키 입력은 무시

            # 패들이 게임 영역 내에 있는지 확인
            if -self.bottom_wall_y < new_paddle_pos < self.top_wall_y:
                self.player1_paddle_position[1] = new_paddle_pos

        # 플레이어 2의 패들 위치 업데이트
        elif player_id == self.player2.id:
            if key_code == 38:  # 위쪽 화살표
                new_paddle_pos = self.player2_paddle_position[1] - move_speed
            elif key_code == 40:  # 아래쪽 화살표
                new_paddle_pos = self.player2_paddle_position[1] + move_speed
            else:
                return  # 다른 키 입력은 무시

            # 패들이 게임 영역 내에 있는지 확인
            if -self.bottom_wall_y < new_paddle_pos < self.top_wall_y:
                self.player2_paddle_position[1] = new_paddle_pos
        # 패들 위치 업데이트 후 게임 상태를 전송
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'game_info',  # common_utils.py에서 처리할 수 있는 메시지 타입
                'data': self.get_game_state()  # 게임 상태 데이터
            }
    )
    
    
    async def start_game_loop(self):
        while True:
            try:
                print("CALCULATING BALL STATE")  # 공의 상태를 계산 중입니다.
                await self.calculate_ball_state()
                # 패들 위치 업데이트 후 게임 상태를 전송합니다.
                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        'type': 'game_info',  
                        'data': self.get_game_state()  
                    }
                )
                await asyncio.sleep(0.016) # 60FPS로 설정
                
            except Exception as e:
                print(f"Error in game_loop: {e}")  # 게임 루프 실행 중 오류가 발생한 경우 오류 메시지를 출력

    def get_game_state(self):
        # 현재 게임 상태를 반환합니다 (패들 및 볼의 위치, 점수 등)
        game_state = {
            'player1': {
                'info': PlayerSerializer(self.player1).data,
                'position': list(self.player1_paddle_position),
                'score': self.player1_score,
            },
            'player2': {
                'info': PlayerSerializer(self.player2).data,
                'position': list(self.player2_paddle_postiiton),
                'score': self.player2_score,
            },
            'ball': {
                'position': list(self.ball_position),
                'radius': self.ball_radius,
            },
            'walls': {
                'top': self.top_wall_y,
                'bottom': self.bottom_wall_y,
            },
            'speed': self.speed,
        }
        return game_state