"""
Dashboard Views — Supervisor KPI Dashboard and Student Lists
================================================================

# EXAM DEFENSE: Thin Views Pattern
# ===================================
# These views follow Django's "Thin Views" best practice:
# 1. Fetch data from the database using the ORM
# 2. Pass it to a template via the context dict
# 3. Return the rendered HTML
#
# Business logic (risk assessment, state transitions) lives in:
# - models.py (Fat Model: transition_to, is_editable_by)
# - services.py (scenario-specific: evaluate_student_risk)
#
# Views do NOT contain business logic — they are the "glue" between
# the HTTP request and the template. This makes them easy to test
# and swap out (e.g., replace with an API serializer later).
"""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Count, Q
from django.shortcuts import render

from apps.core.models import Case, AuditLog
from apps.education.models import StudentRecord


# =============================================================================
# PERMISSION HELPERS
# =============================================================================
def is_supervisor_or_admin(user):
    """
    Check if the user is in the Supervisor or System Admin group.

    # EXAM DEFENSE: Permission Check as a Function
    # ================================================
    # We extract this check into a reusable function because:
    # 1. @user_passes_test(is_supervisor_or_admin) is cleaner than repeating
    #    the group check inside every view function
    # 2. It's the same logic used in our GraphQL permissions (DRY)
    # 3. If we later add a 'Regional Manager' role, we change ONE function
    """
    user_groups = set(user.groups.values_list('name', flat=True))
    return bool(user_groups & {'Supervisor', 'System Admin'})


# =============================================================================
# VIEW: Supervisor Dashboard (KPIs)
# =============================================================================
@login_required
def dashboard_home(request):
    """
    Main dashboard page showing KPIs for the Education Early Warning scenario.

    # EXAM DEFENSE: Dashboard View — What It Does
    # ==============================================
    # This view computes 6 KPIs using Django ORM aggregate functions.
    # All computation happens in PostgreSQL (server-side) — we never
    # load all records into Python memory.
    #
    # The view is accessible to ALL authenticated users, but
    # Supervisors/Admins see extra admin-level stats.
    #
    # KPIs displayed:
    # 1. Total students in the system
    # 2. Students at risk (risk_score > 0)
    # 3. Students in ASSESSMENT (flagged by the service layer)
    # 4. Average attendance rate
    # 5. Status breakdown (for the state machine visualization)
    # 6. Recent audit log entries (last 10)
    """
    # --- Check Scenario ---
    scenario = request.GET.get('scenario', 'education')
    
    if scenario == 'health':
        from apps.health.models import HealthRecord
        all_students = HealthRecord.objects.select_related('case')
        cases = Case.objects.filter(scenario=Case.Scenario.HEALTH)
        kpi_attendance_label = "Avg Adherence"
        avg_attendance = all_students.aggregate(avg=Avg('adherence_rate'))['avg'] or 0.0
    else:
        all_students = StudentRecord.objects.select_related('case')
        cases = Case.objects.filter(scenario=Case.Scenario.EDUCATION)
        kpi_attendance_label = "Avg Attendance"
        avg_attendance = all_students.aggregate(avg=Avg('attendance_rate'))['avg'] or 0.0

    # --- KPI 1: Total students ---
    total_students = all_students.count()

    # --- KPI 2: At-risk students ---
    at_risk_count = all_students.filter(risk_score__gt=0).count()

    # --- KPI 3: Students currently in ASSESSMENT ---
    in_assessment = all_students.filter(case__status=Case.Status.ASSESSMENT).count()

    # --- KPI 4: Students currently in INTAKE (safe) ---
    in_intake = all_students.filter(case__status=Case.Status.INTAKE).count()

    # --- KPI 6: Average risk score ---
    avg_risk = all_students.aggregate(avg=Avg('risk_score'))['avg'] or 0.0

    # --- Status breakdown (for the bar chart / state machine visualization) ---
    status_counts = {}
    for status_choice in Case.Status:
        status_counts[status_choice.value] = {
            'label': status_choice.label,
            'count': cases.filter(status=status_choice.value).count(),
        }

    # --- Recent audit log entries ---
    recent_audits = AuditLog.objects.select_related('actor').order_by('-timestamp')[:10]

    # --- Top 5 highest-risk students (for the "urgent" table) ---
    top_risk_students = (
        all_students
        .filter(risk_score__gt=0)
        .select_related('case')
        .order_by('-risk_score')[:5]
    )

    # --- Check if the current user is a supervisor/admin ---
    is_admin_view = is_supervisor_or_admin(request.user)

    context = {
        # KPI values
        'total_students': total_students,
        'at_risk_count': at_risk_count,
        'in_assessment': in_assessment,
        'in_intake': in_intake,
        'avg_attendance': round(avg_attendance, 1),
        'avg_risk': round(avg_risk, 2),
        'kpi_attendance_label': kpi_attendance_label,
        # Breakdown data
        'status_counts': status_counts,
        'recent_audits': recent_audits,
        'top_risk_students': top_risk_students,
        # UI state
        'active_page': 'dashboard',
        'active_scenario': scenario,
        'is_admin_view': is_admin_view,
    }

    return render(request, 'dashboard/home.html', context)


