from django.db import models
from player.models import Player
from config.models import TimestampBaseModel

class Game(TimestampBaseModel):
    player1 = models.ForeignKey(Player, related_name='player1_id', on_delete=models.SET_NULL, null=True, blank=True)
    player2 = models.ForeignKey(Player, related_name='player2_id', on_delete=models.SET_NULL, null=True, blank=True)
    player1_score = models.PositiveIntegerField(null=True, blank=True)
    player2_score = models.PositiveIntegerField(null=True, blank=True)
    winner = models.ForeignKey(Player, related_name='winner_id', on_delete=models.SET_NULL, null=True, blank=True)
    
    GAME_MODES_CHOICES = (
        (0, 'Quick Match'),
        (1, 'Invite Friend'),
    )
    mode = models.CharField(
        max_length=1,
        choices=GAME_MODES_CHOICES,
        default=0,
    )

    DEVICE_MODES_CHOICES = (
        (0, 'KeyBoard'),
        (1, 'Mouse'),
    )
    input_device = models.CharField(
        max_length=1,
        choices=DEVICE_MODES_CHOICES,
        default=0,
    )

    GAME_LEVEL_CHOICES = (
        (0, 'Easy'),
        (1, 'Normal'),
        (2, 'Hard'),
    )
    speed = models.CharField(
        max_length=1,
        choices=GAME_LEVEL_CHOICES,
        default=1,
    )

    class Meta:
        db_table = "game"

    def __str__(self):
        return f"Game {self.id}"

