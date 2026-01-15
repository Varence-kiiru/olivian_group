from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

DEPARTMENT_GROUP_MAPPING = {
    'sales': ['sales'],
    'technical': ['technical', 'technician'],
    'management': ['management', 'director', 'manager'],
    'finance': ['finance'],
    'hr': ['hr', 'human resources'],
    'marketing': ['marketing'],
    'customer-service': ['customer-service', 'support'],
    'inventory': ['inventory'],
    'operations': ['operations', 'operational'],
    'projects': ['projects', 'project-manager'],
}


class Command(BaseCommand):
    help = 'Sync user departments with Django Groups for chat access control'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually making changes',
        )
        parser.add_argument(
            '--department',
            type=str,
            help='Sync only users in this specific department',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        department_filter = options.get('department')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Get users to process
        users = User.objects.exclude(department='')
        if department_filter:
            users = users.filter(department__iexact=department_filter)
            self.stdout.write(f'Syncing users in department: {department_filter}')

        total_users = users.count()
        if total_users == 0:
            self.stdout.write(self.style.WARNING('No users with departments found.'))
            return

        self.stdout.write(f'Processing {total_users} users with department assignments...')

        updated_count = 0
        created_groups = set()

        for user in users:
            changes_made = self.sync_user_department_groups(user, dry_run, created_groups)

            if changes_made:
                updated_count += 1
                if not dry_run:
                    self.stdout.write(f'✓ Updated groups for {user.username} ({user.department})')
                else:
                    self.stdout.write(f'Would update groups for {user.username} ({user.department})')

        if created_groups:
            self.stdout.write(f'Created new groups: {", ".join(sorted(created_groups))}')

        self.stdout.write(
            self.style.SUCCESS(f'Sync complete. Updated {updated_count} users.')
        )

    def sync_user_department_groups(self, user, dry_run=False, created_groups=None):
        """
        Sync a single user's department with appropriate Django Groups
        Returns True if changes were made
        """
        if not user.department:
            return False

        department_key = user.department.lower().replace(' ', '-').replace('_', '-')

        # Find matching groups for this department
        target_groups = []
        for dept_key, group_names in DEPARTMENT_GROUP_MAPPING.items():
            if dept_key in department_key or any(g in department_key for g in group_names):
                target_groups.extend(group_names)
                break

        if not target_groups:
            # Fallback: use department name directly
            target_groups = [user.department.lower().replace(' ', '-')]

        current_groups = set(user.groups.values_list('name', flat=True))
        target_groups_set = set(target_groups)

        # Add missing department groups
        groups_to_add = target_groups_set - current_groups

        if not dry_run:
            for group_name in groups_to_add:
                group, created = Group.objects.get_or_create(name=group_name)
                user.groups.add(group)
                if created and created_groups is not None:
                    created_groups.add(group_name)

            # Add to 'staff' group if employee
            if user.role != 'customer':
                staff_group, created = Group.objects.get_or_create(name='staff')
                user.groups.add(staff_group)
                if created and created_groups is not None:
                    created_groups.add('staff')

        return len(groups_to_add) > 0
