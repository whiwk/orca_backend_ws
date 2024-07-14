import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.layers import get_channel_layer
import shell.routing
import monitoring.routing
import sniff.routing
import protocolstack.routing
import logs.routing

# Set the default Django settings module for the 'asgi' application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orca_backend_ws.settings')

# Initialize Django ASGI application early to ensure the models are ready
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            shell.routing.websocket_urlpatterns +
            monitoring.routing.websocket_urlpatterns +
            sniff.routing.websocket_urlpatterns +
            protocolstack.routing.websocket_urlpatterns +
            logs.routing.websocket_urlpatterns
        )
    ),
})

channel_layer = get_channel_layer()
