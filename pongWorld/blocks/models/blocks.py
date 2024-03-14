from django.db import models
from config.models import TimestampBaseModel
from player.models import Player

class Block(TimestampBaseModel):
    blocker    = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='blocks')
    blocked    = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='blocked_by')

    class Meta:
        db_table = "block"

    def __str__(self):
        return f"Player {self.blocker.id} blocked Player {self.blocked.id}"