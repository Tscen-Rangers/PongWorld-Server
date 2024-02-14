from django.contrib import admin
from .models import ChatRoom
from .models import JoinChatRoom
from .models import Message
from .models import UnreadMessage

admin.site.register(ChatRoom)
admin.site.register(JoinChatRoom)
admin.site.register(Message)
admin.site.register(UnreadMessage)
