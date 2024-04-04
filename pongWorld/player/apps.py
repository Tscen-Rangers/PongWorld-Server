import os 
import sys
from django.apps import AppConfig
from django.apps import apps

def reset_online_count(**kwargs):
    from player.models import Player
    Player.objects.update(online_count=0)

class PlayerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'player'

    def ready(self):
        if apps.ready:
            if 'runserver' not in sys.argv:
                return True
            
            if not os.environ.get('RESET_ONLINE_COUNT'):
                os.environ['RESET_ONLINE_COUNT'] = 'True'
                reset_online_count()

            # post_migrate 신호를 사용하여 모든 마이그레이션이 완료된 후에 reset_online_count 함수를 호출합니다.
            post_migrate.connect(reset_online_count, sender=self)