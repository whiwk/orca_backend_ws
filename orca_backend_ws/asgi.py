import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.layers import get_channel_layer
import shell.routing
import monitoring.routing
import sniff.routing
import protocolstack.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orca_backend_ws.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            shell.routing.websocket_urlpatterns +
            monitoring.routing.websocket_urlpatterns +
            sniff.routing.websocket_urlpatterns +
            protocolstack.routing.websocket_urlpatterns
        )
    ),
})

channel_layer = get_channel_layer()
