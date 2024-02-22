from django.contrib import admin
from .models import Game

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "player1", "player2", "player1_score", "player2_score", "winner", "mode", "input_device", "speed")
    fields = ("player1", "player2")