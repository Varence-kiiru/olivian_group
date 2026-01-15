from django import forms
from django.utils import timezone
from datetime import datetime
from django.contrib.auth import get_user_model
from .models import Lead, Opportunity, Contact, Company, Activity, Campaign, LeadSource

User = get_user_model()


class ContactForm(forms.ModelForm):
    CONTACT_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('company', 'Company'),
    ]

    contact_type = forms.ChoiceField(
        choices=CONTACT_TYPE_CHOICES,
        initial='individual',
        widget=forms.RadioSelect(attrs={'class': 'contact-type-radio'})
    )

    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        required=False,
        empty_label="Select company...",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'data-placeholder': 'Select or search companies...'
        })
    )

    class Meta:
        model = Contact
        fields = [
            'contact_type', 'title', 'first_name', 'last_name',
            'position', 'department', 'email', 'phone', 'mobile',
            'website', 'address_line_1', 'city', 'county',
            'postal_code', 'country', 'linkedin_url', 'source',
            'notes'
        ]
        widgets = {
            'title': forms.Select(attrs={
                'class': 'form-control'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name',
                'required': 'required'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name',
                'required': 'required'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Job title/position'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Department name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email address',
                'required': 'required'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number',
                'required': 'required'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mobile number'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'address_line_1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Street address'
            }),
            'address_line_2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apartment, suite, etc.'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'county': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'County name'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postal code'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country',
                'value': 'Kenya'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'LinkedIn profile URL'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about the contact'
            }),
            'source': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company_id', None)
        super().__init__(*args, **kwargs)
        
        # Set company queryset and initial value if provided
        self.fields['company'].queryset = Company.objects.order_by('name')
        if company_id:
            self.fields['company'].initial = company_id

        # Set autofocus on first name
        self.fields['first_name'].widget.attrs['autofocus'] = True

    def clean(self):
        cleaned_data = super().clean()
        contact_type = cleaned_data.get('contact_type')
        company = cleaned_data.get('company')

        if contact_type == 'company' and not company:
            self.add_error('company', 'Company is required for business contacts')

        return cleaned_data

    def save(self, commit=True):
        contact = super().save(commit=False)
        
        if commit:
            contact.save()
            
            # Handle company association
            company_name = self.cleaned_data.get('company')
            if company_name and self.cleaned_data['contact_type'] == 'company':
                company, _ = Company.objects.get_or_create(
                    name=company_name,
                    defaults={'created_by': contact.created_by}
                )
                contact.companies.add(company)
            elif self.cleaned_data['contact_type'] == 'individual':
                contact.companies.clear()
                
        return contact


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'name',
            'company_type',
            'industry',
            'email',
            'phone',
            'website',
            'address_line_1',
            'city',
            'county',
            'postal_code',
            'country',
            'employee_count',
            'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company name',
                'required': True
            }),
            'company_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'industry': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Manufacturing, Technology'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'company@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+254-xxx-xxx-xxx'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'address_line_1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Street address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'county': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'County'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postal code'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'value': 'Kenya'
            }),
            'employee_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of employees'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about the company'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['autofocus'] = True
        
        # Make certain fields required
        self.fields['name'].required = True
        self.fields['industry'].required = True
        self.fields['email'].required = False  # Make email optional
        self.fields['phone'].required = False  # Make phone optional

    def clean_website(self):
        website = self.cleaned_data.get('website')
        if website and not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        return website

    def clean(self):
        cleaned_data = super().clean()
        # Ensure at least email or phone is provided
        email = cleaned_data.get('email')
        phone = cleaned_data.get('phone')
        
        if not email and not phone:
            raise forms.ValidationError(
                "Please provide either an email address or phone number."
            )
        
        return cleaned_data


