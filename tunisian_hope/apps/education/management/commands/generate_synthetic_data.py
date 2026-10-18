"""
Management Command: generate_synthetic_data
=============================================

# EXAM DEFENSE: Why a Management Command for Data Generation?
# =============================================================
# 1. Repeatable: Run it once to populate the DB, run it again if you
#    need to reset. The --flush flag deletes old data first.
# 2. Controllable: --count lets you generate 10 students for quick tests
#    or 200 for a realistic demo. Default is 50 as the rubric requires.
# 3. Realistic: Uses the Faker library to generate Tunisian-sounding names,
#    realistic dates, and varied risk profiles.
# 4. Integrated: After generating data, it auto-runs the risk assessment
#    service to transition at-risk students from INTAKE → ASSESSMENT.
#
# Usage:
#   python manage.py generate_synthetic_data               # 50 students
#   python manage.py generate_synthetic_data --count 200   # 200 students
#   python manage.py generate_synthetic_data --flush       # clear + regenerate
#   python manage.py generate_synthetic_data --skip-assess # don't auto-assess
"""

import random
from datetime import date

from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand
from faker import Faker

from apps.core.models import Case
from apps.education.models import StudentRecord
from apps.education.services import process_intake_cases
from apps.health.models import HealthRecord
from apps.health.services import process_health_cases


# =============================================================================
# TUNISIAN DATA POOLS
# =============================================================================
# EXAM DEFENSE: Realistic Synthetic Data
# =========================================
# We define Tunisian-specific name pools and school names to make the demo
# look realistic during the presentation. These are common Tunisian names
# — NOT real people. The Faker library handles dates and random choices.

TUNISIAN_FIRST_NAMES_MALE = [
    'Ahmed', 'Mohamed', 'Youssef', 'Ali', 'Omar', 'Amine', 'Khalil',
    'Hamza', 'Bilel', 'Seif', 'Nizar', 'Anis', 'Fares', 'Rami', 'Zied',
]
TUNISIAN_FIRST_NAMES_FEMALE = [
    'Fatma', 'Mariem', 'Ines', 'Amina', 'Nour', 'Sarra', 'Hiba',
    'Yasmine', 'Rania', 'Lina', 'Asma', 'Eya', 'Rim', 'Dorra', 'Salma',
]
TUNISIAN_LAST_NAMES = [
    'Ben Ali', 'Trabelsi', 'Gharbi', 'Hajji', 'Bouazizi', 'Meddeb',
    'Chaabane', 'Khelifi', 'Jaziri', 'Sfaxi', 'Souissi', 'Dridi',
    'Hamdi', 'Mejri', 'Nasri', 'Saidi', 'Bouzid', 'Larbi', 'Ghorbel',
]
TUNISIAN_SCHOOLS = [
    'Lycee Bourguiba', 'College Ibn Khaldoun', 'Lycee Pilote Sfax',
    'College Farhat Hached', 'Lycee Ariana', 'College Sousse Medina',
    'Lycee Carthage', 'College El Menzah', 'Lycee Bizerte Nord',
    'College Mahdia Centre', 'Lycee El Kef', 'College Monastir',
]
HEALTH_CONDITIONS = [
    'Asthma', 'Diabetes Type 1', 'Severe Malnutrition', 'Obesity', 
    'Chronic Bronchitis', 'Anemia', 'Depression'
]


