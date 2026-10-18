"""
Education Admin Configuration
===============================

# EXAM DEFENSE: Admin Registration for StudentRecord
# =====================================================
# We register StudentRecord in the Django admin so the professor can:
# 1. Browse all student records during the live demo
# 2. See the risk_score and risk_factors computed by services.py
# 3. Filter by school_type, grade_trend, and risk status
# 4. Verify that the Faker-generated data looks realistic
"""

from django.contrib import admin
from apps.education.models import StudentRecord


@admin.register(StudentRecord)
class StudentRecordAdmin(admin.ModelAdmin):
    """Admin view for StudentRecord with read-friendly list display."""

    # --- List view configuration ---
    list_display = [
        'student_id',
        'first_name',
        'last_name',
        'school_type',
        'grade_level',
        'attendance_rate',
        'grade_trend',
        'behavior_notes_count',
        'risk_score',
        'case_status',
    ]
    list_filter = [
        'school_type',
        'grade_trend',
        'grade_level',
    ]
    search_fields = [
        'student_id',
        'first_name',
        'last_name',
        'school_name',
    ]

    # EXAM DEFENSE: readonly_fields prevents accidental edits to computed values.
    # The risk_score and risk_factors are SET by services.py, not by humans.
    readonly_fields = [
        'student_id',
        'risk_score',
        'risk_factors',
        'last_assessed_at',
        'created_at',
        'updated_at',
    ]

    # --- Custom computed column ---
    @admin.display(description='Case Status', ordering='case__status')
    def case_status(self, obj):
        """Show the linked Case's workflow status in the admin list."""
        return obj.case.get_status_display()