class LeadForm(forms.ModelForm):
    # Required fields
    title = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Brief description of the lead',
            'required': 'required'
        })
    )
    contact_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full contact name',
            'required': 'required'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'contact@company.com',
            'required': 'required'
        })
    )

    # Company Information
    company_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter company name'
        })
    )
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://company.com'
        })
    )
    industry = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Manufacturing, Technology'
        })
    )
    company_size = forms.ChoiceField(
        choices=[
            ('', 'Select company size'),
            ('1-10', '1-10 employees'),
            ('11-50', '11-50 employees'),
            ('51-200', '51-200 employees'),
            ('201-500', '201-500 employees'),
            ('500+', '500+ employees'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Contact Details
    job_title = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Job title/position'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+254-xxx-xxx-xxx'
        })
    )
    address = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Street address'
        })
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        })
    )
    country = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Country',
            'value': 'Kenya'
        })
    )

    # Lead Details
    status = forms.ChoiceField(
        choices=Lead.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    priority = forms.ChoiceField(
        choices=Lead.PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    source = forms.ModelChoiceField(
        queryset=LeadSource.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    interest = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe their requirements or interests'
        })
    )
    budget = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Estimated budget in KES'
        })
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Additional details about the lead'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Internal notes'
        })
    )

    # Solar System Details
    system_type = forms.ChoiceField(
        choices=Lead.SYSTEM_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    estimated_capacity = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'kW'
        })
    )
    estimated_value = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'KES'
        })
    )
    monthly_electricity_bill = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'KES'
        })
    )

    # Timeline
    expected_close_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    next_follow_up = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    class Meta:
        model = Lead
        fields = [
            'title', 'status', 'priority', 'source',
            'system_type', 'estimated_capacity', 'estimated_value',
            'monthly_electricity_bill', 'expected_close_date',
            'next_follow_up', 'assigned_to', 'description', 'notes'
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Make certain fields not required for initial form
        self.fields['source'].queryset = LeadSource.objects.filter(is_active=True)
        
        # Filter assigned_to to sales team members
        self.fields['assigned_to'].queryset = User.objects.filter(
            role__in=['super_admin', 'manager', 'sales_manager', 'sales_person']
        ).order_by('first_name', 'last_name')
        
        # Set default assigned_to to current user if creating new lead
        if not self.instance.pk and user:
            self.fields['assigned_to'].initial = user

        # Initialize form with existing data if editing
        if self.instance.pk:
            if self.instance.contact:
                self.fields['contact_name'].initial = self.instance.contact.get_full_name()
                self.fields['email'].initial = self.instance.contact.email
                self.fields['phone'].initial = self.instance.contact.phone
                self.fields['job_title'].initial = self.instance.contact.position

            if self.instance.company:
                self.fields['company_name'].initial = self.instance.company.name
                self.fields['website'].initial = self.instance.company.website
                self.fields['industry'].initial = self.instance.company.industry
                self.fields['city'].initial = self.instance.company.city
                
                # Map employee count to company size
                if self.instance.company.employee_count:
                    count = self.instance.company.employee_count
                    if count <= 10:
                        self.fields['company_size'].initial = '1-10'
                    elif count <= 50:
                        self.fields['company_size'].initial = '11-50'
                    elif count <= 200:
                        self.fields['company_size'].initial = '51-200'
                    elif count <= 500:
                        self.fields['company_size'].initial = '201-500'
                    else:
                        self.fields['company_size'].initial = '500+'

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        contact_name = cleaned_data.get('contact_name')
        email = cleaned_data.get('email')
        
        if not title:
            raise forms.ValidationError("Lead title is required.")
        
        if not contact_name:
            raise forms.ValidationError("Contact name is required.")
        
        if not email:
            raise forms.ValidationError("Email address is required.")
            
        return cleaned_data

    def save(self, commit=True):
        try:
            lead = super().save(commit=False)
            
            # Handle contact creation/assignment
            contact_name = self.cleaned_data.get('contact_name')
            email = self.cleaned_data.get('email')
            
            if contact_name and email:
                # Split contact name into first and last name
                name_parts = contact_name.strip().split()
                first_name = name_parts[0] if name_parts else ''
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                
                # Create or get contact
                contact, created = Contact.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'phone': self.cleaned_data.get('phone', ''),

                        'position': self.cleaned_data.get('job_title', ''),

                    }
                )
                lead.contact = contact
            
            # Handle company creation/assignment
            company_name = self.cleaned_data.get('company_name')
            if company_name:
                company, created = Company.objects.get_or_create(
                    name=company_name,
                    defaults={
                        'industry': self.cleaned_data.get('industry', ''),

                        'website': self.cleaned_data.get('website', ''),

                        'employee_count': self._parse_company_size(self.cleaned_data.get('company_size')),

                        'city': self.cleaned_data.get('city', ''),

                    }
                )
                lead.company = company
                
                # Link contact to company
                if lead.contact:
                    company.contacts.add(lead.contact)
            
            if commit:
                lead.save()
            return lead
            
        except Exception as e:
            print(f"Error saving lead: {str(e)}")
            raise
    
    def _parse_company_size(self, company_size):
        """Convert company size string to approximate number"""
        if not company_size:
            return None
        
        size_mapping = {
            '1-10': 5,
            '11-50': 30,
            '51-200': 125,
            '201-500': 350,
            '500+': 1000,
        }
        return size_mapping.get(company_size)

