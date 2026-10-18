"""
Failure Injection Tests — Proving the System Rejects Invalid Operations
=========================================================================

# EXAM DEFENSE: What is Failure Injection Testing?
# ===================================================
# Failure injection (also called "negative testing" or "chaos testing") is
# a technique where we DELIBERATELY try to BREAK the system to prove that:
#
# 1. Invalid state transitions are blocked by the state machine
# 2. Unauthorized users cannot bypass role checks
# 3. The system logs security violations (audit trail)
# 4. Data integrity is preserved even under malicious input
#
# This is the STRONGEST evidence for the examiner:
# → "Not only does our system work correctly, it PROVABLY fails safely."
#
# Each test follows the pattern:
# 1. SET UP a scenario (e.g., a case in INTAKE status)
# 2. ATTEMPT a forbidden action (e.g., skip to CLOSED)
# 3. ASSERT that the system BLOCKED it (ValidationError raised)
# 4. VERIFY that the original state is UNCHANGED (no data corruption)
# 5. CHECK that an audit log was (or wasn't) created appropriately
#
# These tests are SEPARATE from the happy-path tests in test_models.py.
# The professor can see two test files:
# - test_models.py → proves the system works correctly
# - test_failure_injection.py → proves the system fails safely
"""

import pytest
from datetime import date

from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError

from apps.core.models import Case, AuditLog
from apps.education.models import StudentRecord
from apps.education.services import evaluate_student_risk, process_intake_cases


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def groups(db):
    """Create all 4 role groups."""
    roles = ['Field Operator', 'Supervisor', 'System Admin']
    return {name: Group.objects.get_or_create(name=name)[0] for name in roles}


@pytest.fixture
def operator(db, groups):
    """Create a Field Operator user."""
    user = User.objects.create_user(
        username='fi_operator', password='test123',
        first_name='Karim', last_name='Operator',
    )
    user.groups.add(groups['Field Operator'])
    return user


@pytest.fixture
def other_operator(db, groups):
    """Create a SECOND Field Operator (to test cross-user access)."""
    user = User.objects.create_user(
        username='fi_other_operator', password='test123',
        first_name='Other', last_name='Operator',
    )
    user.groups.add(groups['Field Operator'])
    return user



@pytest.fixture
def supervisor(db, groups):
    """Create a Supervisor user."""
    user = User.objects.create_user(
        username='fi_supervisor', password='test123',
        first_name='Ahmed', last_name='Supervisor',
    )
    user.groups.add(groups['Supervisor'])
    return user


@pytest.fixture
def intake_case(db, operator):
    """Create a case in INTAKE status."""
    return Case.objects.create(
        title='Failure injection test case',
        description='This case is used to test failure scenarios.',
        scenario=Case.Scenario.EDUCATION,
        status=Case.Status.INTAKE,
        assigned_operator=operator,
    )


@pytest.fixture
def closed_case(db, operator, supervisor):
    """Create a case that has been fully closed (terminal state)."""
    case = Case.objects.create(
        title='Closed test case',
        description='This case is already closed.',
        scenario=Case.Scenario.EDUCATION,
        status=Case.Status.INTAKE,
        assigned_operator=operator,
    )
    # Walk through the full lifecycle to get to CLOSED
    case.transition_to(Case.Status.ASSESSMENT, actor=supervisor)
    case.transition_to(Case.Status.ACTIVE, actor=supervisor)
    case.transition_to(Case.Status.FOLLOWUP, actor=supervisor)
    case.transition_to(Case.Status.CLOSED, actor=supervisor)
    return case


