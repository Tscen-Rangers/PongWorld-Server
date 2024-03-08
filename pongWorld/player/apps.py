import os 
import sys

from django.apps import AppConfig


class PlayerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'player'

    def ready(self):

        def reset_online_count():
            Player.objects.update(online_count = 0)

        if 'runserver' not in sys.argv:
            return True

        from django.db.models.signals import post_migrate
        from player.models import Player
        
        if not os.environ.get('RESET_ONLINE_COUNT'):
            os.environ['RESET_ONLINE_COUNT'] = 'True'
            reset_online_count()