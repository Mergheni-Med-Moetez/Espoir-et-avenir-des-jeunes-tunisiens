"""
Education Models — Student Records for the Education Early Warning Scenario
=============================================================================

# EXAM DEFENSE: StudentRecord Model Design
# ===========================================
# This model stores education-specific data that is linked to a Case record.
# We use a OneToOneField to Case because:
#   - Each Case in the EDUCATION scenario has exactly ONE student record
#   - We can access it via case.student_record (reverse relation)
#   - We can also go the other way: student_record.case
#
# Why not put these fields directly on Case?
# → Because Case is shared across ALL scenarios (Education, Health, Digital).
#   Putting attendance_rate on Case would be meaningless for Health cases.
#   This separation keeps models focused and avoids nullable fields everywhere.
"""

from django.db import models


class StudentRecord(models.Model):
    """
    Education-specific data linked to a Case via OneToOneField.

    # EXAM DEFENSE: StudentRecord — Scenario-Specific Extension
    # ===========================================================
    # The Case model holds workflow data (status, priority, assigned users).
    # The StudentRecord holds EDUCATION-SPECIFIC data (attendance, grades).
    #
    # This is the "multi-table inheritance alternative" pattern:
    # instead of subclassing Case (which creates confusing implicit JOINs),
    # we use an explicit OneToOneField. This is clearer, easier to query,
    # and simpler to explain in the oral defense.
    #
    # Access patterns:
    #   case.student_record          → get the student data for a case
    #   student.case.status          → get the workflow status for a student
    #   StudentRecord.objects.select_related('case')  → single query for both
    """

    # --- Enums ---
    class SchoolType(models.TextChoices):
        """Type of educational institution."""
        MIDDLE = 'middle', 'Middle School'
        HIGH = 'high', 'High School'

    class GradeTrend(models.TextChoices):
        """
        Direction of the student's academic performance over the last term.

        # EXAM DEFENSE: GradeTrend is a key risk indicator.
        # 'declining' combined with low attendance triggers auto-assessment.
        """
        IMPROVING = 'improving', 'Improving'
        STABLE = 'stable', 'Stable'
        DECLINING = 'declining', 'Declining'

    # --- Relationship to Case ---
    case = models.OneToOneField(
        'core.Case',
        on_delete=models.CASCADE,
        related_name='student_record',
        help_text='The Case record this student data belongs to.',
    )

    # --- Student Identity (all synthetic) ---
    student_id = models.CharField(
        max_length=20,
        unique=True,
        help_text='Synthetic student identifier (e.g., STU-2026-001).',
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(
        help_text='Student date of birth (synthetic data).',
    )

    # --- School Information ---
    school_name = models.CharField(
        max_length=200,
        help_text='Name of the school (synthetic).',
    )
    school_type = models.CharField(
        max_length=20,
        choices=SchoolType.choices,
        help_text='Middle school or high school.',
    )
    grade_level = models.PositiveIntegerField(
        help_text='Current grade/year level (e.g., 7 for 7th grade).',
    )

    # --- Risk Indicators ---
    # EXAM DEFENSE: These 3 fields are the core inputs to our risk assessment.
    # The service layer (services.py) reads these values and computes a risk score.
    # If the score exceeds a threshold, the linked Case auto-transitions to ASSESSMENT.
    attendance_rate = models.FloatField(
        help_text='30-day attendance rate as a percentage (0.0 to 100.0).',
    )
    grade_trend = models.CharField(
        max_length=20,
        choices=GradeTrend.choices,
        help_text='Academic performance direction over the last term.',
    )
    behavior_notes_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of behavior incident notes in the last 30 days.',
    )

    # --- Computed Risk Assessment (filled by services.py) ---
    risk_score = models.FloatField(
        null=True,
        blank=True,
        help_text='Computed risk score (0.0 = safe, 1.0 = critical). Set by the service layer.',
    )
    risk_factors = models.JSONField(
        default=list,
        blank=True,
        help_text='List of human-readable risk factor descriptions.',
    )
    last_assessed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the risk assessment was last run on this student.',
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student Record'
        verbose_name_plural = 'Student Records'

        # EXAM DEFENSE: Index on attendance_rate for fast "show at-risk students" queries.
        # The dashboard will frequently filter: WHERE attendance_rate < 85.0
        indexes = [
            models.Index(
                fields=['attendance_rate'],
                name='idx_student_attendance',
            ),
        ]

    def __str__(self):
        """e.g., 'STU-2026-001 — Ahmed Ben Ali (Middle School, 78.5% attendance)'"""
        return (
            f"{self.student_id} — {self.first_name} {self.last_name} "
            f"({self.get_school_type_display()}, {self.attendance_rate}% attendance)"
        )