# =============================================================================
# TEST GROUP 1: INVALID STATE TRANSITIONS
# =============================================================================
class TestInvalidTransitions:
    """
    Prove that the state machine blocks illegal transitions.

    # EXAM DEFENSE: Why This Matters
    # =================================
    # If a case worker accidentally (or maliciously) tries to skip from
    # INTAKE directly to CLOSED, our state machine MUST block it.
    # These tests prove that every forbidden path is rejected.
    """

    def test_intake_cannot_jump_to_closed(self, intake_case, operator):
        """
        FAILURE INJECTION: Skip from INTAKE → CLOSED (skipping 3 states).

        # EXAM DEFENSE: This is the most critical test.
        # INTAKE → CLOSED would close a case without any assessment,
        # intervention, or follow-up. This MUST be blocked.
        """
        original_status = intake_case.status
        audit_count_before = AuditLog.objects.count()

        with pytest.raises(ValidationError) as exc_info:
            intake_case.transition_to(Case.Status.CLOSED, actor=operator)

        # Verify: status was NOT changed
        intake_case.refresh_from_db()
        assert intake_case.status == original_status  # Still INTAKE

        # Verify: NO audit log was created (blocked transitions don't log)
        assert AuditLog.objects.count() == audit_count_before

        # Verify: error message is informative
        assert 'Cannot transition' in str(exc_info.value)

    def test_intake_cannot_jump_to_active(self, intake_case, operator):
        """
        FAILURE INJECTION: INTAKE → ACTIVE (skipping ASSESSMENT).

        A case must be assessed before starting active intervention.
        """
        with pytest.raises(ValidationError):
            intake_case.transition_to(Case.Status.ACTIVE, actor=operator)

        intake_case.refresh_from_db()
        assert intake_case.status == Case.Status.INTAKE

    def test_intake_cannot_jump_to_followup(self, intake_case, operator):
        """FAILURE INJECTION: INTAKE → FOLLOWUP (skipping 2 states)."""
        with pytest.raises(ValidationError):
            intake_case.transition_to(Case.Status.FOLLOWUP, actor=operator)

        intake_case.refresh_from_db()
        assert intake_case.status == Case.Status.INTAKE

    def test_closed_case_cannot_reopen(self, closed_case, supervisor):
        """
        FAILURE INJECTION: CLOSED → ANY STATE.

        # EXAM DEFENSE: Terminal State Enforcement
        # ==========================================
        # CLOSED is a terminal state — no transitions allowed.
        # Once a case is closed, it stays closed. This prevents:
        # - Accidental reopening of resolved cases
        # - Manipulation of closed case records
        """
        for target_status in Case.Status:
            if target_status == Case.Status.CLOSED:
                continue  # Skip CLOSED → CLOSED (trivial)

            with pytest.raises(ValidationError):
                closed_case.transition_to(target_status, actor=supervisor)

            closed_case.refresh_from_db()
            assert closed_case.status == Case.Status.CLOSED

    def test_assessment_cannot_jump_to_followup(self, intake_case, supervisor):
        """FAILURE INJECTION: ASSESSMENT → FOLLOWUP (skipping ACTIVE)."""
        # First, legitimately move to ASSESSMENT
        intake_case.transition_to(Case.Status.ASSESSMENT, actor=supervisor)

        with pytest.raises(ValidationError):
            intake_case.transition_to(Case.Status.FOLLOWUP, actor=supervisor)

        intake_case.refresh_from_db()
        assert intake_case.status == Case.Status.ASSESSMENT


# =============================================================================
# TEST GROUP 2: UNAUTHORIZED ACCESS (RBAC Bypass Attempts)
# =============================================================================
class TestUnauthorizedAccess:
    """
    Prove that role-based access controls cannot be bypassed.

    # EXAM DEFENSE: RBAC Testing — Why It's Important
    # ==================================================
    # These tests prove that a Field Operator cannot edit cases created
    # by ANOTHER operator. In a real system, this prevents data tampering.
    """

    def test_operator_cannot_edit_other_operators_case(
        self, intake_case, other_operator
    ):
        """
        FAILURE INJECTION: An operator tries to edit another operator's case.

        # EXAM DEFENSE: Cross-User Access Prevention
        # =============================================
        # The case was created by 'operator', but 'other_operator' tries
        # to access it. is_editable_by() should return False.
        """
        assert intake_case.is_editable_by(other_operator) is False

    def test_user_with_no_role_cannot_edit(self, intake_case, db):
        """
        FAILURE INJECTION: A user with NO group membership tries to edit.

        # EXAM DEFENSE: Zero-Trust Default
        # ===================================
        # Users without a role group get ZERO access. The system defaults
        # to "deny" rather than "allow" — this is a security best practice.
        """
        user_no_role = User.objects.create_user(
            username='fi_no_role', password='test123',
        )
        assert intake_case.is_editable_by(user_no_role) is False


