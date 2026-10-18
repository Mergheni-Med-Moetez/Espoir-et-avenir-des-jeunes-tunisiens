"""
ASGI config for Tunisian Hope & Future.

# EXAM DEFENSE: ASGI (Asynchronous Server Gateway Interface) is the
# async successor to WSGI. It supports WebSockets and async views.
# We include it for future-proofing, even though we use WSGI for now.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_asgi_application()
