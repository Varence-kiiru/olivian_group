from django.core.management.base import BaseCommand
from django.db import transaction
from apps.projects.models import Project
from apps.core.models import ProjectShowcase


class Command(BaseCommand):
    help = 'Sync completed projects to project showcases for homepage display'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing showcases',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force_update = options['force']
        
        self.stdout.write("Syncing completed projects to project showcases...")
        
        # Get completed projects
        completed_projects = Project.objects.filter(status='completed').select_related('client')
        
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for project in completed_projects:
                # Map project type
                project_type_mapping = {
                    'residential': 'residential',
                    'commercial': 'commercial', 
                    'industrial': 'industrial',
                    'utility': 'commercial',  # Map utility to commercial
                    'maintenance': 'commercial',  # Map maintenance to commercial
                    'consultation': 'commercial',  # Map consultation to commercial
                }
                
                showcase_type = project_type_mapping.get(project.project_type, 'commercial')
                
                # Create location string
                location = f"{project.city}, {project.county}" if project.city and project.county else project.city or project.county or 'Kenya'
                
                # Format capacity
                capacity = f"{int(project.system_capacity)}kW" if project.system_capacity else "TBD"
                
                # Check if showcase already exists
                existing_showcase = ProjectShowcase.objects.filter(
                    title=project.name
                ).first()
                
                showcase_data = {
                    'title': project.name,
                    'description': project.description or f"Professional {project.get_project_type_display().lower()} solar installation providing clean energy solutions.",
                    'location': location,
                    'capacity': capacity,
                    'project_type': showcase_type,
                    'completion_date': project.actual_completion or project.target_completion,
                    'is_featured': True,  # Make completed projects featured
                    'order': 0,  # Will be ordered by completion date
                }
                
                if existing_showcase and force_update:
                    if not dry_run:
                        for key, value in showcase_data.items():
                            setattr(existing_showcase, key, value)
                        existing_showcase.save()
                    updated_count += 1
                    self.stdout.write(f"{'[DRY RUN] ' if dry_run else ''}Updated showcase: {project.name}")
                    
                elif not existing_showcase:
                    if not dry_run:
                        ProjectShowcase.objects.create(**showcase_data)
                    created_count += 1
                    self.stdout.write(f"{'[DRY RUN] ' if dry_run else ''}Created showcase: {project.name}")
                    
                else:
                    self.stdout.write(f"Skipped existing showcase: {project.name} (use --force to update)")
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\n[DRY RUN] Would create {created_count} and update {updated_count} project showcases"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSuccessfully created {created_count} and updated {updated_count} project showcases"
                )
            )
            
        # Show current stats
        total_showcases = ProjectShowcase.objects.count()
        featured_showcases = ProjectShowcase.objects.filter(is_featured=True).count()
        
        self.stdout.write(f"\nCurrent project showcases: {total_showcases} total, {featured_showcases} featured")
        self.stdout.write("Homepage will now display real project data!")
