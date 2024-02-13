from django.db import models

class Player(models.Model):
    nickname    = models.CharField(max_length=10)
    email       = models.EmailField(max_length=30)
    profile_img = models.URLField()
    intro       = models.CharField(max_length=200)
    matches     = models.PositiveIntegerField()
    wins        = models.PositiveIntegerField()
    total_score = models.PositiveIntegerField()
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Player ID {self.id}"

class Friend(models.Model):
    follower_id   = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='followers')
    followed_id   = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='following')
    are_we_friend = models.BooleanField()
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Player {self.follower_id.id} followed Player{self.followed_id.id}"

class Block(models.Model):
    blocker_id = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='blocks')
    blocked_id = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Player {self.blocker_id.id} blocked Player {self.blocked_id.id}"