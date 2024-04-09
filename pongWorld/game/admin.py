from django.contrib import admin
from .models import Game, Tournament

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "player1", "player2", "player1_score", "player2_score", "winner", "mode", "speed", "status", "player1_status", "player2_status")
    fields = ("player1", "player2", "player1_score", "player2_score", "winner", "mode", "speed", "status")

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("id", "player1", "player2", "player3", "player4", "winner", "status", "player1_status", "player2_status", "player3_status", "player4_status")
    fields = ("player1", "player2", "player3", "player4", "status")