class Command(BaseCommand):
    """Generate synthetic student records with realistic Tunisian data."""

    help = (
        'Generate synthetic StudentRecord data using Faker. '
        'Creates Cases in INTAKE status and links each to a StudentRecord. '
        'Optionally runs the risk assessment to auto-flag at-risk students.'
    )

    def add_arguments(self, parser):
        """
        Define CLI arguments.

        # EXAM DEFENSE: add_arguments is Django's way to declare CLI flags.
        # The parser is Python's argparse under the hood. Each argument
        # gets a help string so 'manage.py generate_synthetic_data --help'
        # is self-documenting.
        """
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of synthetic student records to generate (default: 50).',
        )
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing StudentRecords and their Cases before generating.',
        )
        parser.add_argument(
            '--skip-assess',
            action='store_true',
            help='Skip the automatic risk assessment after data generation.',
        )
        parser.add_argument(
            '--seed',
            type=int,
            default=42,
            help='Random seed for reproducible data generation (default: 42).',
        )

    def handle(self, *args, **options):
        """
        Main entry point for the management command.

        # EXAM DEFENSE: The handle() method
        # ====================================
        # Django calls this when you run: python manage.py generate_synthetic_data
        # We break the work into clear steps:
        # 1. Setup (seed, Faker instance)
        # 2. Optional flush (delete old data)
        # 3. Get or create the operator user
        # 4. Generate N students with varied risk profiles
        # 5. Optionally run the risk assessment service
        """
        count = options['count']
        flush = options['flush']
        skip_assess = options['skip_assess']
        seed = options['seed']

        # Step 1: Initialize Faker with a seed for reproducibility
        # EXAM DEFENSE: Setting a seed means running the command twice
        # produces the EXACT same data — essential for demos and tests.
        fake = Faker(['ar_AA'])  # Arabic locale for realistic names
        Faker.seed(seed)
        random.seed(seed)

        self.stdout.write(f"\nGenerating {count} synthetic student records (seed={seed})...\n")

        # Step 2: Optional flush
        if flush:
            deleted_students, _ = StudentRecord.objects.all().delete()
            deleted_cases, _ = Case.objects.filter(
                scenario=Case.Scenario.EDUCATION
            ).delete()
            deleted_health, _ = HealthRecord.objects.all().delete()
            deleted_health_cases, _ = Case.objects.filter(
                scenario=Case.Scenario.HEALTH
            ).delete()
            self.stdout.write(self.style.WARNING(
                f"  Flushed {deleted_students} education records, {deleted_cases} education cases, "
                f"{deleted_health} health records, and {deleted_health_cases} health cases."
            ))

        # Step 3: Get or create the demo operator
        operator_group, _ = Group.objects.get_or_create(name='Field Operator')
        operator, created = User.objects.get_or_create(
            username='operator',
            defaults={
                'first_name': 'Karim',
                'last_name': 'Ben Salah',
                'email': 'operator@demo.tn',
            },
        )
        if created:
            operator.set_password('demo1234')
            operator.save()
        operator.groups.add(operator_group)

        # Step 4: Generate students with controlled risk distribution
        # EXAM DEFENSE: Risk Distribution Strategy
        # ==========================================
        # We don't generate 50 identical students. We create 3 profiles:
        #   ~35% "at-risk"    → low attendance + declining grades
        #   ~30% "borderline" → one risk factor present
        #   ~35% "safe"       → good attendance + stable/improving grades
        # This ensures a realistic mix that triggers our state machine AND
        # demonstrates the risk assessment during the live demo.

        created_count = 0
        for i in range(1, count + 1):
            student_id = f"STU-{date.today().year}-{str(i).zfill(3)}"

            # Skip if this student already exists (idempotent)
            if StudentRecord.objects.filter(student_id=student_id).exists():
                self.stdout.write(f"  [--] Student {student_id} already exists, skipping.")
                continue

            # Decide risk profile for this student
            profile = self._choose_risk_profile(i, count)

            # Generate identity data
            is_male = random.choice([True, False])
            first_name = random.choice(
                TUNISIAN_FIRST_NAMES_MALE if is_male else TUNISIAN_FIRST_NAMES_FEMALE
            )
            last_name = random.choice(TUNISIAN_LAST_NAMES)

            # Generate school data
            school_type = random.choice([
                StudentRecord.SchoolType.MIDDLE,
                StudentRecord.SchoolType.HIGH,
            ])
            grade_level = random.randint(7, 9) if school_type == 'middle' else random.randint(10, 12)

            # Generate risk indicators based on the chosen profile
            attendance_rate = profile['attendance_fn']()
            grade_trend = profile['grade_trend']
            behavior_notes = profile['behavior_fn']()

            # Create the Case first (INTAKE status, EDUCATION scenario)
            case = Case.objects.create(
                title=f"Education monitoring: {first_name} {last_name}",
                description=(
                    f"Intake record for student {student_id} at "
                    f"{random.choice(TUNISIAN_SCHOOLS)}. "
                    f"Attendance: {attendance_rate}%, "
                    f"Grade trend: {grade_trend}, "
                    f"Behavior notes: {behavior_notes}."
                ),
                scenario=Case.Scenario.EDUCATION,
                priority=profile['priority'],
                assigned_operator=operator,
            )

            # Create the linked StudentRecord
            date_of_birth = fake.date_of_birth(minimum_age=11, maximum_age=18)
            StudentRecord.objects.create(
                case=case,
                student_id=student_id,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                school_name=random.choice(TUNISIAN_SCHOOLS),
                school_type=school_type,
                grade_level=grade_level,
                attendance_rate=round(attendance_rate, 1),
                grade_trend=grade_trend,
                behavior_notes_count=behavior_notes,
            )

            # =========================================================
            # Generate Health Record for the same student
            # =========================================================
            health_id = f"HLT-{date.today().year}-{str(i).zfill(3)}"
            condition = random.choice(HEALTH_CONDITIONS)
            
            # Align health risk with education risk for demo consistency
            if profile['label'] == 'AT-RISK':
                adherence_rate = random.uniform(40.0, 60.0)
                missed = random.randint(3, 5)
                health_risk = random.uniform(0.7, 1.0)
                health_status = Case.Status.ASSESSMENT
            elif profile['label'] == 'BORDERLINE':
                adherence_rate = random.uniform(60.0, 80.0)
                missed = random.randint(1, 2)
                health_risk = random.uniform(0.3, 0.6)
                health_status = Case.Status.INTAKE
            else:
                adherence_rate = random.uniform(80.0, 100.0)
                missed = 0
                health_risk = 0.0
                health_status = Case.Status.INTAKE

            health_case = Case.objects.create(
                title=f"Health monitoring: {first_name} {last_name}",
                description=f"Routine follow-up and monitoring for {condition}.",
                scenario=Case.Scenario.HEALTH,
                status=health_status,
                priority=profile['priority'],
                assigned_operator=operator,
            )

            HealthRecord.objects.create(
                case=health_case,
                student_id=health_id,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                health_condition=condition,
                adherence_rate=round(adherence_rate, 1),
                missed_appointments=missed,
                risk_score=health_risk,
            )

            created_count += 1
            label = profile['label']
            self.stdout.write(
                f"  [{i:>3}/{count}] {student_id} — {first_name} {last_name} "
                f"({label}, {attendance_rate:.1f}% att., {grade_trend})"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\n[OK] Created {created_count} student records.\n"
        ))

        # Step 5: Run risk assessment (unless --skip-assess)
        if not skip_assess:
            self.stdout.write("Running risk assessment on INTAKE cases...\n")
            results = process_intake_cases(actor=operator)
            self.stdout.write(self.style.SUCCESS(
                f"  Scanned:  {results['total_scanned']} cases\n"
                f"  Flagged:  {results['flagged']} (transitioned to ASSESSMENT)\n"
                f"  Safe:     {results['safe']}\n"
                f"  Errors:   {len(results['errors'])}"
            ))
            if results['errors']:
                for err in results['errors']:
                    self.stdout.write(self.style.ERROR(f"  ! {err}"))
            
            self.stdout.write("Running risk assessment on HEALTH cases...\n")
            health_results = process_health_cases(actor=operator)
            self.stdout.write(self.style.SUCCESS(
                f"  Scanned:  {health_results['total_scanned']} cases\n"
                f"  Flagged:  {health_results['flagged']} (transitioned to ASSESSMENT)\n"
                f"  Safe:     {health_results['safe']}\n"
                f"  Errors:   {len(health_results['errors'])}"
            ))
            if health_results['errors']:
                for err in health_results['errors']:
                    self.stdout.write(self.style.ERROR(f"  ! {err}"))
        else:
            self.stdout.write(self.style.WARNING(
                "Skipped risk assessment (use without --skip-assess to auto-flag)."
            ))

        self.stdout.write(self.style.SUCCESS("\n[OK] Data generation complete!"))

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================
    def _choose_risk_profile(self, index, total):
        """
        Assign a risk profile based on the student's position in the batch.

        # EXAM DEFENSE: Deterministic Risk Distribution
        # ================================================
        # Instead of purely random values (which can produce unrealistic
        # data), we divide students into 3 tiers:
        #   First ~35% → at-risk (low attendance, declining grades)
        #   Next  ~30% → borderline (one risk factor)
        #   Last  ~35% → safe (good attendance, stable/improving)
        #
        # This guarantees the demo always has a meaningful mix of risk
        # levels, making the dashboard and state transitions interesting.
        """
        position = index / total

        if position <= 0.35:
            # AT-RISK profile
            return {
                'label': 'AT-RISK',
                'attendance_fn': lambda: random.uniform(45.0, 80.0),
                'grade_trend': StudentRecord.GradeTrend.DECLINING,
                'behavior_fn': lambda: random.randint(3, 8),
                'priority': Case.Priority.HIGH,
            }
        elif position <= 0.65:
            # BORDERLINE profile
            return {
                'label': 'BORDERLINE',
                'attendance_fn': lambda: random.uniform(75.0, 90.0),
                'grade_trend': random.choice([
                    StudentRecord.GradeTrend.STABLE,
                    StudentRecord.GradeTrend.DECLINING,
                ]),
                'behavior_fn': lambda: random.randint(1, 4),
                'priority': Case.Priority.MEDIUM,
            }
        else:
            # SAFE profile
            return {
                'label': 'SAFE',
                'attendance_fn': lambda: random.uniform(88.0, 100.0),
                'grade_trend': random.choice([
                    StudentRecord.GradeTrend.STABLE,
                    StudentRecord.GradeTrend.IMPROVING,
                ]),
                'behavior_fn': lambda: random.randint(0, 2),
                'priority': Case.Priority.LOW,
            }
