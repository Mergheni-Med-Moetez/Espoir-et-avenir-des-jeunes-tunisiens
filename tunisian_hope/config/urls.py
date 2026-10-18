"""
Tunisian Hope & Future — URL Configuration
============================================

# EXAM DEFENSE: URL Routing Design
# ==================================
# We use Django's include() to delegate URL routing to each app.
# This keeps config/urls.py short and each app self-contained.
# The admin site is mounted at /admin/ (Django's built-in admin interface).
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from strawberry.django.views import GraphQLView
from apps.api.schema import schema


urlpatterns = [
    # --- Django Admin ---
    path('admin/', admin.site.urls),

    # --- Strawberry GraphQL API ---
    # EXAM DEFENSE: GraphQL Endpoint
    # ================================
    # We mount the Strawberry GraphQL view at /graphql/.
    # The GraphiQL playground (interactive API explorer) is enabled
    # automatically when DEBUG=True — the professor can test queries
    # live during the demo without needing Postman or curl.
    path('graphql/', GraphQLView.as_view(schema=schema)),

    # --- App URLs (will be added as apps are built) ---
    # path('cases/', include('apps.cases.urls')),       # TODO: Case views
    path('', include('apps.dashboard.urls')),            # Dashboard (root URL)
]

# --- Serve media files in development ---
# EXAM DEFENSE: In production, media files are served by nginx/Apache,
# not Django. This line only works when DEBUG=True.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# --- Customize admin site header ---
admin.site.site_header = 'Tunisian Hope & Future — Administration'
admin.site.site_title = 'Tunisian Hope & Future'
admin.site.index_title = 'Platform Administration'
