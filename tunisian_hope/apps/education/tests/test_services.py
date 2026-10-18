"""
Tests for the Education Service Layer
========================================

# EXAM DEFENSE: Test Coverage Strategy
# =======================================
# We test the service layer at two levels:
#
# 1. Unit tests for evaluate_student_risk():
#    → Tests the pure risk-scoring function with various inputs
#    → No database needed for the logic itself (but we create model instances)
#
# 2. Integration tests for process_intake_cases():
#    → Creates real Cases + StudentRecords in the test database
#    → Verifies that at-risk cases are auto-transitioned to ASSESSMENT
#    → Checks that safe cases remain in INTAKE
#    → Validates that AuditLog entries are created
"""

import pytest
from datetime import date

from django.contrib.auth.models import User, Group

from apps.core.models import Case, AuditLog
from apps.education.models import StudentRecord
from apps.education.services import (
    evaluate_student_risk,
    process_intake_cases,
    ATTENDANCE_THRESHOLD,
    BEHAVIOR_THRESHOLD,
)


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def groups(db):
    """Get or create the 3 role groups."""
    roles = ['Field Operator', 'Supervisor', 'System Admin']
    return {name: Group.objects.get_or_create(name=name)[0] for name in roles}


@pytest.fixture
def operator(db, groups):
    """Create a Field Operator user for test cases."""
    user = User.objects.create_user(
        username='test_operator',
        password='testpass123',
        first_name='Test',
        last_name='Operator',
    )
    user.groups.add(groups['Field Operator'])
    return user


@pytest.fixture
def make_student(db, operator):
    """
    Factory fixture that creates a Case + StudentRecord pair.

    # EXAM DEFENSE: Factory Fixture Pattern
    # ========================================
    # Instead of creating full objects in every test, we use a "factory"
    # — a function that accepts keyword overrides. This keeps tests short:
    #   student = make_student(attendance_rate=60.0)
    # vs. writing 15 lines of Case + StudentRecord creation each time.
    """
    def _make(
        student_id=None,
        attendance_rate=95.0,
        grade_trend=StudentRecord.GradeTrend.STABLE,
        behavior_notes_count=0,
        status=Case.Status.INTAKE,
    ):
        # Auto-generate unique student_id if not provided
        if student_id is None:
            existing = StudentRecord.objects.count()
            student_id = f"TEST-{existing + 1:03d}"

        case = Case.objects.create(
            title=f"Test case for {student_id}",
            description="Test student record.",
            scenario=Case.Scenario.EDUCATION,
            status=status,
            assigned_operator=operator,
        )

        student = StudentRecord.objects.create(
            case=case,
            student_id=student_id,
            first_name='Test',
            last_name='Student',
            date_of_birth=date(2010, 1, 15),
            school_name='Test School',
            school_type=StudentRecord.SchoolType.MIDDLE,
            grade_level=8,
            attendance_rate=attendance_rate,
            grade_trend=grade_trend,
            behavior_notes_count=behavior_notes_count,
        )
        return student

    return _make


# =============================================================================
# UNIT TESTS — evaluate_student_risk()
# =============================================================================
class TestEvaluateStudentRisk:
    """Test the pure risk evaluation function."""

    def test_safe_student_no_risk(self, make_student):
        """A student with good attendance and stable grades → no risk."""
        student = make_student(attendance_rate=95.0, grade_trend='stable')
        result = evaluate_student_risk(student)

        assert result['is_at_risk'] is False
        assert result['risk_score'] == 0.0
        assert result['risk_factors'] == []

    def test_low_attendance_triggers_risk(self, make_student):
        """Attendance below 85% should flag the student."""
        student = make_student(attendance_rate=70.0)
        result = evaluate_student_risk(student)

        assert result['is_at_risk'] is True
        assert result['risk_score'] > 0
        assert any('attendance' in f.lower() for f in result['risk_factors'])

    def test_declining_grades_trigger_risk(self, make_student):
        """Declining grade trend should flag the student."""
        student = make_student(
            attendance_rate=90.0,  # Above threshold
            grade_trend=StudentRecord.GradeTrend.DECLINING,
        )
        result = evaluate_student_risk(student)

        assert result['is_at_risk'] is True
        assert 0.3 == result['risk_score']  # Only grade trend contributes
        assert any('declining' in f.lower() for f in result['risk_factors'])

    def test_high_behavior_notes_trigger_risk(self, make_student):
        """Behavior notes at or above threshold should flag the student."""
        student = make_student(
            attendance_rate=90.0,
            behavior_notes_count=5,
        )
        result = evaluate_student_risk(student)

        assert result['is_at_risk'] is True
        assert any('behavior' in f.lower() for f in result['risk_factors'])

    def test_multiple_risk_factors_compound(self, make_student):
        """Multiple risk factors should increase the risk score."""
        student = make_student(
            attendance_rate=60.0,
            grade_trend=StudentRecord.GradeTrend.DECLINING,
            behavior_notes_count=5,
        )
        result = evaluate_student_risk(student)

        assert result['is_at_risk'] is True
        assert len(result['risk_factors']) == 3  # All 3 factors present
        assert result['risk_score'] > 0.5  # Compounded score

    def test_risk_score_capped_at_one(self, make_student):
        """Even extreme values should not produce a risk_score > 1.0."""
        student = make_student(
            attendance_rate=10.0,  # Extremely low
            grade_trend=StudentRecord.GradeTrend.DECLINING,
            behavior_notes_count=20,
        )
        result = evaluate_student_risk(student)

        assert result['risk_score'] <= 1.0

    def test_attendance_exactly_at_threshold(self, make_student):
        """Attendance exactly at the threshold should NOT trigger risk."""
        student = make_student(attendance_rate=ATTENDANCE_THRESHOLD)
        result = evaluate_student_risk(student)

        # Exactly at threshold = NOT below it = safe
        assert not any('attendance' in f.lower() for f in result['risk_factors'])

    def test_behavior_below_threshold_safe(self, make_student):
        """Behavior notes below threshold should NOT trigger risk."""
        student = make_student(behavior_notes_count=BEHAVIOR_THRESHOLD - 1)
        result = evaluate_student_risk(student)

        assert not any('behavior' in f.lower() for f in result['risk_factors'])