class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = [
            'name',
            'stage',
            'probability',
            'value',
            'lead',
            'contact',
            'company',
            'expected_close_date',
            'actual_close_date',
            'assigned_to',
            'description',
            'next_steps',
            'competition'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter opportunity name'
            }),
            'stage': forms.Select(attrs={
                'class': 'form-control'
            }),
            'probability': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '5',
                'placeholder': 'Success probability (%)'
            }),
            'value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Opportunity value in KES'
            }),
            'lead': forms.Select(attrs={
                'class': 'form-control'
            }),
            'contact': forms.Select(attrs={
                'class': 'form-control'
            }),
            'company': forms.Select(attrs={
                'class': 'form-control'
            }),
            'expected_close_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'actual_close_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detailed description of the opportunity'
            }),
            'next_steps': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Next actions to move this opportunity forward'
            }),
            'competition': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Information about competing solutions/vendors'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set field labels
        self.fields['name'].label = 'Opportunity Name'
        self.fields['stage'].label = 'Sales Stage'
        self.fields['probability'].label = 'Probability of Success (%)'
        self.fields['value'].label = 'Opportunity Value (KES)'
        self.fields['expected_close_date'].label = 'Expected Close Date'
        self.fields['actual_close_date'].label = 'Actual Close Date'
        self.fields['next_steps'].label = 'Next Steps'
        self.fields['competition'].label = 'Competition'

        # Required fields
        self.fields['name'].required = True
        self.fields['stage'].required = True
        self.fields['value'].required = True
        self.fields['expected_close_date'].required = True
        
        # Filter related fields
        self.fields['contact'].queryset = Contact.objects.all().order_by('first_name', 'last_name')
        self.fields['company'].queryset = Company.objects.all().order_by('name')
        self.fields['lead'].queryset = Lead.objects.exclude(
            status__in=['won', 'lost']
        ).order_by('-created_at')
        self.fields['assigned_to'].queryset = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')

    def clean(self):
        cleaned_data = super().clean()
        stage = cleaned_data.get('stage')
        probability = cleaned_data.get('probability')
        value = cleaned_data.get('value')
        expected_close_date = cleaned_data.get('expected_close_date')
        actual_close_date = cleaned_data.get('actual_close_date')

        if stage in ['closed_won', 'closed_lost'] and not actual_close_date:
            raise forms.ValidationError("Actual close date is required for closed opportunities")

        if probability is not None and (probability < 0 or probability > 100):
            raise forms.ValidationError("Probability must be between 0 and 100")

        if value and value <= 0:
            raise forms.ValidationError("Opportunity value must be greater than zero")

        if expected_close_date and expected_close_date < timezone.now().date():
            raise forms.ValidationError("Expected close date cannot be in the past")

        return cleaned_data


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = [
            # Basic Information
            'subject', 'activity_type', 'status', 'priority', 'category', 'tags',

            # Relationships
            'contact', 'company', 'lead', 'opportunity',

            # Timing
            'scheduled_datetime', 'end_datetime', 'duration_minutes', 'completed_datetime',

            # Location & Logistics
            'location', 'address', 'meeting_room',
            'virtual_meeting_link', 'meeting_id', 'access_code',

            # Preparation & Details
            'preparation_notes', 'materials_needed', 'description',
            'agenda', 'objectives',

            # Activity Outcome
            'outcome', 'action_items', 'next_steps', 'follow_up_date',
            'key_discussion_points', 'decisions_made', 'notes',

            # Cost & Resources
            'estimated_cost', 'actual_cost', 'required_resources',

            # Assignment & Participation
            'assigned_to', 'participants'
        ]
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter activity subject'
            }),
            'activity_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'contact': forms.Select(attrs={
                'class': 'form-control'
            }),
            'lead': forms.Select(attrs={
                'class': 'form-control'
            }),
            'opportunity': forms.Select(attrs={
                'class': 'form-control'
            }),
            'scheduled_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Duration in minutes'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Activity description'
            }),
            'outcome': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Activity outcome'
            }),
            'next_steps': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Next steps'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial datetime if provided in GET parameters
        scheduled_date = self.initial.get('scheduled_date')
        if scheduled_date:
            try:
                # Parse the date string and set initial value
                date_obj = datetime.fromisoformat(scheduled_date.replace('Z', '+00:00'))
                self.fields['scheduled_datetime'].initial = date_obj
            except (ValueError, AttributeError):
                pass

        self.fields['subject'].widget.attrs['autofocus'] = True
        self.fields['contact'].queryset = Contact.objects.all().order_by('last_name', 'first_name')
        self.fields['lead'].queryset = Lead.objects.exclude(status__in=['won', 'lost']).order_by('-created_at')
        self.fields['opportunity'].queryset = Opportunity.objects.exclude(stage__in=['closed_won', 'closed_lost']).order_by('-created_at')


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = [
            'name', 'campaign_type', 'status', 'start_date', 'end_date',
            'budget', 'target_leads', 'target_revenue',
            'description', 'message', 'landing_page_url', 'owner'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'campaign_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'KES'}),
            'target_leads': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of leads'}),
            'target_revenue': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'KES'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'landing_page_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/campaign'}),
            'owner': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['name'].widget.attrs['autofocus'] = True
        self.fields['owner'].queryset = User.objects.filter(
            role__in=['super_admin', 'manager', 'sales_manager']
        ).order_by('first_name', 'last_name')


class LeadSearchForm(forms.Form):
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search leads...'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Lead.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(
            role__in=['super_admin', 'manager', 'sales_manager', 'sales_person']
        ).order_by('first_name', 'last_name'),
        required=False,
        empty_label='All Assignees',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    source = forms.ModelChoiceField(
        queryset=LeadSource.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label='All Sources',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class QuickLeadForm(forms.ModelForm):
    """Simplified form for quick lead creation"""
    class Meta:
        model = Lead
        fields = ['title', 'contact', 'phone', 'email', 'estimated_value', 'source']
        
    phone = forms.CharField(max_length=20, required=False)
    email = forms.EmailField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contact'].required = False
        
    def save(self, commit=True):
        lead = super().save(commit=False)
        
        # Create contact if phone/email provided but no contact selected
        if not lead.contact and (self.cleaned_data.get('phone') or self.cleaned_data.get('email')):
            contact_data = {
                'first_name': 'New',
                'last_name': 'Contact',
                'phone': self.cleaned_data.get('phone', ''),
                'email': self.cleaned_data.get('email', ''),
            }
            contact = Contact.objects.create(**contact_data)
            lead.contact = contact
        
        if commit:
            lead.save()
        return lead
