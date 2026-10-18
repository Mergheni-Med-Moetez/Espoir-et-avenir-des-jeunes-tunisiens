#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.

# EXAM DEFENSE: manage.py
# ========================
# This is the standard entry point for all Django management commands
# (runserver, migrate, createsuperuser, etc.). The only customization
# is pointing DJANGO_SETTINGS_MODULE to 'config.settings' instead of
# the default project-named module, to keep our folder structure clean.
"""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
