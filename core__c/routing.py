from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/chat/$', consumers.ChatConsumer.as_asgi()),
    # re_path(r"ws/online-users/$", consumers.OnlineUsersConsumer.as_asgi()),
    # You can add more routes like:
    # re_path(r'^ws/notification/$', consumers.NotificationConsumer.as_asgi()),
]
