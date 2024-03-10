import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

from game.socket.routing import game_websocket_urlpatterns
from websocket.routing import websocket_urlpatterns as first_websocket_urlpatterns
from .middleware import JwtAuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

websocket_urlpatterns = first_websocket_urlpatterns + game_websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            JwtAuthMiddlewareStack(
                URLRouter(
                    websocket_urlpatterns
                )
            )
        )
    }
)
