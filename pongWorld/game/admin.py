from django.contrib import admin
from .models import Game
from .models import GamePlayer

admin.site.register(Game)
admin.site.register(GamePlayer)