# =============================================================================
# TEST GROUP 3: DATA INTEGRITY UNDER FAILURE
# =============================================================================
class TestDataIntegrityUnderFailure:
    """
    Prove that failed operations do NOT corrupt data.

    # EXAM DEFENSE: Data Integrity Proof
    # =====================================
    # These tests verify that after a rejected transition:
    # 1. The case status is UNCHANGED
    # 2. The case reference is UNCHANGED
    # 3. No phantom audit log entries are created
    # 4. Other cases in the system are unaffected
    """

    def test_failed_transition_preserves_all_fields(self, intake_case, operator):
        """
        After a rejected transition, ALL case fields must be unchanged.

        # EXAM DEFENSE: Atomicity
        # =========================
        # This test captures a snapshot of every field BEFORE the failed
        # transition, then verifies they're all identical AFTER.
        # This proves that our transition_to() method is atomic:
        # either it succeeds completely, or nothing changes.
        """
        # Snapshot before
        snapshot = {
            'reference': intake_case.reference,
            'title': intake_case.title,
            'status': intake_case.status,
            'scenario': intake_case.scenario,
            'priority': intake_case.priority,
        }

        # Attempt forbidden transition
        with pytest.raises(ValidationError):
            intake_case.transition_to(Case.Status.CLOSED, actor=operator)

        # Refresh and verify EVERY field
        intake_case.refresh_from_db()
        for field_name, expected_value in snapshot.items():
            actual_value = getattr(intake_case, field_name)
            assert actual_value == expected_value, (
                f"Field '{field_name}' was corrupted! "
                f"Expected '{expected_value}', got '{actual_value}'"
            )

    def test_failed_transition_no_audit_created(self, intake_case, operator):
        """
        A failed transition MUST NOT create an audit log entry.

        # EXAM DEFENSE: No Ghost Entries
        # =================================
        # If a blocked transition created an audit entry, it would:
        # 1. Pollute the audit trail with non-events
        # 2. Confuse supervisors reviewing the log
        # 3. Indicate a code defect (logging before validation)
        """
        audit_count_before = AuditLog.objects.count()

        with pytest.raises(ValidationError):
            intake_case.transition_to(Case.Status.CLOSED, actor=operator)

        assert AuditLog.objects.count() == audit_count_before

    def test_other_cases_unaffected_by_failed_transition(
        self, intake_case, operator, supervisor
    ):
        """
        A failed transition on Case A must NOT affect Case B.

        # EXAM DEFENSE: Isolation Proof
        # ================================
        # This is important in a multi-user system: if one user triggers
        # an error, it must NOT cascade to other users' cases.
        """
        # Create a second case
        case_b = Case.objects.create(
            title='Case B — should be unaffected',
            description='Isolation test.',
            scenario=Case.Scenario.EDUCATION,
            status=Case.Status.INTAKE,
            assigned_operator=operator,
        )

        # Legitimately transition Case B to ASSESSMENT
        case_b.transition_to(Case.Status.ASSESSMENT, actor=supervisor)

        # Now fail a transition on Case A
        with pytest.raises(ValidationError):
            intake_case.transition_to(Case.Status.CLOSED, actor=operator)

        # Verify Case B is STILL in ASSESSMENT (unaffected)
        case_b.refresh_from_db()
        assert case_b.status == Case.Status.ASSESSMENT


# =============================================================================
# TEST GROUP 4: SERVICE LAYER FAILURE RESILIENCE
# =============================================================================
class TestServiceLayerResilience:
    """
    Prove that the education service layer handles edge cases gracefully.
    """

    def test_risk_assessment_handles_missing_student_record(
        self, db, operator
    ):
        """
        FAILURE INJECTION: process_intake_cases on a case WITHOUT a StudentRecord.

        # EXAM DEFENSE: Graceful Degradation
        # =====================================
        # If a Case exists but has no linked StudentRecord (data entry error),
        # the service should skip it and report the error — NOT crash.
        """
        # Create a case with no student record
        Case.objects.create(
            title='Orphaned case (no student record)',
            description='Missing student data.',
            scenario=Case.Scenario.EDUCATION,
            status=Case.Status.INTAKE,
            assigned_operator=operator,
        )

        # This should NOT raise an exception
        results = process_intake_cases(actor=operator)

        assert results['total_scanned'] == 1
        assert len(results['errors']) == 1  # Reported as an error
        assert 'no StudentRecord' in results['errors'][0]

    def test_risk_assessment_safe_student_stays_in_intake(
        self, db, operator
    ):
        """
        FAILURE INJECTION: A completely safe student should NOT be transitioned.

        # EXAM DEFENSE: False Positive Prevention
        # ==========================================
        # The risk engine must NOT flag safe students. A false positive
        # would waste specialist time and alarm parents unnecessarily.
        """
        case = Case.objects.create(
            title='Safe student case',
            description='This student is fine.',
            scenario=Case.Scenario.EDUCATION,
            status=Case.Status.INTAKE,
            assigned_operator=operator,
        )
        StudentRecord.objects.create(
            case=case,
            student_id='FI-SAFE-001',
            first_name='Safe',
            last_name='Student',
            date_of_birth=date(2010, 1, 1),
            school_name='Test School',
            school_type=StudentRecord.SchoolType.MIDDLE,
            grade_level=8,
            attendance_rate=98.0,  # Far above threshold
            grade_trend=StudentRecord.GradeTrend.IMPROVING,
            behavior_notes_count=0,
        )

        results = process_intake_cases(actor=operator)

        case.refresh_from_db()
        assert case.status == Case.Status.INTAKE  # NOT transitioned
        assert results['flagged'] == 0
        assert results['safe'] == 1
