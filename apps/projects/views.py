from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, UpdateView, CreateView, TemplateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import models
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Project
from .forms import ProjectCreateForm, ProjectUpdateForm


def complete_project(project):
    """Utility function to mark a project as completed"""
    project.status = 'completed'
    project.completion_percentage = 100
    if not project.actual_completion:
        project.actual_completion = timezone.now().date()
    project.save()
    return project

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/list.html'
    context_object_name = 'projects'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        from django.db.models import Sum, Count
        from decimal import Decimal
        
        context = super().get_context_data(**kwargs)
        
        # Calculate real-time statistics (same logic as HomeView and ProjectShowcaseView)
        all_projects = Project.objects.all()
        completed_projects = all_projects.filter(status='completed')
        active_projects = all_projects.filter(status__in=['planning', 'in_progress'])
        
        # Total project value for active and completed projects
        total_value = all_projects.exclude(status='cancelled').aggregate(
            total=Sum('estimated_cost')
        )['total'] or 0
        
        # Total capacity installed (sum of system_capacity for completed projects)
        total_capacity = completed_projects.aggregate(
            total=Sum('system_capacity')
        )['total'] or 0
        
        # Format capacity display based on size
        if total_capacity >= 1000:
            capacity_display = f"{round(total_capacity / 1000, 1)}MW"
        else:
            capacity_display = f"{int(total_capacity)}kW" if total_capacity else "0kW"
        
        context.update({
            'total_projects': all_projects.count(),
            'active_projects': active_projects.count(),
            'completed_projects': completed_projects.count(),
            'total_value': total_value,
            'total_capacity_display': capacity_display,
        })
        
        return context

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectCreateForm
    template_name = 'projects/create.html'
    success_url = reverse_lazy('projects:list')

    def form_valid(self, form):
        # Project number will be auto-generated in the model's save method
        response = super().form_valid(form)
        
        # Handle notification and calendar options
        self.handle_post_creation_actions(form)
        
        return response
    
    def handle_post_creation_actions(self, form):
        """Handle post-creation actions like notifications and calendar events"""
        project = self.object
        request = self.request
        
        # Send notification to project manager if requested and manager is assigned
        if (request.POST.get('send_notification') and 
            project.project_manager and 
            hasattr(project.project_manager, 'email')):
            self.send_project_notification(project)
        
        # Create calendar events if requested (placeholder for future implementation)
        if request.POST.get('create_calendar_event'):
            self.create_calendar_events(project)
    
    def send_project_notification(self, project):
        """Send email notification to project manager"""
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            import logging
            
            logger = logging.getLogger(__name__)
            logger.info(f"Sending project notification to {project.project_manager.email}")
            
            subject = f"New Project Assignment: {project.name}"
            message = f"""Hello {project.project_manager.get_full_name()},

You have been assigned as the project manager for a new project:

Project: {project.name}
Project Number: {project.project_number}
Client: {project.client.name if project.client else 'N/A'}
Start Date: {project.start_date or 'Not set'}
Target Completion: {project.target_completion or 'Not set'}

Project Description:
{project.description or 'No description provided'}

Please log in to the system to view full project details and begin planning.

Project Details: {self.request.build_absolute_uri(project.get_absolute_url())}

Best regards,
The Olivian Group Team
"""
            
            result = send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [project.project_manager.email],
                fail_silently=False,  # Changed to False to catch errors
            )
            
            logger.info(f"Email sent successfully. Result: {result}")
            return True
            
        except Exception as e:
            # Log error but don't fail the form submission
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send project notification: {str(e)}")
            logger.error(f"Project manager email: {project.project_manager.email if project.project_manager else 'None'}")
            return False
    
    def create_calendar_events(self, project):
        """Create calendar events for project timeline"""
        try:
            import logging
            from datetime import datetime, timedelta
            from django.utils import timezone
            
            logger = logging.getLogger(__name__)
            logger.info(f"Creating calendar events for project: {project.name}")
            
            events_created = []
            
            # Create start date event if start_date is set
            if project.start_date:
                start_event = self._create_calendar_event(
                    title=f"Project Start: {project.name}",
                    description=f"Project {project.project_number} begins\n\nDescription: {project.description or 'No description provided'}\n\nClient: {project.client.name if project.client else 'N/A'}",
                    start_date=project.start_date,
                    attendees=[project.project_manager.email] if project.project_manager and hasattr(project.project_manager, 'email') else []
                )
                if start_event:
                    events_created.append(start_event)
            
            # Create target completion event if target_completion is set
            if project.target_completion:
                completion_event = self._create_calendar_event(
                    title=f"Project Target Completion: {project.name}",
                    description=f"Target completion date for project {project.project_number}\n\nDescription: {project.description or 'No description provided'}\n\nClient: {project.client.name if project.client else 'N/A'}",
                    start_date=project.target_completion,
                    attendees=[project.project_manager.email] if project.project_manager and hasattr(project.project_manager, 'email') else []
                )
                if completion_event:
                    events_created.append(completion_event)
            
            # Create milestone reminders if both dates are set
            if project.start_date and project.target_completion:
                self._create_milestone_events(project, events_created)
            
            logger.info(f"Created {len(events_created)} calendar events for project {project.project_number}")
            return events_created
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create calendar events for project {project.project_number}: {str(e)}")
            return []
    
    def _create_calendar_event(self, title, description, start_date, attendees=None):
        """Create individual calendar event using iCal format"""
        try:
            from django.core.mail import EmailMessage
            from django.conf import settings
            import uuid
            from datetime import datetime
            
            # Generate iCal content
            event_uid = str(uuid.uuid4())
            now = datetime.now().strftime('%Y%m%dT%H%M%SZ')
            event_date = start_date.strftime('%Y%m%d') if hasattr(start_date, 'strftime') else start_date
            
            ical_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Olivian Group//Project Calendar//EN
