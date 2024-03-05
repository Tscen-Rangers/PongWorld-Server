from urllib.parse import parse_qs

from jwt import decode as jwt_decode, exceptions as jwt_exceptions

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

from player.models import Player

@database_sync_to_async
def get_user(validated_token):
    try:
        user = Player.objects.get(id=validated_token["user_id"])
        return user
    except Player.DoesNotExist:
        return AnonymousUser()

class JwtAuthMiddleware(BaseMiddleware):

    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        close_old_connections()

        token = parse_qs(scope["query_string"].decode("utf8"))["token"][0]

        try:
            decoded_token = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            scope["user"] = await get_user(validated_token=decoded_token)
        except (ValueError, jwt_exceptions.DecodeError, jwt_exceptions.ExpiredSignatureError):
            await send({
                'type': 'websocket.close',
                'code': 4003
            })
            return

        return await super().__call__(scope, receive, send)

def JwtAuthMiddlewareStack(inner):
    return JwtAuthMiddleware(AuthMiddlewareStack(inner))