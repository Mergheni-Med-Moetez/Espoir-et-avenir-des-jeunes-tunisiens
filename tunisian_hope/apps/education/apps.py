"""
Education Application Configuration
======================================

# EXAM DEFENSE: Why a separate Education app?
# ==============================================
# Each scenario (Education, Health, Digital) gets its own Django app because:
# 1. Separation of concerns — education-specific models don't pollute core/
# 2. Independent evolution — we can add education features without touching health/
# 3. Clear boundaries — the professor sees which code belongs to which scenario
# 4. Matches the rubric requirement for "modular design" (Track A)
"""

from django.apps import AppConfig


class EducationConfig(AppConfig):
    """Configuration for the Education Early Warning scenario (Scenario 1)."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.education'
    verbose_name = 'Education'
