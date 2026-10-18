"""
Core Model Tests — State Machine, UserProfile, and AuditLog
==============================================================

# EXAM DEFENSE: Testing Strategy
# =================================
# We use pytest + pytest-django instead of Django's default unittest because:
# 1. Tests are shorter (plain 'assert' instead of 'self.assertEqual')
# 2. Error messages are more informative (shows actual vs expected values)
# 3. Fixtures use dependency injection (cleaner setup/teardown)
# 4. Parametrize lets us test multiple inputs with one function
#
# We use @pytest.mark.django_db to tell pytest-django to create a
# test database for each test. Without it, database access raises an error.
#
# These tests cover rubric criteria:
# - D1 (Correctness): State machine transitions work correctly
# - D3 (Testing strategy): Unit tests with clear assertions
# - E1 (Security): Blocked transitions are enforced
"""

import pytest
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError

from apps.core.models import Case, UserProfile, AuditLog, ROLES


# =============================================================================
# FIXTURES — Reusable test setup
# =============================================================================
# EXAM DEFENSE: Pytest Fixtures
# ===============================
# Fixtures are functions that create test data. When a test function lists
# a fixture name as a parameter, pytest automatically calls the fixture
# and passes the result. This avoids repeating setup code in every test.

@pytest.fixture
def setup_groups(db):
    """
    Get or create the 4 role groups.
    The 'db' fixture enables database access.
    Note: Groups may already exist from our post_migrate signal.
    """
    groups = {}
    for role_name in ROLES:
        groups[role_name], _ = Group.objects.get_or_create(name=role_name)
    return groups


@pytest.fixture
def operator_user(setup_groups):
    """Create a test user with the Field Operator role."""
    user = User.objects.create_user(
        username='test_operator',
        password='testpass123',
        first_name='Test',
        last_name='Operator',
    )
    user.groups.add(setup_groups['Field Operator'])
    UserProfile.objects.create(user=user, region='tunis')
    return user


@pytest.fixture
def supervisor_user(setup_groups):
    """Create a test user with the Supervisor role."""
    user = User.objects.create_user(
        username='test_supervisor',
        password='testpass123',
    )
    user.groups.add(setup_groups['Supervisor'])
    UserProfile.objects.create(user=user, region='ariana')
    return user


@pytest.fixture
def sample_case(operator_user):
    """Create a sample Case in INTAKE status."""
    return Case.objects.create(
        title='Test student showing signs of disengagement',
        description='Attendance dropping, grade trend declining.',
        scenario=Case.Scenario.EDUCATION,
        status=Case.Status.INTAKE,
        priority=Case.Priority.MEDIUM,
        assigned_operator=operator_user,
    )


# =============================================================================
# USER PROFILE TESTS
# =============================================================================
class TestUserProfile:
    """Tests for the UserProfile model."""

    @pytest.mark.django_db
    def test_profile_creation(self, operator_user):
        """Verify that a UserProfile is correctly linked to a User."""
        profile = operator_user.profile  # Access via related_name
        assert profile is not None
        assert profile.region == 'tunis'
        assert profile.role_name == 'Field Operator'

    @pytest.mark.django_db
    def test_profile_str_representation(self, operator_user):
        """Verify the __str__ method returns 'Full Name — Region'."""
        profile = operator_user.profile
        expected = 'Test Operator — Tunis'
        assert str(profile) == expected

    @pytest.mark.django_db
    def test_profile_role_name_no_group(self, db):
        """A user with no group should show 'No Role Assigned'."""
        user = User.objects.create_user(username='no_role', password='test123')
        profile = UserProfile.objects.create(user=user)
        assert profile.role_name == 'No Role Assigned'


# =============================================================================
# CASE MODEL TESTS
# =============================================================================
class TestCaseModel:
    """Tests for Case creation and field defaults."""

    @pytest.mark.django_db
    def test_case_auto_reference(self, sample_case):
        """Verify that a case reference is auto-generated on save."""
        assert sample_case.reference.startswith('CASE-')
        assert len(sample_case.reference) > 0

    @pytest.mark.django_db
    def test_case_default_status(self, operator_user):
        """New cases should default to INTAKE status."""
        case = Case.objects.create(
            title='Default status test',
            description='Testing default status.',
            scenario=Case.Scenario.HEALTH,
            assigned_operator=operator_user,
        )
        assert case.status == Case.Status.INTAKE

    @pytest.mark.django_db
    def test_case_str_representation(self, sample_case):
        """Verify the __str__ method includes reference, title, and status."""
        result = str(sample_case)
        assert sample_case.reference in result
        assert 'Intake' in result


