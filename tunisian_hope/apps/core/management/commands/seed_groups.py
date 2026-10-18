"""
Management Command: seed_groups
==================================
Usage: python manage.py seed_groups

# EXAM DEFENSE: Management Commands
# ====================================
# Django management commands are custom CLI tools you run with manage.py.
# This command manually creates the 3 role Groups and optionally creates
# a demo superuser for each role.
#
# Why have this if the signal already creates groups?
# → The signal is the automatic safety net. This command is for:
#   1. Explicit setup during demos ("see, I run this command and roles exist")
#   2. Creating demo users with known passwords for the live demo
#   3. Resetting roles if something goes wrong
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

from apps.core.models import ROLES, UserProfile


class Command(BaseCommand):
    """Create the 4 role Groups and optional demo users."""

    help = 'Seed the database with the 3 platform role Groups and demo users.'

    def add_arguments(self, parser):
        """
        Add optional --with-users flag.

        # EXAM DEFENSE: add_arguments lets us define CLI flags.
        # --with-users creates a demo user for each role so the professor
        # can log in and test different roles during the live demo.
        """
        parser.add_argument(
            '--with-users',
            action='store_true',
            help='Also create a demo user for each role (password: demo1234).',
        )

    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(self.style.MIGRATE_HEADING('Seeding role groups...'))

        # Step 1: Create Groups
        for role_name in ROLES:
            group, created = Group.objects.get_or_create(name=role_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  [OK] Created group: {role_name}'))
            else:
                self.stdout.write(f'  [--] Group already exists: {role_name}')

        # Step 1b: Assign Django Admin permissions to Supervisor and System Admin
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        # Get permissions
        admin_content_types = ContentType.objects.filter(app_label__in=['core', 'education', 'auth', 'health'])
        admin_perms = Permission.objects.filter(content_type__in=admin_content_types)

        supervisor_content_types = ContentType.objects.filter(app_label__in=['core', 'education', 'health'])
        supervisor_perms = Permission.objects.filter(content_type__in=supervisor_content_types)

        # Assign to System Admin (Everything)
        admin_group = Group.objects.filter(name='System Admin').first()
        if admin_group:
            admin_group.permissions.set(admin_perms)

        # Assign to Supervisor (Only core and education)
        supervisor_group = Group.objects.filter(name='Supervisor').first()
        if supervisor_group:
            supervisor_group.permissions.set(supervisor_perms)

        # Assign limited permissions to Field Operator
        operator_group = Group.objects.filter(name='Field Operator').first()
        if operator_group:
            case_perms = Permission.objects.filter(content_type__app_label='core', codename__in=['view_case', 'change_case', 'add_case'])
            operator_group.permissions.set(case_perms)

        self.stdout.write(self.style.SUCCESS('  [OK] Assigned model permissions to admin groups'))

        # Step 2: Optionally create demo users
        if options['with_users']:
            self.stdout.write(self.style.MIGRATE_HEADING('\nCreating demo users...'))

            # Map each role to a simple username
            demo_users = {
                'Field Operator': 'operator',
                'Supervisor': 'supervisor',
                'System Admin': 'admin_user',
            }

            for role_name, username in demo_users.items():
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': username.capitalize(),
                        'last_name': 'Demo',
                        'email': f'{username}@tunisianhope.tn',
                        'is_staff': True,  # Allows admin site access
                    },
                )
                if created:
                    user.set_password('demo1234')
                    user.save()

                    # Assign to role group
                    group = Group.objects.get(name=role_name)
                    user.groups.add(group)

                    # Create profile
                    UserProfile.objects.get_or_create(
                        user=user,
                        defaults={'region': 'tunis'},
                    )

                    self.stdout.write(
                        self.style.SUCCESS(f'  [OK] Created user: {username} ({role_name})')
                    )
                else:
                    self.stdout.write(f'  [--] User already exists: {username}')

        self.stdout.write(self.style.SUCCESS('\n[OK] Seeding complete!'))
