# mylogin/routing.py
from django.urls import re_path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    # ใช้ thread_id เป็น room
    re_path(r'ws/chat/(?P<thread_id>\d+)/$', ChatConsumer.as_asgi()),
]