"""
Strawberry GraphQL Types — Data Transfer Objects for the API
==============================================================

# EXAM DEFENSE: Why Explicit Strawberry Types (Not Auto-Generated)?
# ====================================================================
# Strawberry-django can auto-generate types from Django models using
# @strawberry_django.type(Model). This is convenient, but for our exam:
#
# 1. We define types MANUALLY so every field is visible and explainable
# 2. No "magic" that the professor can't trace through the code
# 3. We control exactly which fields are exposed (security: never leak
#    internal fields like password hashes or raw PKs unintentionally)
# 4. Shows we understand the GraphQL type system, not just a code generator
#
# Strawberry uses Python 3.11+ type hints (PEP 484) as the schema definition
# language. Each @strawberry.type class becomes a GraphQL object type:
#
#   Python:  name: str           →  GraphQL:  name: String!
#   Python:  risk_score: float | None  →  GraphQL:  riskScore: Float
#
# The | None syntax (PEP 604, Python 3.10+) marks nullable fields.
# Strawberry auto-converts snake_case to camelCase in the GraphQL schema.
"""

from __future__ import annotations

import strawberry
from typing import Optional


# =============================================================================
# CASE TYPE — Workflow data exposed to the GraphQL API
# =============================================================================
@strawberry.type
class CaseType:
    """
    GraphQL representation of a Case record.

    # EXAM DEFENSE: Field Selection
    # ===============================
    # We expose workflow fields (reference, status, priority, timestamps)
    # but NOT internal database fields (raw pk, ForeignKey IDs).
    # This is a security best practice: the API consumer sees only
    # what they need, not the database internals.
    """
    reference: str
    title: str
    status: str
    status_display: str
    scenario: str
    priority: str
    priority_display: str
    operator_name: str | None
    created_at: str
    updated_at: str


# =============================================================================
# STUDENT RECORD TYPE — Education-specific data
# =============================================================================
@strawberry.type
class StudentRecordType:
    """
    GraphQL representation of a StudentRecord with its linked Case.

    # EXAM DEFENSE: Nested Types
    # ============================
    # The 'case' field is a nested CaseType. In GraphQL, the frontend can
    # request only the fields it needs:
    #
    #   query {
    #     studentsInAssessment {
    #       studentId
    #       attendanceRate
    #       case { status reference }   ← only 2 Case fields, not all
    #     }
    #   }
    #
    # This is the key advantage over REST: no over-fetching.
    # A REST endpoint would return ALL Case fields every time.
    """
    student_id: str
    first_name: str
    last_name: str
    school_name: str
    school_type: str
    grade_level: int
    attendance_rate: float
    grade_trend: str
    behavior_notes_count: int
    risk_score: float | None
    risk_factors: list[str]
    last_assessed_at: str | None
    case: CaseType


# =============================================================================
# DASHBOARD AGGREGATE TYPES — KPI data for the Education dashboard
# =============================================================================
@strawberry.type
class StatusCount:
    """
    Count of cases grouped by workflow status.

    # EXAM DEFENSE: This type powers the dashboard bar chart.
    # e.g., { status: "assessment", label: "Assessment", count: 30 }
    """
    status: str
    label: str
    count: int


@strawberry.type
class RiskBucket:
    """
    Distribution of students by risk score range.

    # EXAM DEFENSE: This type powers the risk distribution pie chart.
    # e.g., { label: "High Risk (0.7-1.0)", count: 12 }
    """
    label: str
    min_score: float
    max_score: float
    count: int


@strawberry.type
class EducationDashboardType:
    """
    Aggregate dashboard data for the Education Early Warning scenario.

    # EXAM DEFENSE: Dashboard Type — Why Aggregate in the Backend?
    # ==============================================================
    # We compute aggregates (counts, averages) on the SERVER, not the client.
    # This is better because:
    # 1. PostgreSQL is faster at COUNT/AVG than JavaScript in the browser
    # 2. We don't send 50+ raw records over the network just to count them
    # 3. The dashboard loads in one GraphQL query, not multiple REST calls
    #
    # GraphQL query example:
    #   query {
    #     educationDashboard {
    #       totalStudents
    #       atRiskCount
    #       averageAttendance
    #       statusBreakdown { status count }
    #     }
    #   }
    """
    total_students: int
    at_risk_count: int
    safe_count: int
    in_assessment_count: int
    in_intake_count: int
    average_attendance: float
    average_risk_score: float
    status_breakdown: list[StatusCount]
    risk_distribution: list[RiskBucket]
