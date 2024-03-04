from .game_config import *
from ..serializers import PlayerSerializer

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