from django.urls import path
from .consumers import ShellConsumer

websocket_urlpatterns = [
    path('ws/shell/', ShellConsumer.as_asgi()),
]
