"""
WSGI config for Tunisian Hope & Future.

# EXAM DEFENSE: WSGI (Web Server Gateway Interface) is the standard
# interface between Python web applications and web servers.
# In production, a server like Gunicorn uses this file to serve the app.
# In development, `manage.py runserver` uses it automatically.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()
