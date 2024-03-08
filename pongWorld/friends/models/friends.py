from django.db import models
from player.models import Player
from config.models import TimestampBaseModel

class Friend(TimestampBaseModel):
    follower      = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='followers')
    followed      = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='following')
    are_we_friend = models.BooleanField(default=False)

    class Meta:
        db_table = "friend"

    def __str__(self):
        return f"Player {self.follower.id} followed Player{self.followed.id}"

