"""
Core Application Configuration
================================

# EXAM DEFENSE: AppConfig
# ========================
# Every Django app needs an AppConfig class. The 'name' field must match
# the Python import path (apps.core). The ready() method is called once
# at startup — we use it to connect our post_migrate signal that
# automatically creates the 4 role Groups in the database.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for the Core application (roles, profiles, audit)."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core — Roles, Profiles & Audit'

    def ready(self):
        """
        Import signals when the app is ready.
        This connects our post_migrate handler that seeds role Groups.
        """
        # EXAM DEFENSE: We import signals inside ready() — not at module level —
        # to avoid circular imports. This is the Django-recommended pattern.
        import apps.core.signals  # noqa: F401
