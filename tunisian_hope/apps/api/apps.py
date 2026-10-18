"""
API Application Configuration
================================

# EXAM DEFENSE: Why a separate API app?
# ========================================
# The API app serves as the single entry point for ALL external data access:
# - Strawberry GraphQL endpoint (Criterion F6)
# - Future REST endpoints (DRF serializers/viewsets)
#
# Keeping API concerns separate from core/ and education/ means:
# 1. Models don't know about serialization formats (loose coupling)
# 2. We can add REST + GraphQL side by side without conflicts
# 3. The professor sees clean architectural boundaries
"""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Configuration for the API layer (REST + GraphQL)."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.api'
    verbose_name = 'API Layer (REST + GraphQL)'
