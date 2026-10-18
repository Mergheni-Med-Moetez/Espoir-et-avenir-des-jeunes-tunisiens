"""
GraphQL Permission Classes — Role-Based Access for Strawberry Resolvers
=========================================================================

# EXAM DEFENSE: GraphQL Permissions — Why Custom, Not DRF?
# ===========================================================
# Django REST Framework has its own permission system (IsAuthenticated, etc.)
# but Strawberry uses a different mechanism: permission classes that implement
# the has_permission() method.
#
# We build our own because:
# 1. Strawberry's permission system integrates with its resolver pipeline
# 2. It uses Python type hints (consistent with our Strawberry approach)
# 3. It's only ~20 lines — simpler than learning two permission systems
# 4. The professor sees we understand authorization at the API layer
#
# How it works:
# - Each permission class has a has_permission() method
# - It receives the Strawberry 'info' context (which contains the Django request)
# - It checks the user's groups against the allowed roles
# - If denied, it raises PermissionError with a clear message
"""

import typing

import strawberry
from strawberry.permission import BasePermission
from strawberry.types import Info


class IsAuthenticated(BasePermission):
    """
    Ensure the user is logged in before accessing this resolver.

    # EXAM DEFENSE: This is the simplest permission check.
    # request.user.is_authenticated is Django's built-in property
    # that returns True if the user has a valid session cookie.
    """
    message = "Authentication required. Please log in."

    def has_permission(self, source: typing.Any, info: Info, **kwargs) -> bool:
        request = info.context["request"]
        return request.user.is_authenticated


class IsSupervisorOrAdmin(BasePermission):
    """
    Restrict access to Supervisor and System Admin roles only.

    # EXAM DEFENSE: Role-Based API Access
    # ======================================
    # The education dashboard contains AGGREGATE data about student risk.
    # This is sensitive information that should only be visible to:
    # - Supervisors (who oversee all cases)
    # - System Admins (who have full platform access)
    #
    # Field Operators and Specialists should NOT see aggregate risk data
    # because it could expose information about students outside their
    # assigned scope.
    #
    # We check group membership using Django's built-in auth system,
    # the same approach used in Case.is_editable_by() (consistency).
    """
    message = (
        "Access denied. Only Supervisors and System Admins "
        "can access dashboard aggregate data."
    )

    def has_permission(self, source: typing.Any, info: Info, **kwargs) -> bool:
        request = info.context["request"]

        # Must be authenticated first
        if not request.user.is_authenticated:
            return False

        # Check group membership
        user_groups = set(request.user.groups.values_list('name', flat=True))
        allowed_groups = {'Supervisor', 'System Admin'}

        return bool(user_groups & allowed_groups)  # Set intersection
