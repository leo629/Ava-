
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.core.asgi import get_asgi_application
# DO NOT import routing at the top

# Import inside the block where apps are ready
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            __import__("chat.routing").routing.websocket_urlpatterns
        )
    ),
})
