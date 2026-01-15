from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    LeadSource, Contact, Company, Lead, Opportunity,
    Activity, Campaign, Pipeline, PipelineStage,
    EmailTemplate, EmailLog, Document, LeadScore, Workflow, WorkflowStep
)


@admin.register(LeadSource)
class LeadSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
    )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'email', 'phone', 'position', 'city', 'created_at']
    list_filter = ['title', 'city', 'county', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'mobile', 'position']
    ordering = ['last_name', 'first_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('title', 'first_name', 'last_name', 'email', 'phone', 'mobile', 'position')
        }),
        ('Address', {
            'fields': ('address_line_1', 'address_line_2', 'city', 'county', 'postal_code'),
            'classes': ('collapse',)
        }),
        ('Professional', {
            'fields': ('linkedin_url', 'notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'last_name'


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'company_type', 'city', 'primary_contact', 'employee_count', 'created_at']
    list_filter = ['company_type', 'city', 'county', 'industry', 'created_at']
    search_fields = ['name', 'registration_number', 'tax_number', 'email', 'phone']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['contacts']
    
    fieldsets = (
        ('Company Information', {
            'fields': ('name', 'company_type', 'registration_number', 'tax_number')
        }),
        ('Contact Details', {
            'fields': ('email', 'phone', 'website', 'primary_contact')
        }),
        ('Address', {
            'fields': ('address_line_1', 'address_line_2', 'city', 'county', 'postal_code'),
            'classes': ('collapse',)
        }),
        ('Business Details', {
            'fields': ('industry', 'annual_revenue', 'employee_count'),
            'classes': ('collapse',)
        }),
        ('Relationships', {
            'fields': ('contacts',),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class ActivityInline(admin.TabularInline):
    model = Activity
    extra = 0
    fields = ['subject', 'activity_type', 'status', 'scheduled_datetime', 'assigned_to']
    readonly_fields = ['created_at']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'contact', 'company', 'status', 'priority', 'estimated_value', 
        'assigned_to', 'next_follow_up', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'system_type', 'source', 'assigned_to', 
        'created_at', 'next_follow_up'
    ]
    search_fields = ['title', 'contact__first_name', 'contact__last_name', 'company__name', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'days_since_created']
    inlines = [ActivityInline]
    
    fieldsets = (
        ('Lead Information', {
            'fields': ('title', 'contact', 'company', 'status', 'priority', 'source')
        }),
        ('Solar Project Details', {
            'fields': ('system_type', 'estimated_capacity', 'estimated_value', 'monthly_electricity_bill'),
            'classes': ('collapse',)
        }),
        ('Timeline', {
            'fields': ('expected_close_date', 'last_contact_date', 'next_follow_up')
        }),
        ('Assignment', {
            'fields': ('assigned_to',)
        }),
        ('Details', {
            'fields': ('description', 'notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'days_since_created'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('contact', 'company', 'assigned_to', 'source')
    
    actions = ['mark_as_qualified', 'assign_to_me']
    
    def mark_as_qualified(self, request, queryset):
        updated = queryset.update(status='qualified')
        self.message_user(request, f'{updated} leads marked as qualified.')
    mark_as_qualified.short_description = 'Mark selected leads as qualified'
    
    def assign_to_me(self, request, queryset):
        updated = queryset.update(assigned_to=request.user)
        self.message_user(request, f'{updated} leads assigned to you.')
    assign_to_me.short_description = 'Assign selected leads to me'


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'contact', 'company', 'stage', 'probability', 'value', 
        'weighted_value', 'expected_close_date', 'assigned_to'
    ]
    list_filter = ['stage', 'probability', 'assigned_to', 'expected_close_date', 'created_at']
    search_fields = ['name', 'contact__first_name', 'contact__last_name', 'company__name', 'description']
    ordering = ['-value', 'expected_close_date']
    readonly_fields = ['created_at', 'updated_at', 'weighted_value', 'is_overdue']
    inlines = [ActivityInline]
    
    fieldsets = (
        ('Opportunity Information', {
            'fields': ('name', 'lead', 'contact', 'company')
        }),
        ('Sales Details', {
            'fields': ('stage', 'probability', 'value', 'weighted_value')
        }),
        ('Timeline', {
            'fields': ('expected_close_date', 'actual_close_date', 'is_overdue')
        }),
        ('Assignment', {
            'fields': ('assigned_to',)
        }),
        ('Details', {
            'fields': ('description', 'next_steps', 'competition'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def weighted_value(self, obj):
        return f"KES {obj.weighted_value:,.0f}"
    weighted_value.short_description = 'Weighted Value'


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = [
        'subject', 'activity_type', 'status', 'contact', 'scheduled_datetime', 
        'assigned_to', 'created_at'
    ]
    list_filter = [
        'activity_type', 'status', 'assigned_to', 'scheduled_datetime', 'created_at'
    ]
    search_fields = ['subject', 'contact__first_name', 'contact__last_name', 'description']
    ordering = ['scheduled_datetime']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Activity Information', {
            'fields': ('subject', 'activity_type', 'status')
        }),
        ('Relationships', {
            'fields': ('lead', 'opportunity', 'contact')
        }),
        ('Timing', {
            'fields': ('scheduled_datetime', 'duration_minutes', 'completed_datetime')
        }),
        ('Assignment', {
            'fields': ('assigned_to',)
        }),
        ('Details', {
            'fields': ('description', 'outcome', 'next_steps'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'campaign_type', 'status', 'start_date', 'end_date', 
        'budget', 'target_leads', 'owner'
    ]
    list_filter = ['campaign_type', 'status', 'start_date', 'owner', 'created_at']
    search_fields = ['name', 'description', 'message']
    ordering = ['-start_date']
    readonly_fields = ['created_at', 'updated_at', 'actual_leads', 'lead_conversion_rate']
    
    fieldsets = (
        ('Campaign Information', {
            'fields': ('name', 'campaign_type', 'status')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Budget & Targets', {
            'fields': ('budget', 'target_leads', 'target_revenue')
        }),
        ('Content', {
            'fields': ('description', 'message', 'landing_page_url'),
            'classes': ('collapse',)
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Performance', {
            'fields': ('actual_leads', 'lead_conversion_rate'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class PipelineStageInline(admin.TabularInline):
    model = PipelineStage
    extra = 0
    fields = ['name', 'order', 'probability', 'is_closed', 'is_won']
    ordering = ['order']


@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'is_active', 'created_at']
    list_filter = ['is_default', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PipelineStageInline]
    
    fieldsets = (
        ('Pipeline Information', {
            'fields': ('name', 'description')
        }),
        ('Settings', {
            'fields': ('is_default', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ['pipeline', 'name', 'order', 'probability', 'is_closed', 'is_won']
    list_filter = ['pipeline', 'is_closed', 'is_won']
    search_fields = ['name', 'pipeline__name']
    ordering = ['pipeline', 'order']


# New Model Admin Registrations
@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'template_type', 'created_by', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at', 'template_type']
    search_fields = ['name', 'subject', 'body']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'template_type', 'subject', 'body')
        }),
        ('Settings', {
            'fields': ('is_active', 'created_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'subject', 'status', 'template', 'sent_at', 'opened_at']
    list_filter = ['status', 'sent_at', 'template']
    search_fields = ['recipient', 'subject', 'recipient_name']
    ordering = ['-sent_at']
    readonly_fields = ['sent_at', 'delivered_at', 'opened_at', 'clicked_at']

    fieldsets = (
        ('Email Details', {
            'fields': ('template', 'recipient', 'recipient_name', 'subject')
        }),
        ('Content', {
            'fields': ('body',),
            'classes': ('collapse',)
        }),
        ('Status & Tracking', {
            'fields': ('status', 'sent_at', 'delivered_at', 'opened_at', 'clicked_at')
        }),
        ('Additional Info', {
            'fields': ('error_message', 'message_id'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'lead', 'opportunity', 'uploaded_by', 'uploaded_at', 'version']
    list_filter = ['document_type', 'uploaded_at', 'version', 'is_latest']
    search_fields = ['title', 'description', 'lead__title', 'opportunity__name']
    ordering = ['-uploaded_at']
    readonly_fields = ['uploaded_at', 'version']

    fieldsets = (
        ('Document Information', {
            'fields': ('title', 'document_type', 'file', 'description')
        }),
        ('Relationships', {
            'fields': ('lead', 'contact', 'company', 'opportunity')
        }),
        ('Version Control', {
            'fields': ('version', 'is_latest')
        }),
        ('Settings', {
            'fields': ('uploaded_by',)
        }),
        ('Metadata', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(LeadScore)
class LeadScoreAdmin(admin.ModelAdmin):
    list_display = ['lead', 'total_score', 'grade', 'last_calculated']
    list_filter = ['grade', 'last_calculated']
    search_fields = ['lead__title', 'lead__contact__first_name', 'lead__contact__last_name', 'grade']
    ordering = ['-total_score', '-last_calculated']
    readonly_fields = ['last_calculated']

    fieldsets = (
        ('Lead Score Information', {
            'fields': ('lead', 'total_score', 'grade')
        }),
        ('Score Breakdown', {
            'fields': ('score_breakdown',),
            'classes': ('collapse',)
        }),
        ('Calculation', {
            'fields': ('last_calculated', 'calculated_by'),
            'classes': ('collapse',)
        }),
    )


class WorkflowStepInline(admin.TabularInline):
    model = WorkflowStep
    extra = 0
    fields = ['name', 'order', 'action_type', 'delay_days', 'delay_hours']
    ordering = ['order']


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ['name', 'workflow_type', 'trigger_event', 'created_at', 'is_active']
    list_filter = ['workflow_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [WorkflowStepInline]

    fieldsets = (
        ('Workflow Information', {
            'fields': ('name', 'description', 'workflow_type')
        }),
        ('Triggers', {
            'fields': ('trigger_event', 'trigger_conditions'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active', 'created_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'name', 'order', 'action_type', 'delay_days', 'delay_hours']
    list_filter = ['workflow', 'action_type']
    search_fields = ['name', 'workflow__name']
    ordering = ['workflow', 'order']

    fieldsets = (
        ('Step Information', {
            'fields': ('workflow', 'name', 'order', 'action_type')
        }),
        ('Configuration', {
            'fields': ('action_config', 'conditions'),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('delay_days', 'delay_hours'),
            'classes': ('collapse',)
        }),
    )