# =============================================================================
# STATE MACHINE TESTS — The most critical tests
# =============================================================================
class TestStateMachine:
    """
    Tests for the Case state machine transitions.

    # EXAM DEFENSE: These tests prove our state machine works correctly.
    # We test BOTH valid transitions (should succeed) and invalid ones
    # (should raise ValidationError). Testing the "unhappy path" is
    # what separates a good test suite from a superficial one.
    """

    @pytest.mark.django_db
    def test_valid_transition_intake_to_assessment(self, sample_case, operator_user):
        """INTAKE → ASSESSMENT should succeed (the normal first step)."""
        sample_case.transition_to(Case.Status.ASSESSMENT, actor=operator_user)
        sample_case.refresh_from_db()
        assert sample_case.status == Case.Status.ASSESSMENT

    @pytest.mark.django_db
    def test_valid_transition_assessment_to_active(self, sample_case, operator_user):
        """ASSESSMENT → ACTIVE should succeed."""
        sample_case.transition_to(Case.Status.ASSESSMENT, actor=operator_user)
        sample_case.transition_to(Case.Status.ACTIVE, actor=operator_user)
        sample_case.refresh_from_db()
        assert sample_case.status == Case.Status.ACTIVE

    @pytest.mark.django_db
    def test_valid_transition_full_lifecycle(self, sample_case, operator_user):
        """Test the complete happy path: INTAKE → ASSESSMENT → ACTIVE → FOLLOWUP → CLOSED."""
        sample_case.transition_to(Case.Status.ASSESSMENT, actor=operator_user)
        sample_case.transition_to(Case.Status.ACTIVE, actor=operator_user)
        sample_case.transition_to(Case.Status.FOLLOWUP, actor=operator_user)
        sample_case.transition_to(Case.Status.CLOSED, actor=operator_user)
        sample_case.refresh_from_db()
        assert sample_case.status == Case.Status.CLOSED

    @pytest.mark.django_db
    def test_blocked_transition_intake_to_active(self, sample_case, operator_user):
        """INTAKE → ACTIVE should be BLOCKED (must go through ASSESSMENT first)."""
        with pytest.raises(ValidationError) as exc_info:
            sample_case.transition_to(Case.Status.ACTIVE, actor=operator_user)

        # Verify the error message is informative
        assert 'Cannot transition' in str(exc_info.value)

    @pytest.mark.django_db
    def test_blocked_transition_intake_to_closed(self, sample_case, operator_user):
        """INTAKE → CLOSED should be BLOCKED (can't skip the entire workflow)."""
        with pytest.raises(ValidationError):
            sample_case.transition_to(Case.Status.CLOSED, actor=operator_user)

    @pytest.mark.django_db
    def test_blocked_transition_closed_to_anything(self, sample_case, operator_user):
        """CLOSED → anything should be BLOCKED (terminal state)."""
        # Move to closed via the full path
        sample_case.transition_to(Case.Status.ASSESSMENT, actor=operator_user)
        sample_case.transition_to(Case.Status.ACTIVE, actor=operator_user)
        sample_case.transition_to(Case.Status.FOLLOWUP, actor=operator_user)
        sample_case.transition_to(Case.Status.CLOSED, actor=operator_user)

        # Now try to reopen — should fail
        with pytest.raises(ValidationError):
            sample_case.transition_to(Case.Status.INTAKE, actor=operator_user)

    @pytest.mark.django_db
    def test_valid_backward_transition_assessment_to_intake(self, sample_case, operator_user):
        """ASSESSMENT → INTAKE should succeed (return for more info)."""
        sample_case.transition_to(Case.Status.ASSESSMENT, actor=operator_user)
        sample_case.transition_to(Case.Status.INTAKE, actor=operator_user)
        sample_case.refresh_from_db()
        assert sample_case.status == Case.Status.INTAKE

    @pytest.mark.django_db
    def test_get_allowed_transitions(self, sample_case):
        """Verify get_allowed_transitions returns correct list for INTAKE."""
        allowed = sample_case.get_allowed_transitions()
        assert allowed == [Case.Status.ASSESSMENT]

    @pytest.mark.django_db
    def test_get_allowed_transitions_closed(self, sample_case, operator_user):
        """CLOSED state should have NO allowed transitions."""
        # Move to closed
        sample_case.transition_to(Case.Status.ASSESSMENT, actor=operator_user)
        sample_case.transition_to(Case.Status.ACTIVE, actor=operator_user)
        sample_case.transition_to(Case.Status.FOLLOWUP, actor=operator_user)
        sample_case.transition_to(Case.Status.CLOSED, actor=operator_user)

        allowed = sample_case.get_allowed_transitions()
        assert allowed == []


# =============================================================================
# AUDIT LOG TESTS
# =============================================================================
class TestAuditLog:
    """Tests for audit log creation during state transitions."""

    @pytest.mark.django_db
    def test_transition_creates_audit_log(self, sample_case, operator_user):
        """Each state transition should create exactly one AuditLog entry."""
        initial_count = AuditLog.objects.count()
        sample_case.transition_to(Case.Status.ASSESSMENT, actor=operator_user)
        assert AuditLog.objects.count() == initial_count + 1

    @pytest.mark.django_db
    def test_audit_log_content(self, sample_case, operator_user):
        """Verify the AuditLog entry contains correct old/new values."""
        sample_case.transition_to(Case.Status.ASSESSMENT, actor=operator_user)

        log = AuditLog.objects.latest('timestamp')
        assert log.actor == operator_user
        assert log.action == AuditLog.Action.TRANSITION
        assert log.target_model == 'Case'
        assert log.target_id == sample_case.pk
        assert log.old_value == {'status': 'intake'}
        assert log.new_value == {'status': 'assessment'}

    @pytest.mark.django_db
    def test_blocked_transition_no_audit_log(self, sample_case, operator_user):
        """A blocked transition should NOT create an AuditLog entry."""
        initial_count = AuditLog.objects.count()
        with pytest.raises(ValidationError):
            sample_case.transition_to(Case.Status.CLOSED, actor=operator_user)
        # Count should not have changed
        assert AuditLog.objects.count() == initial_count

    @pytest.mark.django_db
    def test_full_lifecycle_audit_trail(self, sample_case, operator_user):
        """A full lifecycle should create exactly 4 audit log entries."""
        sample_case.transition_to(Case.Status.ASSESSMENT, actor=operator_user)
        sample_case.transition_to(Case.Status.ACTIVE, actor=operator_user)
        sample_case.transition_to(Case.Status.FOLLOWUP, actor=operator_user)
        sample_case.transition_to(Case.Status.CLOSED, actor=operator_user)

        logs = AuditLog.objects.filter(
            target_model='Case',
            target_id=sample_case.pk,
        )
        assert logs.count() == 4
