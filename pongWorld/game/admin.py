from django.contrib import admin
from .models import Game, Tournament

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "player1", "player2", "player1_score", "player2_score", "winner", "mode", "input_device", "speed", "status")
    fields = ("player1", "player2")

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("id", "player1", "player2", "player3", "player4", "winner", "status")
    fields = ("player1", "player2", "player3", "player4")