from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import Case

class HealthRecord(models.Model):
    case = models.OneToOneField(
        Case,
        on_delete=models.CASCADE,
        related_name='health_record',
        help_text='The case handling this health follow-up.'
    )
    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    
    health_condition = models.CharField(
        max_length=100,
        help_text='Primary health condition being monitored (e.g., Asthma, Diabetes).'
    )
    adherence_rate = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text='Percentage of medication/treatment adhered to (0-100).'
    )
    missed_appointments = models.PositiveIntegerField(
        default=0,
        help_text='Number of recent missed check-ups or appointments.'
    )
    
    risk_score = models.FloatField(
        null=True, blank=True,
        help_text='Computed risk score from 0.0 (safe) to 1.0 (critical).'
    )
    risk_factors = models.JSONField(
        null=True, blank=True,
        help_text='List of reasons contributing to the risk score.'
    )
    last_assessed_at = models.DateTimeField(
        null=True, blank=True,
        help_text='When the risk score was last calculated.'
    )

    class Meta:
        verbose_name = 'Health Record'
        verbose_name_plural = 'Health Records'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id}) - {self.health_condition}"
