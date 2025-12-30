from django.db import models
from django.utils import timezone
from decimal import Decimal
from apps.core.models import TimeStampedModel

class Budget(TimeStampedModel):
    BUDGET_TYPES = [
        ('project', 'Project Budget'),
        ('department', 'Department Budget'),
        ('annual', 'Annual Budget'),
        ('quarterly', 'Quarterly Budget'),
        ('monthly', 'Monthly Budget'),
        ('operational', 'Operational Budget'),
        ('capital', 'Capital Budget'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200)
    description = models.TextField()
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Financial Information
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    spent_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    committed_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    available_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Period Information
    period_start = models.DateField()
    period_end = models.DateField()
    fiscal_year = models.IntegerField()
    
    # Organizational Information
    department = models.CharField(max_length=100, blank=True)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, null=True, blank=True)
    owner = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='owned_budgets')
    
    # Approval Information
    requires_approval = models.BooleanField(default=True)
    approval_threshold = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Notifications
    alert_threshold_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=80.0)
    email_notifications = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['budget_type', 'status']),
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['department', 'fiscal_year']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.fiscal_year:
            self.fiscal_year = self.period_start.year
        
        # Calculate available amount
        self.available_amount = self.total_amount - self.allocated_amount - self.committed_amount
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.period_start.year})"
    
    @property
    def utilization_percentage(self):
        """Calculate budget utilization percentage"""
        if self.total_amount == 0:
            return 0
        return (self.spent_amount / self.total_amount) * 100
    
    @property
    def allocation_percentage(self):
        """Calculate budget allocation percentage"""
        if self.total_amount == 0:
            return 0
        return (self.allocated_amount / self.total_amount) * 100
    
    def is_over_budget(self):
        return self.spent_amount > self.total_amount
    
    def is_approaching_limit(self):
        return self.utilization_percentage >= self.alert_threshold_percentage
    
    def get_variance(self):
        """Calculate budget variance"""
        return self.total_amount - self.spent_amount
    
    def update_amounts(self):
        """Update spent and allocated amounts based on categories"""
        categories = self.categories.all()
        self.spent_amount = sum(cat.spent_amount for cat in categories)
        self.allocated_amount = sum(cat.allocated_amount for cat in categories)
        self.save()

class BudgetCategory(TimeStampedModel):
    CATEGORY_TYPES = [
        ('materials', 'Materials'),
        ('labor', 'Labor'),
        ('equipment', 'Equipment'),
        ('transportation', 'Transportation'),
        ('overhead', 'Overhead'),
        ('marketing', 'Marketing'),
        ('administrative', 'Administrative'),
        ('utilities', 'Utilities'),
        ('insurance', 'Insurance'),
        ('permits', 'Permits & Licenses'),
        ('professional_services', 'Professional Services'),
        ('training', 'Training'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other'),
    ]
    
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=30, choices=CATEGORY_TYPES)
    description = models.TextField(blank=True)
    
    # Financial Information
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    committed_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Controls
    is_active = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    approval_threshold = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ('budget', 'name')
    
    def __str__(self):
        return f"{self.budget.name} - {self.name}"
    
    @property
    def available_amount(self):
        return self.allocated_amount - self.spent_amount - self.committed_amount
    
    @property
    def utilization_percentage(self):
        if self.allocated_amount == 0:
            return 0
        return (self.spent_amount / self.allocated_amount) * 100
    
    def is_over_budget(self):
        return self.spent_amount > self.allocated_amount
    
    def can_spend(self, amount):
        return self.available_amount >= amount