METHOD:REQUEST
BEGIN:VEVENT
UID:{event_uid}
DTSTART;VALUE=DATE:{event_date}
DTEND;VALUE=DATE:{event_date}
DTSTAMP:{now}
SUMMARY:{title}
DESCRIPTION:{description}
ORGANIZER:mailto:{settings.DEFAULT_FROM_EMAIL}
STATUS:CONFIRMED
TRANSP:TRANSPARENT
END:VEVENT
END:VCALENDAR"""
            
            # Send calendar invite via email if attendees are specified
            if attendees:
                for attendee_email in attendees:
                    if attendee_email:
                        email = EmailMessage(
                            subject=f"Calendar Invite: {title}",
                            body=f"Please find the calendar invitation attached.\n\n{description}",
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            to=[attendee_email],
                        )
                        email.attach(f"event_{event_uid}.ics", ical_content, "text/calendar")
                        email.send()
            
            return {
                'uid': event_uid,
                'title': title,
                'date': start_date,
                'ical_content': ical_content
            }
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create individual calendar event: {str(e)}")
            return None
    
    def _create_milestone_events(self, project, events_created):
        """Create milestone reminder events"""
        try:
            from datetime import timedelta
            
            # Calculate project duration and milestones
            duration = (project.target_completion - project.start_date).days
            
            # Create milestone events for longer projects
            if duration > 30:  # Only for projects longer than 30 days
                # 25% milestone
                milestone_25 = project.start_date + timedelta(days=int(duration * 0.25))
                event_25 = self._create_calendar_event(
                    title=f"Project Milestone (25%): {project.name}",
                    description=f"25% milestone checkpoint for project {project.project_number}",
                    start_date=milestone_25,
                    attendees=[project.project_manager.email] if project.project_manager and hasattr(project.project_manager, 'email') else []
                )
                if event_25:
                    events_created.append(event_25)
                
                # 50% milestone
                milestone_50 = project.start_date + timedelta(days=int(duration * 0.50))
                event_50 = self._create_calendar_event(
                    title=f"Project Milestone (50%): {project.name}",
                    description=f"50% milestone checkpoint for project {project.project_number}",
                    start_date=milestone_50,
                    attendees=[project.project_manager.email] if project.project_manager and hasattr(project.project_manager, 'email') else []
                )
                if event_50:
                    events_created.append(event_50)
                
                # 75% milestone
                milestone_75 = project.start_date + timedelta(days=int(duration * 0.75))
                event_75 = self._create_calendar_event(
                    title=f"Project Milestone (75%): {project.name}",
                    description=f"75% milestone checkpoint for project {project.project_number}",
                    start_date=milestone_75,
                    attendees=[project.project_manager.email] if project.project_manager and hasattr(project.project_manager, 'email') else []
                )
                if event_75:
                    events_created.append(event_75)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create milestone events: {str(e)}")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.quotations.models import Customer
        from apps.accounts.models import User
        
        context['customers'] = Customer.objects.all().order_by('name')
        context['project_managers'] = User.objects.filter(role__in=['manager', 'project_manager']).order_by('first_name')
        
        return context

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/detail.html'
    context_object_name = 'project'
    slug_field = 'project_number'
    slug_url_kwarg = 'project_number'

class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectUpdateForm
    template_name = 'projects/update.html'
    slug_field = 'project_number'
    slug_url_kwarg = 'project_number'
    
    def get_success_url(self):
        return reverse_lazy('projects:detail', kwargs={'project_number': self.object.project_number})
    
    def form_valid(self, form):
        """Handle form submission with debugging for image upload"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Debug: Check what's in the form
        logger.info(f"ProjectUpdateView.form_valid called")
        logger.info(f"Form is valid: {form.is_valid()}")
        logger.info(f"Form cleaned_data keys: {list(form.cleaned_data.keys())}")
        
        if 'featured_image' in form.cleaned_data:
            image = form.cleaned_data['featured_image']
            logger.info(f"Featured image: {image}")
            if image:
                logger.info(f"Image name: {image.name}")
                logger.info(f"Image size: {image.size}")

        response = super().form_valid(form)
        
        # Debug: Check if image was saved
        logger.info(f"Project after save - featured_image: {self.object.featured_image}")
        if self.object.featured_image:
            logger.info(f"Image name: {self.object.featured_image.name}")
            logger.info(f"Image URL: {self.object.featured_image.url}")
        
        return response
    
    def form_invalid(self, form):
        """Handle invalid form submission"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.error(f"ProjectUpdateView.form_invalid called")
        logger.error(f"Form errors: {form.errors}")
        
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.quotations.models import Customer
        from apps.accounts.models import User
        
        context['customers'] = Customer.objects.all().order_by('name')
        context['project_managers'] = User.objects.filter(role__in=['manager', 'project_manager']).order_by('first_name')
        context['technicians'] = User.objects.filter(role='technician').order_by('first_name')
        
        return context

class ProjectShowcaseView(TemplateView):
    template_name = 'projects/showcase.html'

    def get_context_data(self, **kwargs):
        from django.db.models import Sum, Count

        context = super().get_context_data(**kwargs)

        # Get completed projects for showcase
        completed_projects = Project.objects.filter(status='completed').select_related('client').prefetch_related('documents')
        context['projects'] = completed_projects[:12]

        # Calculate statistics
        all_projects = Project.objects.all()
        completed_count = completed_projects.count()

        # Total capacity installed (sum of system_capacity for completed projects)
        total_capacity = completed_projects.aggregate(
            total=Sum('system_capacity')
        )['total'] or 0

        # Estimate CO2 saved (roughly 0.8 kg CO2 per kWh, assume 1500 kWh per kW per year)
        from decimal import Decimal
        annual_generation = total_capacity * Decimal('1500')  # kWh per year
        co2_saved = (annual_generation * Decimal('0.8')) / Decimal('1000')  # Convert to tons

        # Count unique cities
        cities_count = completed_projects.values('city').distinct().count()

        # Format capacity display based on size
        if total_capacity >= 1000:
            capacity_display = f"{round(total_capacity / 1000, 1)}MW"
        else:
            capacity_display = f"{int(total_capacity)}kW" if total_capacity else "0kW"

        context.update({
            'stats': {
                'projects_completed': completed_count,
                'total_capacity_display': capacity_display,
                'co2_saved_tons': round(co2_saved, 1) if co2_saved else 0,
                'cities_served': cities_count,
            },
            'project_types': Project.PROJECT_TYPES,
            'featured_projects': completed_projects.filter(
                models.Q(system_capacity__gte=10) |  # Large systems
                models.Q(project_type='commercial') |  # Commercial projects
                models.Q(project_type='industrial')   # Industrial projects
            )[:6]
        })

        return context

class ProjectShowcaseDetailView(DetailView):
    """Public view for project showcase details - no login required"""
    model = Project
    template_name = 'projects/showcase_detail.html'
    context_object_name = 'project'
    slug_field = 'project_number'
    slug_url_kwarg = 'project_number'

    def get_queryset(self):
        # Only show completed projects publicly
        return Project.objects.filter(status='completed').select_related('client')

    def get_context_data(self, **kwargs):
        from decimal import Decimal
        context = super().get_context_data(**kwargs)
        project = self.object

        # Calculate environmental impact
        if project.estimated_generation:
            # Rough calculation: 0.8 kg CO2 per kWh
            annual_co2_saved = (project.estimated_generation * Decimal('0.8')) / Decimal('1000')  # tons per year
            context['annual_co2_saved'] = round(float(annual_co2_saved), 1)
            # 25 year lifespan estimate
            context['total_co2_saved'] = round(float(annual_co2_saved * Decimal('25')), 1)

        # Calculate payback period estimate (rough: KES 25 per kWh saved)
        if project.estimated_generation and project.contract_value:
            monthly_savings = project.estimated_generation * Decimal('25')  # KES per month
            if monthly_savings > 0:
                yearly_savings = monthly_savings * Decimal('12')
                context['estimated_payback_years'] = round(float(project.contract_value / yearly_savings), 1)

        # Get project photos for gallery
        context['project_photos'] = project.documents.filter(document_type='photo').select_related('uploaded_by')

        # Get similar projects
        similar_projects = Project.objects.filter(
            status='completed',
            project_type=project.project_type
        ).exclude(id=project.id)[:3]
        context['similar_projects'] = similar_projects

        return context

class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    slug_field = 'project_number'
    slug_url_kwarg = 'project_number'
    success_url = reverse_lazy('projects:list')
    template_name = 'projects/confirm_delete.html'

class ProjectDeleteAPIView(LoginRequiredMixin, View):
    """API endpoint for deleting projects via AJAX"""
    
    def delete(self, request, project_id):
        try:
            project = get_object_or_404(Project, id=project_id)
            
            # Check permissions (only super admin, manager, or project owner can delete)
            if not (request.user.role in ['super_admin', 'manager'] or 
                   request.user == project.project_manager):
                return JsonResponse({
                    'success': False, 
                    'message': 'You do not have permission to delete this project.'
                }, status=403)
            
            project_name = project.name
            project.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Project "{project_name}" was deleted successfully.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting project: {str(e)}'
            }, status=500)

class ProjectCompleteAPIView(LoginRequiredMixin, View):
    """API endpoint for marking projects as completed via AJAX"""

    def post(self, request, project_id):
        try:
            project = get_object_or_404(Project, id=project_id)
            
            # Check permissions (only super admin, manager, or project owner can complete)
            if not (request.user.role in ['super_admin', 'manager', 'project_manager'] or 
                   request.user == project.project_manager):
                return JsonResponse({
                    'success': False, 
                    'message': 'You do not have permission to complete this project.'
                }, status=403)
            
            # Mark as completed using utility function
            complete_project(project)
            
            return JsonResponse({
                'success': True,
                'message': f'Project "{project.name}" has been marked as completed successfully.',
                'status': project.status,
                'completion_percentage': project.completion_percentage
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error completing project: {str(e)}'
            }, status=500)

def import_showcases_view(request):
    """Import Project Showcases into Project Management system"""
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Import showcases called with method: {request.method}")
    
    # Only allow POST requests
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': f'Only POST method allowed. Received: {request.method}'
        }, status=405)
    
    # Check authentication
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required.'
        }, status=401)
    
    # Only allow super admin and managers to import
    if not request.user.role in ['super_admin', 'manager']:
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to import projects.'
        }, status=403)
    
    try:
        from apps.core.models import ProjectShowcase
        from apps.quotations.models import Customer
        from decimal import Decimal
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Get all project showcases that haven't been imported yet
        showcases = ProjectShowcase.objects.all()
        imported_count = 0
        skipped_count = 0
        
        for showcase in showcases:
            # Check if project already exists
            existing_project = Project.objects.filter(name=showcase.title).first()
            
            if existing_project:
                skipped_count += 1
                continue
            
            # Map project type
            project_type_mapping = {
                'residential': 'residential',
                'commercial': 'commercial', 
                'industrial': 'industrial',
                'government': 'commercial',
            }
            
            project_type = project_type_mapping.get(showcase.project_type, 'commercial')
            
            # Parse capacity
            try:
                capacity_str = showcase.capacity.replace('kW', '').replace('MW', '000').strip()
                if capacity_str.replace('.', '').isdigit():
                    system_capacity = Decimal(capacity_str)
                else:
                    system_capacity = Decimal('10.0')
            except (AttributeError, ValueError):
                system_capacity = Decimal('10.0')
            
            # Parse location FIRST (before using city variable)
            location_parts = showcase.location.split(',')
            city = location_parts[0].strip() if location_parts else 'Nairobi'
            county = location_parts[1].strip() if len(location_parts) > 1 else 'Nairobi'
            
            # Calculate values
            estimated_cost = system_capacity * 150000
            contract_value = estimated_cost * Decimal('1.2')
            estimated_generation = system_capacity * 130
            
            # Create or get customer
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
                    'average_monthly_bill': 15000,  # Default bill
                    'property_type': 'commercial' if project_type in ['commercial', 'industrial'] else 'residential',
                    'roof_type': 'concrete',
                    'roof_area': float(system_capacity) * 8,  # Estimate 8 sqm per kW
                }
            )
            
            # Create project
            Project.objects.create(
                name=showcase.title,
                description=showcase.description or f"Professional {project_type} solar installation.",
                project_type=project_type,
                status='completed',
                client=customer,
                system_type='grid_tied',
                system_capacity=system_capacity,
                estimated_generation=estimated_generation,
                installation_address=showcase.location,
                city=city,
                county=county,
                contract_value=contract_value,
                estimated_cost=estimated_cost,
                actual_cost=estimated_cost,
                start_date=showcase.completion_date or showcase.created_at.date(),
                target_completion=showcase.completion_date or showcase.created_at.date(),
                actual_completion=showcase.completion_date,
                duration_days=30,
                completion_percentage=100,
            )
            
            imported_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully imported {imported_count} projects. Skipped {skipped_count} existing projects.',
            'imported': imported_count,
            'skipped': skipped_count
        })
        
    except Exception as e:
        logger.error(f"Error importing showcases: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error importing projects: {str(e)}'
        }, status=500)
