from django.contrib import admin
from apps.health.models import HealthRecord

@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'first_name', 'last_name', 'health_condition', 'adherence_rate', 'risk_score')
    search_fields = ('student_id', 'first_name', 'last_name', 'health_condition')
    list_filter = ('health_condition',)
    readonly_fields = ('risk_score', 'risk_factors', 'last_assessed_at')
