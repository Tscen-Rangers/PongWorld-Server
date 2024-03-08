from django.contrib import admin
from .models import Player, Friend


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("id", "nickname", "email", "profile_img", "intro", "matches", "wins", "total_score")
    fields = ("nickname", "email", "profile_img", "intro", "matches", "wins", "total_score")

@admin.register(Friend)
class FriendAdmin(admin.ModelAdmin):
    list_display = ("id", "follower", "followed", "are_we_friend")
    fields = ("follower", "followed", "are_we_friend")