from django.contrib import admin
from .models import Player

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("id", "nickname", "email", "profile_img", "intro", "matches", "wins", "total_score", "online_count", "two_factor_auth_enabled")
    fields = ("nickname", "email", "profile_img", "intro", "matches", "wins", "total_score", "online_count", "two_factor_auth_enabled")
