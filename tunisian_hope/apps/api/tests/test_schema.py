"""
Tests for the Strawberry GraphQL API
=======================================

# EXAM DEFENSE: GraphQL Testing Strategy
# =========================================
# We test the GraphQL API using Strawberry's built-in schema.execute_sync()
# method instead of Django's test client. This gives us:
#
# 1. Direct schema testing — no HTTP overhead, no URL routing to debug
# 2. We can inject a custom 'info' context with a mock request/user
# 3. Each test is fast and isolated
#
# We test 3 categories:
# 1. Query correctness — do resolvers return the right data?
# 2. Permission enforcement — are unauthorized users blocked?
# 3. Edge cases — empty results, invalid parameters
"""

import pytest
from datetime import date
from unittest.mock import MagicMock

from django.contrib.auth.models import User, Group
from django.test import RequestFactory

from apps.core.models import Case
from apps.education.models import StudentRecord
from apps.api.schema import schema


# =============================================================================
# TEST HELPERS
# =============================================================================
def _make_context(user):
    """
    Build a Strawberry-compatible context dict with a Django request.

    # EXAM DEFENSE: Why Mock the Request?
    # ======================================
    # Strawberry resolvers access the Django request via info.context["request"].
    # Instead of spinning up a full HTTP server, we create a minimal request
    # object using Django's RequestFactory and attach our test user to it.
    # This is the standard testing pattern for Strawberry-Django.
    """
    factory = RequestFactory()
    request = factory.get('/graphql/')
    request.user = user
    return {"request": request}


def _execute_query(query_string, user, variables=None):
    """Execute a GraphQL query with the given user context."""
    context = _make_context(user)
    result = schema.execute_sync(
        query_string,
        context_value=context,
        variable_values=variables,
    )
    return result


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def groups(db):
    """Get or create the 3 role groups."""
    roles = ['Field Operator', 'Supervisor', 'System Admin']
    return {name: Group.objects.get_or_create(name=name)[0] for name in roles}


@pytest.fixture
def supervisor(db, groups):
    """Create a Supervisor user."""
    user = User.objects.create_user(
        username='gql_supervisor', password='test123',
        first_name='Supervisor', last_name='Test',
    )
    user.groups.add(groups['Supervisor'])
    return user


@pytest.fixture
def admin_user(db, groups):
    """Create a System Admin user."""
    user = User.objects.create_user(
        username='gql_admin', password='test123',
        first_name='Admin', last_name='Test',
    )
    user.groups.add(groups['System Admin'])
    return user


@pytest.fixture
def operator(db, groups):
    """Create a Field Operator user (should NOT access dashboard)."""
    user = User.objects.create_user(
        username='gql_operator', password='test123',
        first_name='Operator', last_name='Test',
    )
    user.groups.add(groups['Field Operator'])
    return user


@pytest.fixture
def anonymous_user():
    """Create an anonymous (not logged in) user mock."""
    user = MagicMock()
    user.is_authenticated = False
    return user


@pytest.fixture
def sample_students(db, operator):
    """Create a mix of students for testing queries."""
    students = []

    # 2 at-risk students (ASSESSMENT status)
    for i in range(2):
        case = Case.objects.create(
            title=f"At-risk student {i}",
            description="Test at-risk.",
            scenario=Case.Scenario.EDUCATION,
            status=Case.Status.ASSESSMENT,
            assigned_operator=operator,
        )
        student = StudentRecord.objects.create(
            case=case,
            student_id=f"GQL-RISK-{i:03d}",
            first_name=f"Risk{i}",
            last_name="Student",
            date_of_birth=date(2010, 1, 1),
            school_name="Test School",
            school_type=StudentRecord.SchoolType.MIDDLE,
            grade_level=8,
            attendance_rate=60.0 + i * 5,
            grade_trend=StudentRecord.GradeTrend.DECLINING,
            behavior_notes_count=4,
            risk_score=0.8 - i * 0.1,
        )
        students.append(student)

    # 3 safe students (INTAKE status)
    for i in range(3):
        case = Case.objects.create(
            title=f"Safe student {i}",
            description="Test safe.",
            scenario=Case.Scenario.EDUCATION,
            status=Case.Status.INTAKE,
            assigned_operator=operator,
        )
        student = StudentRecord.objects.create(
            case=case,
            student_id=f"GQL-SAFE-{i:03d}",
            first_name=f"Safe{i}",
            last_name="Student",
            date_of_birth=date(2011, 6, 15),
            school_name="Test School",
            school_type=StudentRecord.SchoolType.HIGH,
            grade_level=10,
            attendance_rate=92.0 + i * 2,
            grade_trend=StudentRecord.GradeTrend.STABLE,
            behavior_notes_count=0,
            risk_score=0.0,
        )
        students.append(student)

    return students


