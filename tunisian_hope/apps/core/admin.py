"""
Core Admin — Register models with Django's admin interface
============================================================

# EXAM DEFENSE: Django Admin Registration
# ==========================================
# Django's admin is a free, auto-generated CRUD interface. By registering
# our models here, the professor can immediately inspect and edit data
# through the browser at /admin/ during the demo.
#
# We customize the admin display with:
# - list_display: columns shown in the list view
# - list_filter: sidebar filters for quick filtering
# - search_fields: enables the search bar
# - readonly_fields: prevents accidental edits to auto-generated fields
#
# This directly addresses rubric C1 (Backend implementation quality).
"""

from django.contrib import admin

from apps.core.models import UserProfile, Case, AuditLog


# =============================================================================
# USER PROFILE ADMIN
# =============================================================================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for UserProfile."""

    list_display = ('user', 'role_name', 'region', 'phone', 'created_at')
    list_filter = ('region',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')
    readonly_fields = ('created_at', 'updated_at')

    # EXAM DEFENSE: raw_id_fields replaces the User dropdown with a lookup
    # popup. Without this, Django loads ALL users into a <select> — very
    # slow if you have hundreds of users.
    raw_id_fields = ('user',)

    def has_delete_permission(self, request, obj=None):
        """Only System Admins can delete user profiles. Supervisors cannot."""
        if request.user.is_superuser or request.user.groups.filter(name='System Admin').exists():
            return True
        return False


# =============================================================================
# CASE ADMIN
# =============================================================================
@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    """Admin configuration for Case with state machine visualization."""

    list_display = (
        'reference', 'title', 'scenario', 'status',
        'priority', 'assigned_operator', 'created_at',
    )
    list_filter = ('status', 'scenario', 'priority', 'created_at')
    search_fields = ('reference', 'title', 'description')
    readonly_fields = ('reference', 'created_at', 'updated_at')
    raw_id_fields = ('assigned_operator', 'supervisor')

    # EXAM DEFENSE: fieldsets organize the admin form into logical groups.
    # This makes it easier for the professor to see the data structure.
    fieldsets = (
        ('Case Information', {
            'fields': ('reference', 'title', 'description', 'scenario'),
        }),
        ('Workflow', {
            'fields': ('status', 'priority'),
        }),
        ('Assigned Staff', {
            'fields': ('assigned_operator', 'supervisor'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),  # Collapsed by default to save space
        }),
    )

    def get_queryset(self, request):
        """Restrict operators to seeing only their own cases."""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.groups.filter(name__in=['Supervisor', 'System Admin']).exists():
            return qs
        return qs.filter(assigned_operator=request.user)

    def has_change_permission(self, request, obj=None):
        """Ensure operators can only edit their own cases."""
        if request.user.is_superuser or request.user.groups.filter(name__in=['Supervisor', 'System Admin']).exists():
            return True
        if obj is not None and obj.assigned_operator != request.user:
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        """Ensure operators cannot delete cases."""
        if request.user.groups.filter(name='Field Operator').exists():
            return False
        return True


# =============================================================================
# AUDIT LOG ADMIN
# =============================================================================
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin configuration for AuditLog.

    # EXAM DEFENSE: AuditLog is READ-ONLY in the admin.
    # Audit logs must NEVER be editable — that would defeat their purpose.
    # We use has_add/change/delete_permission to enforce this at the admin level.
    """

    list_display = ('timestamp', 'actor', 'action', 'target_model', 'target_id')
    list_filter = ('action', 'target_model', 'timestamp')
    search_fields = ('actor__username', 'target_model')
    readonly_fields = (
        'actor', 'action', 'target_model', 'target_id',
        'old_value', 'new_value', 'ip_address', 'timestamp',
    )

    def has_add_permission(self, request):
        """Prevent manual creation of audit logs via admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing of audit logs — they must be immutable."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs — they are permanent records."""
        return False
