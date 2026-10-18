"""
Dashboard Application Configuration
======================================

# EXAM DEFENSE: Dashboard App — Role of This App
# ==================================================
# The dashboard app is responsible for all HTML views:
# - Supervisor KPI dashboard (the main page)
# - Student list and at-risk student views
# - Future: case detail views, intervention forms
#
# It is deliberately separated from the API app because:
# - API returns JSON/GraphQL (machine-readable)
# - Dashboard returns HTML (human-readable)
# - Different consumers, different rendering logic
"""

from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """Configuration for the Dashboard views."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    verbose_name = 'Dashboard & Views'