class BudgetApproval(TimeStampedModel):
    APPROVAL_LEVELS = [
        (1, 'Manager'),
        (2, 'Director'),
        (3, 'CEO'),
        (4, 'Board'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('escalated', 'Escalated'),
    ]
    
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    approval_level = models.IntegerField(choices=APPROVAL_LEVELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(blank=True)
    approved_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    decision_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['approval_level']
        unique_together = ('budget', 'approval_level')
    
    def __str__(self):
        return f"{self.budget.name} - Level {self.approval_level} Approval"

class BudgetRevision(TimeStampedModel):
    REVISION_TYPES = [
        ('increase', 'Budget Increase'),
        ('decrease', 'Budget Decrease'),
        ('reallocation', 'Budget Reallocation'),
        ('extension', 'Period Extension'),
    ]
    
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='revisions')
    revision_type = models.CharField(max_length=20, choices=REVISION_TYPES)
    reason = models.TextField()
    
    # Previous values
    previous_amount = models.DecimalField(max_digits=15, decimal_places=2)
    new_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Dates
    previous_end_date = models.DateField(null=True, blank=True)
    new_end_date = models.DateField(null=True, blank=True)
    
    # Approval
    requested_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='budget_revisions')
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    approved = models.BooleanField(default=False)
    approved_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.budget.name} - {self.get_revision_type_display()}"

class ExpenseRequest(TimeStampedModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    EXPENSE_TYPES = [
        ('project_expense', 'Project Expense'),
        ('operational_expense', 'Operational Expense'),
        ('capital_expense', 'Capital Expense'),
        ('emergency_expense', 'Emergency Expense'),
    ]
    
    # Request Information
    request_number = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Financial Information
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Budget Allocation
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE)
    budget_category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE)
    
    # Project Association (if applicable)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, null=True, blank=True)
    
    # Requestor Information
    requested_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='expense_requests')
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Vendor Information
    vendor_name = models.CharField(max_length=200, blank=True)
    vendor_contact = models.CharField(max_length=200, blank=True)
    
    # Supporting Documents
    supporting_documents = models.FileField(upload_to='expense_requests/', blank=True, null=True)
    receipt = models.FileField(upload_to='expense_receipts/', blank=True, null=True)
    
    # Important Dates
    required_date = models.DateField()
    approved_date = models.DateTimeField(null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.request_number:
            year = timezone.now().year
            count = ExpenseRequest.objects.filter(created_at__year=year).count() + 1
            self.request_number = f"OG-EXP-{year}-{count:04d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.request_number} - {self.title}"
    
    def can_approve(self, user):
        """Check if user can approve this expense request"""
        # Implement approval logic based on amount and user role
        if user.role in ['manager', 'super_admin']:
            return True
        if user.role == 'project_manager' and self.project and self.project.project_manager == user:
            return self.requested_amount <= 50000  # KES 50,000 limit for project managers
        return False

class PaymentSchedule(TimeStampedModel):
    """Payment schedule for projects and contracts"""
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='payment_schedule')
    milestone = models.ForeignKey('projects.ProjectMilestone', on_delete=models.CASCADE, null=True, blank=True)
    
    # Payment Information
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage of total contract value")
    
    # Schedule
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    
    # Status
    is_paid = models.BooleanField(default=False)
    invoice_number = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Budget Tracking
    budget_category = models.ForeignKey(BudgetCategory, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['due_date']
    
    def __str__(self):
        return f"{self.project.project_number} - {self.description}"
    
    def is_overdue(self):
        return not self.is_paid and timezone.now().date() > self.due_date

class BudgetReport(TimeStampedModel):
    """Budget reports and analytics"""
    REPORT_TYPES = [
        ('monthly', 'Monthly Report'),
        ('quarterly', 'Quarterly Report'),
        ('annual', 'Annual Report'),
        ('project', 'Project Report'),
        ('variance', 'Variance Report'),
    ]
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Scope
    budgets = models.ManyToManyField(Budget, related_name='reports')
    departments = models.JSONField(default=list, blank=True)
    
    # Report Data
    report_data = models.JSONField(default=dict)
    summary = models.TextField(blank=True)
    
    # Generated Report
    report_file = models.FileField(upload_to='budget_reports/', blank=True, null=True)
    generated_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.name} - {self.period_start} to {self.period_end}"
