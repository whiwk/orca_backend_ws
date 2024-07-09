from django.urls import path
from .consumers import SniffConsumer

websocket_urlpatterns = [
    path('ws/sniff/', SniffConsumer.as_asgi()),
]
