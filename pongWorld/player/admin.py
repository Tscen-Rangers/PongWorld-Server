from django.contrib import admin
from .models import Player
from .models import Friend
from .models import Block

admin.site.register(Player)
admin.site.register(Friend)
admin.site.register(Block)

