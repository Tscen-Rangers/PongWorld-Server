from channels.middleware import BaseMiddleware
from player.models import Player
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from jwt import decode as jwt_decode
from django.conf import settings
from channels.auth import AuthMiddlewareStack

@database_sync_to_async
def get_user(validated_token):
    try:
        user = Player.objects.get(id=validated_token["user_id"])
        return user
    except User.DoesNotExist:
        return AnonymousUser()

class JwtAuthMiddleware(BaseMiddleware):

    def __init(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])
        if b'authorization' in headers:
            token_name, token_key = headers[b'authorization'].decode().split()
            if token_name == 'Bearer':
                decoded_data = jwt_decode(token_key, settings.SECRET_KEY, algorithms=["HS256"])
                scope["user"] = await get_user(validated_token=decoded_data)
        return await super().__call__(scope, receive, send)

def JwtAuthMiddlewareStack(inner):
    return JwtAuthMiddleware(AuthMiddlewareStack(inner))