from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel
from decimal import Decimal
import os


def project_image_upload_path(instance, filename):
    """Generate upload path for project images"""
    # Get file extension
    ext = filename.split('.')[-1]
    # Create filename using project number
    filename = f"{instance.project_number or 'temp'}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    # Use forward slashes for Django (not os.path.join which uses OS-specific separators)
    return f'project_images/{filename}'

class ProjectSequence(models.Model):
    """Model to track project sequence numbers"""
    year = models.IntegerField(unique=True)
    last_number = models.IntegerField(default=0)
    
    @classmethod
    def get_next_number(cls, year=None):
        if year is None:
            year = timezone.now().year
        
        sequence, created = cls.objects.get_or_create(year=year, defaults={'last_number': 0})
        sequence.last_number += 1
        sequence.save()
        return f"OG-PRJ-{year}-{sequence.last_number:04d}"

class Project(TimeStampedModel):
    PROJECT_TYPES = [
        ('residential', 'Residential Installation'),
        ('commercial', 'Commercial Installation'),
        ('industrial', 'Industrial Installation'),
        ('utility', 'Utility Scale'),
        ('maintenance', 'Maintenance Project'),
        ('consultation', 'Consultation'),
    ]
    
    STATUS_CHOICES = [
        ('lead', 'Lead'),
        ('quoted', 'Quoted'),
        ('approved', 'Approved'),
        ('planning', 'Planning'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('testing', 'Testing & Commissioning'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Basic Information
    project_number = models.CharField(max_length=20, unique=True, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lead')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Client Information
    client = models.ForeignKey('quotations.Customer', on_delete=models.CASCADE, related_name='projects')
    quotation = models.ForeignKey('quotations.Quotation', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Team Assignment
    project_manager = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='managed_projects'
    )
    installation_team = models.ManyToManyField(
        'accounts.User', 
        related_name='installation_projects',
        blank=True
    )
    salesperson = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='sales_projects'
    )
    
    # System Details
    system_type = models.CharField(
        max_length=20,
        choices=[
            ('grid_tied', 'Grid-Tied System'),
            ('off_grid', 'Off-Grid System'),
            ('hybrid', 'Hybrid System'),
            ('backup', 'Backup Power System'),
        ]
    )
    system_capacity = models.DecimalField(max_digits=8, decimal_places=2, help_text="kW")
    estimated_generation = models.DecimalField(max_digits=10, decimal_places=2, help_text="kWh per month")
    
    # Location Details
    installation_address = models.TextField()
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    site_access_notes = models.TextField(blank=True)
    
    # Financial Information
    contract_value = models.DecimalField(max_digits=12, decimal_places=2)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Timeline
    start_date = models.DateField()
    target_completion = models.DateField()
    actual_completion = models.DateField(null=True, blank=True)
    duration_days = models.IntegerField(help_text="Estimated duration in days")
    
    # Progress Tracking
    completion_percentage = models.IntegerField(default=0)
    
    # Quality and Safety
    safety_requirements = models.TextField(blank=True)
    quality_standards = models.TextField(blank=True)
    permits_required = models.JSONField(default=list, blank=True)
    
    # Documentation
    site_survey_report = models.FileField(upload_to='project_documents/', blank=True, null=True)
    installation_drawings = models.FileField(upload_to='project_documents/', blank=True, null=True)
    completion_certificate = models.FileField(upload_to='project_documents/', blank=True, null=True)
    
    # Project Images
    featured_image = models.ImageField(
        upload_to=project_image_upload_path, 
        blank=True,
        null=True, 
        help_text="Main project image displayed on website"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project_number']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['project_manager', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.project_number:
            self.project_number = ProjectSequence.get_next_number()
        
        # Calculate profit margin
        if self.contract_value and self.estimated_cost:
            profit = self.contract_value - self.estimated_cost
            self.profit_margin = (profit / self.contract_value) * 100
        
        # Auto-mark as completed if completion percentage is 100%
        if self.completion_percentage >= 100 and self.status not in ['completed', 'cancelled']:
            self.status = 'completed'
            if not self.actual_completion:
                self.actual_completion = timezone.now().date()
        
        # Auto-start project if start date has passed and still in lead status
        elif (self.start_date and self.start_date <= timezone.now().date() and 
              self.status == 'lead'):
            self.status = 'planning'
        
        # Auto-set to in_progress if project has started work
        elif (self.start_date and self.start_date <= timezone.now().date() and 
              self.status in ['planning'] and self.completion_percentage > 0):
            self.status = 'in_progress'
        
        # Check if status changed to completed
        is_new = self.pk is None
        old_status = None
        if not is_new:
            old_instance = Project.objects.get(pk=self.pk)
            old_status = old_instance.status
        
        super().save(*args, **kwargs)
        
        # Auto-sync to showcase when completed
        if self.status == 'completed' and old_status != 'completed':
            self.sync_to_showcase()
    
    def __str__(self):
        return f"{self.project_number} - {self.name}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('projects:detail', kwargs={'project_number': self.project_number})
    
    def get_budget_utilization(self):
        """Calculate budget utilization percentage"""
        if self.estimated_cost == 0:
            return 0
        return (self.actual_cost / self.estimated_cost) * 100
    
    def is_over_budget(self):
        return self.actual_cost > self.estimated_cost
    
    def is_behind_schedule(self):
        if self.status == 'completed':
            return self.actual_completion > self.target_completion
        return timezone.now().date() > self.target_completion
    
    def update_completion_percentage(self):
        """Calculate completion percentage based on completed tasks"""
        tasks = self.tasks.all()
        if not tasks:
            return 0
        
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status='completed').count()
        self.completion_percentage = int((completed_tasks / total_tasks) * 100)
        self.save()
        return self.completion_percentage
    
    def mark_as_completed(self):
        """Mark project as completed with 100% completion"""
        self.status = 'completed'
        self.completion_percentage = 100
        if not self.actual_completion:
            self.actual_completion = timezone.now().date()
        self.save()
    
    def start_project(self):
        """Start the project - change status from lead to planning"""
        if self.status == 'lead':
            self.status = 'planning'
            self.save()
    
    def begin_work(self):
        """Begin project work - change status to in_progress"""
        if self.status in ['lead', 'planning']:
            self.status = 'in_progress'
            self.save()
    
    def sync_to_showcase(self):
        """Sync completed project to project showcase for homepage display"""
        if self.status != 'completed':
            return
            
        from apps.core.models import ProjectShowcase
        
        # Map project type
        project_type_mapping = {
            'residential': 'residential',
            'commercial': 'commercial', 
            'industrial': 'industrial',
            'utility': 'commercial',
            'maintenance': 'commercial',
            'consultation': 'commercial',
        }
        
        showcase_type = project_type_mapping.get(self.project_type, 'commercial')
        
        # Create location string
        location = f"{self.city}, {self.county}" if self.city and self.county else self.city or self.county or 'Kenya'
        
        # Format capacity
        capacity = f"{int(self.system_capacity)}kW" if self.system_capacity else "TBD"
        
        # Update or create showcase
        showcase, created = ProjectShowcase.objects.update_or_create(
            title=self.name,
            defaults={
                'description': self.description or f"Professional {self.get_project_type_display().lower()} solar installation providing clean energy solutions.",
                'location': location,
                'capacity': capacity,
                'project_type': showcase_type,
                'completion_date': self.actual_completion or self.target_completion,
                'is_featured': True,
                'order': 0,
            }
        )
        
        return showcase

class ProjectTask(TimeStampedModel):
    TASK_TYPES = [
        ('site_survey', 'Site Survey'),
        ('design', 'System Design'),
        ('permits', 'Permits & Approvals'),
        ('procurement', 'Equipment Procurement'),
        ('delivery', 'Equipment Delivery'),
        ('installation', 'Installation'),
        ('electrical', 'Electrical Work'),
        ('testing', 'Testing & Commissioning'),
        ('documentation', 'Documentation'),
        ('training', 'Customer Training'),
        ('handover', 'Project Handover'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField()
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Assignment
    assigned_to = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    assigned_team = models.ManyToManyField('accounts.User', related_name='team_tasks', blank=True)
    
    # Timeline
    start_date = models.DateField()
    due_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    # Progress
    completion_percentage = models.IntegerField(default=0)
    
    # Dependencies
    dependencies = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    # Additional Information
    notes = models.TextField(blank=True)
    attachments = models.FileField(upload_to='task_attachments/', blank=True, null=True)
    
    class Meta:
        ordering = ['start_date', 'due_date']
    
    def __str__(self):
        return f"{self.project.project_number} - {self.title}"
    
    def is_overdue(self):
        if self.status == 'completed':
            return self.completion_date > self.due_date
        return timezone.now().date() > self.due_date
    
    def can_start(self):
        """Check if task can start based on dependencies"""
        return all(dep.status == 'completed' for dep in self.dependencies.all())

class ProjectExpense(TimeStampedModel):
    EXPENSE_CATEGORIES = [
        ('materials', 'Materials'),
        ('equipment', 'Equipment'),
        ('labor', 'Labor'),
        ('transport', 'Transportation'),
        ('permits', 'Permits & Licenses'),
        ('subcontractor', 'Subcontractor'),
        ('overhead', 'Overhead'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(max_length=20, choices=EXPENSE_CATEGORIES)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    supplier = models.CharField(max_length=100, blank=True)
    invoice_number = models.CharField(max_length=50, blank=True)
    receipt = models.FileField(upload_to='project_receipts/', blank=True, null=True)
    
    # Approval
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Budget tracking
    budget_category = models.ForeignKey('budget.BudgetCategory', on_delete=models.SET_NULL, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update project actual cost
        self.project.actual_cost = self.project.expenses.filter(approved=True).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        self.project.save()
    
    def __str__(self):
        return f"{self.project.project_number} - {self.description}"

class ProjectMilestone(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField()
    target_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('delayed', 'Delayed'),
        ],
        default='pending'
    )
    payment_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['target_date']
    
    def __str__(self):
        return f"{self.project.project_number} - {self.title}"
    
    def is_delayed(self):
        if self.status == 'completed':
            return self.actual_date > self.target_date
        return timezone.now().date() > self.target_date

class ProjectDocument(TimeStampedModel):
    DOCUMENT_TYPES = [
        ('contract', 'Contract'),
        ('site_survey', 'Site Survey'),
        ('design', 'System Design'),
        ('permit', 'Permit'),
        ('invoice', 'Invoice'),
        ('receipt', 'Receipt'),
        ('photo', 'Progress Photo'),
        ('report', 'Report'),
        ('certificate', 'Certificate'),
        ('warranty', 'Warranty'),
        ('manual', 'User Manual'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='project_documents/')
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False, help_text="Visible to client")
    
    def __str__(self):
        return f"{self.project.project_number} - {self.title}"

class ProjectUpdate(TimeStampedModel):
    """Progress updates and communications"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='updates')
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    is_internal = models.BooleanField(default=False, help_text="Internal update, not shared with client")
    
    # Attachments
    photos = models.FileField(upload_to='project_updates/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.project.project_number} - {self.title}"