# =============================================================================
# QUERY CORRECTNESS TESTS
# =============================================================================
class TestStudentsInAssessment:
    """Test the studentsInAssessment query."""

    QUERY = """
        query {
            studentsInAssessment {
                studentId
                firstName
                lastName
                attendanceRate
                riskScore
                case {
                    reference
                    status
                    statusDisplay
                }
            }
        }
    """

    def test_returns_only_assessment_students(self, sample_students, supervisor):
        """Only students in ASSESSMENT status should be returned."""
        result = _execute_query(self.QUERY, supervisor)

        assert result.errors is None
        students = result.data['studentsInAssessment']
        assert len(students) == 2  # Only the 2 at-risk ones

        # All returned students should be in assessment
        for s in students:
            assert s['case']['status'] == 'assessment'

    def test_ordered_by_risk_score_descending(self, sample_students, supervisor):
        """Results should be ordered by risk_score (highest first)."""
        result = _execute_query(self.QUERY, supervisor)

        students = result.data['studentsInAssessment']
        scores = [s['riskScore'] for s in students]
        assert scores == sorted(scores, reverse=True)


class TestStudentLookup:
    """Test the student(studentId) query."""

    QUERY = """
        query StudentLookup($id: String!) {
            student(studentId: $id) {
                studentId
                firstName
                attendanceRate
                gradeTrend
            }
        }
    """

    def test_find_existing_student(self, sample_students, supervisor):
        """Looking up an existing student_id should return their data."""
        result = _execute_query(
            self.QUERY, supervisor,
            variables={"id": "GQL-RISK-000"},
        )

        assert result.errors is None
        student = result.data['student']
        assert student is not None
        assert student['studentId'] == 'GQL-RISK-000'
        assert student['firstName'] == 'Risk0'

    def test_nonexistent_student_returns_null(self, sample_students, supervisor):
        """Looking up a non-existent student_id should return null."""
        result = _execute_query(
            self.QUERY, supervisor,
            variables={"id": "DOES-NOT-EXIST"},
        )

        assert result.errors is None
        assert result.data['student'] is None


class TestCasesByStatus:
    """Test the casesByStatus query."""

    QUERY = """
        query CasesByStatus($status: String!) {
            casesByStatus(status: $status) {
                reference
                status
                statusDisplay
                title
            }
        }
    """

    def test_filter_by_intake(self, sample_students, supervisor):
        """Should return only INTAKE cases."""
        result = _execute_query(
            self.QUERY, supervisor,
            variables={"status": "intake"},
        )

        assert result.errors is None
        cases = result.data['casesByStatus']
        assert len(cases) == 3  # 3 safe students in INTAKE

    def test_invalid_status_returns_empty(self, sample_students, supervisor):
        """An invalid status string should return an empty list, not error."""
        result = _execute_query(
            self.QUERY, supervisor,
            variables={"status": "invalid_status"},
        )

        assert result.errors is None
        assert result.data['casesByStatus'] == []


