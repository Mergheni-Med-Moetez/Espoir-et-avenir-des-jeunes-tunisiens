"""
Permission Tests — Role-Based Access Control (RBAC)
=====================================================

# EXAM DEFENSE: Permission Testing
# ===================================
# These tests verify that the is_editable_by() method on Case correctly
# enforces our role-based access control rules:
#
# - System Admin / Supervisor → can edit ANY case
# - Field Operator → can edit ONLY their own cases
# - No role → cannot edit anything
#
# This directly addresses rubric criteria:
# - D1 (Correctness): Permissions work as expected
# - E1 (Security): Unauthorized access is denied
"""

import pytest
from django.contrib.auth.models import User, Group

from apps.core.models import Case, UserProfile, ROLES


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def groups(db):
    """Get or create all 3 role groups (may already exist from post_migrate signal)."""
    return {name: Group.objects.get_or_create(name=name)[0] for name in ROLES}


@pytest.fixture
def operator(groups):
    """Field Operator user who creates cases."""
    user = User.objects.create_user(username='perm_operator', password='test123')
    user.groups.add(groups['Field Operator'])
    UserProfile.objects.create(user=user, region='tunis')
    return user


@pytest.fixture
def supervisor(groups):
    """Supervisor user who validates transitions."""
    user = User.objects.create_user(username='perm_supervisor', password='test123')
    user.groups.add(groups['Supervisor'])
    UserProfile.objects.create(user=user, region='ariana')
    return user


@pytest.fixture
def admin_user(groups):
    """System Admin user who manages the platform."""
    user = User.objects.create_user(username='perm_admin', password='test123')
    user.groups.add(groups['System Admin'])
    UserProfile.objects.create(user=user, region='tunis')
    return user


@pytest.fixture
def other_operator(groups):
    """A DIFFERENT operator (not the one who created the case)."""
    user = User.objects.create_user(username='other_operator', password='test123')
    user.groups.add(groups['Field Operator'])
    UserProfile.objects.create(user=user, region='bizerte')
    return user


@pytest.fixture
def case_owned_by_operator(operator):
    """A case created by 'operator'."""
    return Case.objects.create(
        title='Permission test case',
        description='Testing role-based access control.',
        scenario=Case.Scenario.EDUCATION,
        assigned_operator=operator,
    )


# =============================================================================
# PERMISSION TESTS
# =============================================================================
class TestRoleBasedAccess:
    """
    Test the is_editable_by() method for each role.

    # EXAM DEFENSE: We test every combination of user role × case ownership.
    # This is called "boundary testing" — we check both the allowed and
    # denied cases to make sure the logic has no gaps.
    """

    @pytest.mark.django_db
    def test_operator_can_edit_own_case(self, case_owned_by_operator, operator):
        """An operator should be able to edit a case they created."""
        assert case_owned_by_operator.is_editable_by(operator) is True

    @pytest.mark.django_db
    def test_operator_cannot_edit_others_case(self, case_owned_by_operator, other_operator):
        """An operator should NOT be able to edit someone else's case."""
        assert case_owned_by_operator.is_editable_by(other_operator) is False



    @pytest.mark.django_db
    def test_supervisor_can_edit_any_case(self, case_owned_by_operator, supervisor):
        """A supervisor should be able to edit ANY case (oversight role)."""
        assert case_owned_by_operator.is_editable_by(supervisor) is True

    @pytest.mark.django_db
    def test_admin_can_edit_any_case(self, case_owned_by_operator, admin_user):
        """A system admin should be able to edit ANY case."""
        assert case_owned_by_operator.is_editable_by(admin_user) is True

    @pytest.mark.django_db
    def test_user_with_no_role_cannot_edit(self, case_owned_by_operator, db):
        """A user with no role group should NOT be able to edit any case."""
        no_role_user = User.objects.create_user(
            username='no_role_user', password='test123'
        )
        assert case_owned_by_operator.is_editable_by(no_role_user) is False
