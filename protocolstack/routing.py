from django.urls import path
from .consumers import ProtocolStackConsumer

websocket_urlpatterns = [
    path('ws/protocolstack/', ProtocolStackConsumer.as_asgi()),
]
