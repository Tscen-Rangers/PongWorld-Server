from django.db import models
from player.models import Player

class Game(models.Model):
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "game"

    def __str__(self):
        return f"Game {self.id}"

class GamePlayer(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    is_winner = models.BooleanField()
    score = models.PositiveIntegerField()
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "game_player"

    def __str__(self):
        return f"Player {self.player.nickname} - Game {self.game.id}"


