from django.core.management.base import BaseCommand
from django.db import transaction
from apps.core.models import ProjectShowcase
from apps.projects.models import Project
from apps.quotations.models import Customer
from decimal import Decimal


class Command(BaseCommand):
    help = 'Import Project Showcases from admin into Project Management system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force import even if project already exists',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force_import = options['force']
        
        self.stdout.write("Importing Project Showcases into Project Management...")
        
        # Get all project showcases
        showcases = ProjectShowcase.objects.all()
        
        if not showcases.exists():
            self.stdout.write(self.style.WARNING("No project showcases found to import."))
            return
        
        imported_count = 0
        skipped_count = 0
        
        with transaction.atomic():
            for showcase in showcases:
                # Check if project already exists
                existing_project = Project.objects.filter(name=showcase.title).first()
                
                if existing_project and not force_import:
                    self.stdout.write(f"Skipped: {showcase.title} (already exists as {existing_project.project_number})")
                    skipped_count += 1
                    continue
                
                # Map project type
                project_type_mapping = {
                    'residential': 'residential',
                    'commercial': 'commercial', 
                    'industrial': 'industrial',
                    'government': 'commercial',  # Map government to commercial
                }
                
                project_type = project_type_mapping.get(showcase.project_type, 'commercial')
                
                # Parse capacity (remove 'kW' and convert to decimal)
                try:
                    capacity_str = showcase.capacity.replace('kW', '').replace('MW', '000').strip()
                    if capacity_str.replace('.', '').isdigit():
                        system_capacity = Decimal(capacity_str)
                    else:
                        system_capacity = Decimal('10.0')  # Default
                except (AttributeError, ValueError):
                    system_capacity = Decimal('10.0')
                
                # Parse location FIRST
                location_parts = showcase.location.split(',')
                city = location_parts[0].strip() if location_parts else 'Nairobi'
                county = location_parts[1].strip() if len(location_parts) > 1 else 'Nairobi'
                
                # Calculate estimated values
                estimated_cost = system_capacity * 150000  # 150,000 KES per kW
                contract_value = estimated_cost * Decimal('1.2')  # 20% markup
                estimated_generation = system_capacity * 130  # 130 kWh per kW per month
                
                # Create or get a default customer
                customer, created = Customer.objects.get_or_create(
                    email=f"client_{showcase.id}@oliviangroup.com",
                    defaults={
                        'name': f'Client for {showcase.title}',
                        'phone': '+254700000000',
                        'address': showcase.location,
                        'city': city,
                        'company_name': f'Client for {showcase.title}',
                        'business_type': 'business' if project_type in ['commercial', 'industrial'] else 'individual',
                        'monthly_consumption': estimated_generation,
                        'average_monthly_bill': 15000,
                        'property_type': 'commercial' if project_type in ['commercial', 'industrial'] else 'residential',
                        'roof_type': 'concrete',
                        'roof_area': float(system_capacity) * 8,
                    }
                )
                
                project_data = {
                    'name': showcase.title,
                    'description': showcase.description or f"Professional {project_type} solar installation.",
                    'project_type': project_type,
                    'status': 'completed',  # Import as completed since they're showcases
                    'client': customer,
                    'system_type': 'grid_tied',  # Default system type
                    'system_capacity': system_capacity,
                    'estimated_generation': estimated_generation,
                    'installation_address': showcase.location,
                    'city': city,
                    'county': county,
                    'contract_value': contract_value,
                    'estimated_cost': estimated_cost,
                    'actual_cost': estimated_cost,
                    'start_date': showcase.completion_date or showcase.created_at.date(),
                    'target_completion': showcase.completion_date or showcase.created_at.date(),
                    'actual_completion': showcase.completion_date,
                    'duration_days': 30,  # Default duration
                    'completion_percentage': 100,  # Completed
                }
                
                if not dry_run:
                    if existing_project and force_import:
                        # Update existing project
                        for key, value in project_data.items():
                            setattr(existing_project, key, value)
                        existing_project.save()
                        self.stdout.write(f"Updated: {showcase.title} → {existing_project.project_number}")
                    else:
                        # Create new project
                        project = Project.objects.create(**project_data)
                        self.stdout.write(f"Imported: {showcase.title} → {project.project_number}")
                    
                    imported_count += 1
                else:
                    self.stdout.write(f"[DRY RUN] Would import: {showcase.title}")
                    imported_count += 1
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\n[DRY RUN] Would import {imported_count} projects and skip {skipped_count}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSuccessfully imported {imported_count} projects and skipped {skipped_count}"
                )
            )
            
        self.stdout.write("\nProject Showcases are now available in Project Management!")
        self.stdout.write("You can view them at: /projects/")
