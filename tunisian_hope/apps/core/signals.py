"""
Core Signals — Auto-create Role Groups on Migration
=====================================================

# EXAM DEFENSE: Signals — Why post_migrate?
# ============================================
# Django signals are like "event hooks" — they run custom code when
# something happens (a model saves, a request starts, migrations finish, etc.).
#
# We use the post_migrate signal to automatically create the 4 role Groups
# every time `python manage.py migrate` runs. This guarantees that the
# Groups exist in ANY environment (dev, test, production) without manual setup.
#
# Alternative: A management command (seed_groups.py) — we provide that too
# for explicit seeding. But the signal is the safety net.
"""

import logging

from django.db.models.signals import post_migrate
from django.dispatch import receiver

from apps.core.models import ROLES

logger = logging.getLogger(__name__)


@receiver(post_migrate, sender=None)
def create_default_groups(sender, **kwargs):
    """
    Create the 4 role Groups if they don't already exist.

    # EXAM DEFENSE: get_or_create() Pattern
    # =======================================
    # get_or_create() either fetches an existing record or creates a new one.
    # It returns a tuple: (object, created_boolean).
    # This is idempotent — running it 100 times has the same effect as once.
    # No duplicate Groups, no errors on repeated migrations.
    """
    # We import Group here (not at module level) to avoid issues if
    # the auth app hasn't been migrated yet during initial setup.
    from django.contrib.auth.models import Group

    for role_name in ROLES:
        group, created = Group.objects.get_or_create(name=role_name)
        if created:
            logger.info("Created role group: '%s'", role_name)
