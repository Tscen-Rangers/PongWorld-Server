from django.db import models
from config.models import TimestampBaseModel

class Player(TimestampBaseModel):
    nickname    = models.CharField(max_length=10)
    email       = models.EmailField(max_length=30)
    profile_img = models.URLField()
    intro       = models.CharField(max_length=200)
    matches     = models.PositiveIntegerField()
    wins        = models.PositiveIntegerField()
    total_score = models.PositiveIntegerField()

    class Meta:
        db_table = "player"

    def __str__(self):
        return f"Player ID {self.id}"

class Friend(TimestampBaseModel):
    follower      = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='followers')
    followed      = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='following')
    are_we_friend = models.BooleanField()

    class Meta:
        db_table = "friend"

    def __str__(self):
        return f"Player {self.follower_id.id} followed Player{self.followed_id.id}"

class Block(TimestampBaseModel):
    blocker    = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='blocks')
    blocked    = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='blocked_by')

    class Meta:
        db_table = "block"

    def __str__(self):
        return f"Player {self.blocker_id.id} blocked Player {self.blocked_id.id}"