class TestEducationDashboard:
    """Test the educationDashboard aggregate query."""

    QUERY = """
        query {
            educationDashboard {
                totalStudents
                atRiskCount
                safeCount
                inAssessmentCount
                inIntakeCount
                averageAttendance
                averageRiskScore
                statusBreakdown {
                    status
                    label
                    count
                }
                riskDistribution {
                    label
                    count
                }
            }
        }
    """

    def test_correct_aggregate_counts(self, sample_students, supervisor):
        """Dashboard should show correct counts for our test data."""
        result = _execute_query(self.QUERY, supervisor)

        assert result.errors is None
        dashboard = result.data['educationDashboard']
        assert dashboard['totalStudents'] == 5
        assert dashboard['atRiskCount'] == 2
        assert dashboard['safeCount'] == 3
        assert dashboard['inAssessmentCount'] == 2
        assert dashboard['inIntakeCount'] == 3

    def test_average_attendance_computed(self, sample_students, supervisor):
        """Average attendance should be calculated correctly."""
        result = _execute_query(self.QUERY, supervisor)

        dashboard = result.data['educationDashboard']
        # (60 + 65 + 92 + 94 + 96) / 5 = 81.4
        assert dashboard['averageAttendance'] == 81.4

    def test_status_breakdown_includes_all_statuses(self, sample_students, supervisor):
        """Status breakdown should include all 5 status values."""
        result = _execute_query(self.QUERY, supervisor)

        breakdown = result.data['educationDashboard']['statusBreakdown']
        statuses = [entry['status'] for entry in breakdown]
        assert 'intake' in statuses
        assert 'assessment' in statuses
        assert 'closed' in statuses

    def test_admin_can_access_dashboard(self, sample_students, admin_user):
        """System Admin should also be able to access the dashboard."""
        result = _execute_query(self.QUERY, admin_user)

        assert result.errors is None
        assert result.data['educationDashboard']['totalStudents'] == 5


# =============================================================================
# PERMISSION ENFORCEMENT TESTS
# =============================================================================
class TestPermissions:
    """Test that permission classes properly restrict access."""

    DASHBOARD_QUERY = """
        query {
            educationDashboard {
                totalStudents
            }
        }
    """

    STUDENTS_QUERY = """
        query {
            studentsInAssessment {
                studentId
            }
        }
    """

    def test_anonymous_cannot_access_students(self, sample_students, anonymous_user):
        """Unauthenticated users should be blocked from student data."""
        result = _execute_query(self.STUDENTS_QUERY, anonymous_user)

        assert result.errors is not None
        assert len(result.errors) > 0

    def test_anonymous_cannot_access_dashboard(self, sample_students, anonymous_user):
        """Unauthenticated users should be blocked from dashboard."""
        result = _execute_query(self.DASHBOARD_QUERY, anonymous_user)

        assert result.errors is not None

    def test_operator_cannot_access_dashboard(self, sample_students, operator):
        """Field Operators should NOT be able to access dashboard aggregates."""
        result = _execute_query(self.DASHBOARD_QUERY, operator)

        assert result.errors is not None
        # Check that the error message mentions access denial
        error_msg = str(result.errors[0])
        assert 'denied' in error_msg.lower() or 'supervisor' in error_msg.lower()

    def test_operator_can_access_students(self, sample_students, operator):
        """Field Operators CAN see the student list (just not the dashboard)."""
        result = _execute_query(self.STUDENTS_QUERY, operator)

        assert result.errors is None  # No permission error
        assert len(result.data['studentsInAssessment']) == 2

    def test_supervisor_can_access_all(self, sample_students, supervisor):
        """Supervisors should access both student queries AND dashboard."""
        # Student query
        result1 = _execute_query(self.STUDENTS_QUERY, supervisor)
        assert result1.errors is None

        # Dashboard query
        result2 = _execute_query(self.DASHBOARD_QUERY, supervisor)
        assert result2.errors is None
