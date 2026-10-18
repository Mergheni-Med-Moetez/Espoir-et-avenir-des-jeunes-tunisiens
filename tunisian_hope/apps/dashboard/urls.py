"""
Dashboard URL Configuration
==============================

# EXAM DEFENSE: app_name for Namespacing
# =========================================
# Setting app_name = 'dashboard' means we use {% url 'dashboard:home' %}
# in templates instead of plain {% url 'home' %}. This prevents name
# collisions if another app also defines a 'home' view.
"""

from django.urls import path
from apps.dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('students/', views.student_list, name='student_list'),
    path('students/at-risk/', views.at_risk_students, name='at_risk'),
    path('health-records/', views.health_record_list, name='health_record_list'),
    path('health-records/at-risk/', views.at_risk_health, name='at_risk_health'),
    
    path('alerts/', views.alerts_list, name='alerts_list'),
    path('alerts/<int:alert_id>/', views.alert_detail, name='alert_detail'),
    path('alerts/<int:alert_id>/generate/', views.generate_alert_report, name='generate_alert_report'),
    path('alerts/<int:alert_id>/export/', views.export_alert_report, name='export_alert_report'),
]
