from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from apps.chat.models import ChatRoom
from apps.projects.models import Project
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create default chat rooms for the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of default rooms',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No rooms will be created'))

        self.stdout.write(self.style.SUCCESS('Starting creation of default chat rooms...'))

        # Create general announcements room
        self.create_general_announcements_room(force, dry_run)

        # Create department rooms based on existing groups
        self.create_department_rooms(force, dry_run)

        # Create project rooms for active projects
        self.create_project_rooms(force, dry_run)

        self.stdout.write(self.style.SUCCESS('Default rooms creation completed!'))

    def create_general_announcements_room(self, force=False, dry_run=False):
        """Create the main general announcements room"""
        room_name = 'general-announcements'

        if ChatRoom.objects.filter(name=room_name).exists() and not force:
            self.stdout.write(f'General announcements room "{room_name}" already exists. Skipping.')
            return

        if dry_run:
            self.stdout.write(f'Would create: General Announcements room "{room_name}"')
            return

        room, created = ChatRoom.objects.get_or_create(
            name=room_name,
            defaults={
                'room_type': 'general',
                'description': 'Company-wide announcements, updates, and important communications',
                'created_by': self.get_superuser(),
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created general announcements room: {room_name}'))
        elif force:
            room.room_type = 'general'
            room.description = 'Company-wide announcements, updates, and important communications'
            room.save()
            self.stdout.write(self.style.SUCCESS(f'Updated general announcements room: {room_name}'))

    def create_department_rooms(self, force=False, dry_run=False):
        """Create department chat rooms based on existing Django groups"""
        departments = [
            'management', 'sales', 'operations', 'technical', 'hr', 'finance',
            'marketing', 'customer-service', 'projects', 'inventory'
        ]

        for dept in departments:
            # Check if a group with this name exists (case-insensitive)
            group = Group.objects.filter(name__iexact=dept).first()
            if not group and 'management' in dept.lower():
                # Special case for management variations
                group = Group.objects.filter(name__icontains='manager').first()

            room_name = f"{dept.lower().replace('_', '-')}-chat"

            if ChatRoom.objects.filter(name=room_name).exists() and not force:
                self.stdout.write(f'Department room "{room_name}" already exists. Skipping.')
                continue

            if dry_run:
                self.stdout.write(f'Would create: Department room "{room_name}"')
                continue

            room, created = ChatRoom.objects.get_or_create(
                name=room_name,
                defaults={
                    'room_type': 'department',
                    'description': f'Department communication for {dept.replace("-", " ").title()}',
                    'created_by': self.get_superuser(),
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Created department room: {room_name}'))

    def create_project_rooms(self, force=False, dry_run=False):
        """Create chat rooms for active projects"""
        # Get active projects
        projects = Project.objects.filter(
            status__in=['planning', 'scheduled', 'in_progress', 'testing']
        )

        if not projects.exists():
            self.stdout.write('No new active projects found that need chat rooms.')
            return

        for project in projects:
            room_name = f"project-{project.project_number.lower()}"

            if ChatRoom.objects.filter(name=room_name).exists() and not force:
                self.stdout.write(f'Project room "{room_name}" already exists. Skipping.')
                continue

            if dry_run:
                self.stdout.write(f'Would create: Project room "{room_name}" for project {project.name}')
                continue

            # Get participants - project manager and team members
            participants = []
            if project.project_manager:
                participants.append(project.project_manager)

            # Add installation team members
            for user in project.installation_team.all():
                if user not in participants:
                    participants.append(user)

            room = ChatRoom.objects.create(
                name=room_name,
                room_type='project',
                description=f'Communication room for project: {project.name}',
                project=project,
                created_by=self.get_superuser(),
            )

            # Add participants
            room.participants.set(participants)
            room.save()

            self.stdout.write(self.style.SUCCESS(f'Created project room: {room_name} for {project.name} with {len(participants)} participants'))

    def get_superuser(self):
        """Get a superuser to set as room creator"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        superuser = User.objects.filter(is_superuser=True).first()
        if not superuser:
            # Fallback to first admin
            superuser = User.objects.filter(is_staff=True).first()
        if not superuser:
            # Last fallback - create system user
            superuser = User.objects.filter(is_active=True).first()
        return superuser