# =============================================================================
# VIEW: Student List
# =============================================================================
@login_required
def student_list(request):
    """
    List all student records with their risk indicators.

    # EXAM DEFENSE: Thin View — Only Data Fetching
    # ================================================
    # This view does ONE thing: fetch students with their cases in a single
    # query (select_related), then pass them to the template. No business
    # logic, no risk computation, no state transitions.
    """
    students = (
        StudentRecord.objects
        .select_related('case', 'case__assigned_operator')
        .order_by('-risk_score', '-created_at')
    )

    context = {
        'students': students,
        'active_page': 'students',
        'total_count': students.count(),
    }

    return render(request, 'dashboard/student_list.html', context)


# =============================================================================
# VIEW: At-Risk Students
# =============================================================================
@login_required
def at_risk_students(request):
    """
    Show only students flagged as at-risk (risk_score > 0).

    # EXAM DEFENSE: Filtered View
    # ==============================
    # This is a focused view for case workers: it shows ONLY the students
    # that need attention. By filtering at the ORM level, PostgreSQL handles
    # the WHERE clause — we don't load safe students into memory.
    """
    students = (
        StudentRecord.objects
        .filter(risk_score__gt=0)
        .select_related('case', 'case__assigned_operator')
        .order_by('-risk_score')
    )

    context = {
        'students': students,
        'active_page': 'at-risk',
        'total_count': students.count(),
    }

    return render(request, 'dashboard/at_risk.html', context)


# =============================================================================
# VIEW: Health Record List
# =============================================================================
@login_required
def health_record_list(request):
    """List all health records."""
    from apps.health.models import HealthRecord
    records = (
        HealthRecord.objects
        .select_related('case', 'case__assigned_operator')
        .order_by('-risk_score', '-case__created_at')
    )
    context = {
        'students': records,
        'active_page': 'health_records',
        'total_count': records.count(),
        'scenario': 'health'
    }
    return render(request, 'dashboard/health_list.html', context)


# =============================================================================
# VIEW: At-Risk Health Records
# =============================================================================
@login_required
def at_risk_health(request):
    """Show only health records flagged as at-risk."""
    from apps.health.models import HealthRecord
    records = (
        HealthRecord.objects
        .filter(risk_score__gt=0)
        .select_related('case', 'case__assigned_operator')
        .order_by('-risk_score')
    )
    context = {
        'students': records,
        'active_page': 'at_risk_health',
        'total_count': records.count(),
        'scenario': 'health'
    }
    return render(request, 'dashboard/health_at_risk.html', context)


# =============================================================================
# VIEW: Alerts List
# =============================================================================
@login_required
@user_passes_test(is_supervisor_or_admin)
def alerts_list(request):
    """List all alerts targeted to the current user."""
    from apps.core.models import Alert
    alerts = Alert.objects.filter(target_user=request.user).order_by('-created_at')
    
    context = {
        'alerts': alerts,
        'active_page': 'alerts',
    }
    return render(request, 'dashboard/alerts_list.html', context)

# =============================================================================
# VIEW: Alert Detail
# =============================================================================
@login_required
@user_passes_test(is_supervisor_or_admin)
def alert_detail(request, alert_id):
    """View the details and the AI report of a specific alert."""
    from django.shortcuts import get_object_or_404
    from apps.core.models import Alert
    alert = get_object_or_404(Alert, id=alert_id, target_user=request.user)
    
    # Mark as read
    if not alert.is_read:
        alert.is_read = True
        alert.save(update_fields=['is_read'])
        
    context = {
        'alert': alert,
        'active_page': 'alerts',
    }
    return render(request, 'dashboard/alert_detail.html', context)

# =============================================================================
# VIEW: Generate AI Report (On Demand)
# =============================================================================
@login_required
@user_passes_test(is_supervisor_or_admin)
def generate_alert_report(request, alert_id):
    """Triggers Ollama generation for the alert and redirects back to detail view."""
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from apps.core.models import Alert
    from apps.core.ai_services import generate_report_for_alert
    
    alert = get_object_or_404(Alert, id=alert_id, target_user=request.user)
    
    success = generate_report_for_alert(alert)
    if success:
        messages.success(request, "AI Report generated successfully.")
    else:
        messages.error(request, "Failed to generate AI report.")
        
    return redirect('dashboard:alert_detail', alert_id=alert.id)


# =============================================================================
# VIEW: Export AI Report to PDF
# =============================================================================
@login_required
@user_passes_test(is_supervisor_or_admin)
def export_alert_report(request, alert_id):
    """Generates a PDF from the report text and returns it as a download."""
    from django.shortcuts import get_object_or_404, redirect
    from django.http import HttpResponse
    from django.contrib import messages
    from apps.core.models import Alert
    from apps.core.ai_services import generate_pdf_from_text
    
    alert = get_object_or_404(Alert, id=alert_id, target_user=request.user)
    
    if not alert.report_text:
        messages.error(request, "Cannot export: No report text exists yet.")
        return redirect('dashboard:alert_detail', alert_id=alert.id)
        
    pdf_bytes = generate_pdf_from_text(alert.report_text, alert.case.reference)
    
    if not pdf_bytes:
        messages.error(request, "PDF generation failed internally.")
        return redirect('dashboard:alert_detail', alert_id=alert.id)
        
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ai_report_{alert.case.reference}.pdf"'
    return response

