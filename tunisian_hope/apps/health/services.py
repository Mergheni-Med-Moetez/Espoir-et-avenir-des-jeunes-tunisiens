import logging
from django.utils import timezone
from apps.core.models import Case, AuditLog
from apps.health.models import HealthRecord
from apps.core.ai_services import create_alerts_for_case

logger = logging.getLogger(__name__)

ADHERENCE_THRESHOLD = 70.0
MISSED_APPOINTMENTS_THRESHOLD = 2

def evaluate_health_risk(health_record):
    risk_factors = []
    risk_score = 0.0

    if health_record.adherence_rate < ADHERENCE_THRESHOLD:
        gap = ADHERENCE_THRESHOLD - health_record.adherence_rate
        adherence_risk = min(gap / ADHERENCE_THRESHOLD, 0.5)
        risk_score += adherence_risk
        risk_factors.append(
            f"Low adherence: {health_record.adherence_rate}% "
            f"(threshold: {ADHERENCE_THRESHOLD}%)"
        )

    if health_record.missed_appointments >= MISSED_APPOINTMENTS_THRESHOLD:
        risk_score += 0.3
        risk_factors.append(
            f"High missed appointments: {health_record.missed_appointments} "
            f"(threshold: {MISSED_APPOINTMENTS_THRESHOLD})"
        )

    risk_score = min(round(risk_score, 2), 1.0)

    return {
        'risk_score': risk_score,
        'risk_factors': risk_factors,
        'is_at_risk': len(risk_factors) > 0,
    }

def process_health_cases(actor):
    intake_cases = (
        Case.objects
        .filter(status=Case.Status.INTAKE, scenario=Case.Scenario.HEALTH)
        .select_related('health_record')
    )

    results = {
        'total_scanned': 0,
        'flagged': 0,
        'safe': 0,
        'errors': [],
    }

    for case in intake_cases:
        results['total_scanned'] += 1

        try:
            health_record = case.health_record
        except HealthRecord.DoesNotExist:
            results['errors'].append(
                f"Case {case.reference} has no HealthRecord — skipped."
            )
            continue

        assessment = evaluate_health_risk(health_record)

        health_record.risk_score = assessment['risk_score']
        health_record.risk_factors = assessment['risk_factors']
        health_record.last_assessed_at = timezone.now()
        health_record.save(update_fields=[
            'risk_score', 'risk_factors', 'last_assessed_at'
        ])

        if assessment['is_at_risk']:
            try:
                case.transition_to(Case.Status.ASSESSMENT, actor=actor)
                results['flagged'] += 1
                logger.info(
                    "Health Case %s flagged: risk_score=%.2f, factors=%s",
                    case.reference,
                    assessment['risk_score'],
                    assessment['risk_factors'],
                )
                # Create alerts for supervisors (AI report generated on demand later)
                create_alerts_for_case(case)
            except Exception as e:
                results['errors'].append(
                    f"Case {case.reference}: transition failed — {str(e)}"
                )
        else:
            results['safe'] += 1
            logger.debug(
                "Health Case %s is safe: risk_score=%.2f",
                case.reference,
                assessment['risk_score'],
            )

    return results
