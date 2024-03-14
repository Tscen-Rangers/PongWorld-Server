from django.contrib import admin
from .models import Friend

@admin.register(Friend)
class FriendAdmin(admin.ModelAdmin):
    list_display = ("id", "follower", "followed", "are_we_friend")
    fields = ("follower", "followed", "are_we_friend")