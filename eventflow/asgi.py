import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eventflow.settings")

# ตรงนี้ Django จะ setup settings ให้เรียบร้อย
django_asgi_app = get_asgi_application()

# ค่อย import routing หลังจาก settings พร้อมแล้ว
import mylogin.routing  # noqa: E402  (ถ้าใช้ flake8)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            mylogin.routing.websocket_urlpatterns
        )
    ),
})