# =============================================================================
# INTEGRATION TESTS — process_intake_cases()
# =============================================================================
class TestProcessIntakeCases:
    """Test the batch processing function that auto-transitions at-risk cases."""

    def test_at_risk_case_transitions_to_assessment(self, make_student, operator):
        """An at-risk INTAKE case should auto-transition to ASSESSMENT."""
        student = make_student(
            attendance_rate=60.0,
            grade_trend=StudentRecord.GradeTrend.DECLINING,
        )

        results = process_intake_cases(actor=operator)

        # Refresh from database to see the transition
        student.case.refresh_from_db()
        student.refresh_from_db()

        assert student.case.status == Case.Status.ASSESSMENT
        assert results['flagged'] == 1
        assert student.risk_score is not None
        assert student.risk_score > 0
        assert len(student.risk_factors) > 0

    def test_safe_case_stays_in_intake(self, make_student, operator):
        """A safe INTAKE case should remain in INTAKE status."""
        student = make_student(
            attendance_rate=95.0,
            grade_trend=StudentRecord.GradeTrend.IMPROVING,
        )

        results = process_intake_cases(actor=operator)

        student.case.refresh_from_db()
        assert student.case.status == Case.Status.INTAKE
        assert results['safe'] == 1

    def test_non_education_cases_ignored(self, db, operator):
        """Cases from other scenarios should NOT be processed."""
        # Create a Health scenario case (not Education)
        Case.objects.create(
            title="Health case",
            description="Should be ignored by education service.",
            scenario=Case.Scenario.HEALTH,
            assigned_operator=operator,
        )

        results = process_intake_cases(actor=operator)

        assert results['total_scanned'] == 0  # Not counted

    def test_non_intake_cases_ignored(self, make_student, operator):
        """Cases not in INTAKE status should NOT be processed."""
        # Create a case already in ASSESSMENT status
        student = make_student(
            attendance_rate=50.0,
            grade_trend=StudentRecord.GradeTrend.DECLINING,
            status=Case.Status.ASSESSMENT,  # Already past INTAKE
        )

        results = process_intake_cases(actor=operator)

        assert results['total_scanned'] == 0

    def test_audit_log_created_on_transition(self, make_student, operator):
        """Auto-transitions should create AuditLog entries."""
        student = make_student(
            attendance_rate=60.0,
            grade_trend=StudentRecord.GradeTrend.DECLINING,
        )

        process_intake_cases(actor=operator)

        # Check that an audit log was created for the transition
        audit_entries = AuditLog.objects.filter(
            target_model='Case',
            target_id=student.case.pk,
            action=AuditLog.Action.TRANSITION,
        )
        assert audit_entries.count() == 1
        assert audit_entries.first().actor == operator

    def test_mixed_batch_processing(self, make_student, operator):
        """Process a mix of safe and at-risk students correctly."""
        # Create 3 at-risk students
        for i in range(3):
            make_student(
                student_id=f"RISK-{i:03d}",
                attendance_rate=55.0 + i * 5,
                grade_trend=StudentRecord.GradeTrend.DECLINING,
            )

        # Create 2 safe students
        for i in range(2):
            make_student(
                student_id=f"SAFE-{i:03d}",
                attendance_rate=92.0 + i * 2,
                grade_trend=StudentRecord.GradeTrend.STABLE,
            )

        results = process_intake_cases(actor=operator)

        assert results['total_scanned'] == 5
        assert results['flagged'] == 3
        assert results['safe'] == 2
        assert results['errors'] == []

    def test_last_assessed_at_is_set(self, make_student, operator):
        """After assessment, last_assessed_at should be populated."""
        student = make_student(attendance_rate=70.0)

        assert student.last_assessed_at is None  # Before processing

        process_intake_cases(actor=operator)

        student.refresh_from_db()
        assert student.last_assessed_at is not None  # Now set
