from django import forms
from django.forms import modelformset_factory, inlineformset_factory
from django.contrib.auth import get_user_model
from .models import Quotation, QuotationItem, Customer, QuotationRequest
from apps.products.models import Product, ProductCategory
from django.utils.translation import gettext_lazy as _
from formtools.wizard.views import SessionWizardView

User = get_user_model()


class CustomerRequirementsForm1(forms.Form):
    """Step 1: Customer Information"""
    customer_name = forms.CharField(
        label="Full Name",
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Enter full name'}),
        required=True
    )

    customer_email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={'placeholder': 'Enter email address'}),
        required=True
    )

    customer_phone = forms.CharField(
        label="Phone Number",
        max_length=15,
        widget=forms.TextInput(attrs={'placeholder': '712345678'}),
        required=True
    )

    customer_company = forms.CharField(
        label="Company/Organization",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Optional company name'})
    )

    customer_address = forms.CharField(
        label="Address",
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Full address'}),
        required=True
    )

    customer_city = forms.CharField(
        label="City",
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'City name'}),
        required=True
    )

    COUNTY_CHOICES = [
        ('', 'Select County'),
        ('nairobi', 'Nairobi'),
        ('mombasa', 'Mombasa'),
        ('kisumu', 'Kisumu'),
        ('nakuru', 'Nakuru'),
        ('kiambu', 'Kiambu'),
        ('machakos', 'Machakos'),
        ('kajiado', 'Kajiado'),
        ('other', 'Other'),
    ]

    customer_county = forms.ChoiceField(
        label="County",
        choices=COUNTY_CHOICES,
        required=True
    )


class CustomerRequirementsForm2(forms.Form):
    """Step 2: Property Information"""

    PROPERTY_TYPE_CHOICES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
    ]

    property_type = forms.ChoiceField(
        label="Property Type",
        choices=PROPERTY_TYPE_CHOICES,
        widget=forms.RadioSelect(),
        required=True
    )

    BUILDING_AGE_CHOICES = [
        ('', 'Select age range'),
        ('new', 'Less than 5 years'),
        ('recent', '5-15 years'),
        ('mature', '15-30 years'),
        ('old', 'More than 30 years'),
    ]

    building_age = forms.ChoiceField(
        label="Building Age",
        choices=BUILDING_AGE_CHOICES,
        required=False
    )

    FLOORS_CHOICES = [
        ('1', '1 Floor'),
        ('2', '2 Floors'),
        ('3', '3 Floors'),
        ('4+', '4+ Floors'),
    ]

    floors = forms.ChoiceField(
        label="Number of Floors",
        choices=FLOORS_CHOICES,
        initial='1',
        required=False
    )

    ROOF_TYPE_CHOICES = [
        ('iron_sheets', 'Iron Sheets'),
        ('tiles', 'Clay/Concrete Tiles'),
        ('concrete', 'Concrete Slab'),
    ]

    roof_type = forms.ChoiceField(
        label="Roof Type",
        choices=ROOF_TYPE_CHOICES,
        widget=forms.RadioSelect(),
        required=True
    )

    roof_area = forms.IntegerField(
        label="Available Roof Area (sq meters)",
        min_value=10,
        max_value=10000,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 100'}),
        required=True
    )

    ROOF_ORIENTATION_CHOICES = [
        ('', 'Select primary direction'),
        ('south', 'South (Best)'),
        ('southwest', 'Southwest (Good)'),
        ('southeast', 'Southeast (Good)'),
        ('west', 'West (Fair)'),
        ('east', 'East (Fair)'),
        ('north', 'North (Poor)'),
    ]

    roof_orientation = forms.ChoiceField(
        label="Roof Orientation",
        choices=ROOF_ORIENTATION_CHOICES,
        required=False
    )

    SHADING_CHOICES = [
        ('trees', 'Nearby trees causing shade'),
        ('buildings', 'Adjacent buildings'),
        ('none', 'Clear, unobstructed area'),
    ]

    shading_issues = forms.MultipleChoiceField(
        label="Shading Issues",
        choices=SHADING_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )


class CustomerRequirementsForm3(forms.Form):
    """Step 3: Energy Consumption Analysis"""

    monthly_bill = forms.DecimalField(
        label="Average Monthly Bill",
        max_digits=10,
        decimal_places=2,
        min_value=500,
        max_value=500000,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 15000.00'}),
        required=True
    )

    monthly_consumption = forms.IntegerField(
        label="Monthly Consumption",
        min_value=50,
        max_value=50000,
        widget=forms.NumberInput(attrs={'placeholder': 'kWh'}),
        required=False  # Auto-calculated
    )

    PEAK_USAGE_CHOICES = [
        ('morning', 'Morning (6AM-12PM)'),
        ('afternoon', 'Afternoon (12PM-6PM)'),
        ('evening', 'Evening (6PM-10PM)'),
        ('night', 'Night (10PM-6AM)'),
    ]

    peak_usage_time = forms.ChoiceField(
        label="Peak Usage Time",
        choices=PEAK_USAGE_CHOICES,
        initial='evening',
        required=False
    )

    BACKUP_NEEDS_CHOICES = [
        ('none', 'No backup needed'),
        ('essential', 'Essential loads only'),
        ('partial', '50% of total load'),
        ('full', 'Full backup power'),
    ]

    backup_needs = forms.ChoiceField(
        label="Backup Power Needs",
        choices=BACKUP_NEEDS_CHOICES,
        initial='essential',
        required=False
    )

    GRID_CONNECTION_CHOICES = [
        ('reliable', 'Reliable grid connection'),
        ('intermittent', 'Frequent power outages'),
        ('poor', 'Poor/unreliable grid'),
        ('none', 'No grid connection'),
    ]

    grid_connection = forms.ChoiceField(
        label="Grid Connection",
        choices=GRID_CONNECTION_CHOICES,
        initial='reliable',
        required=False
    )


class CustomerRequirementsWizard(SessionWizardView):
    """Django Form Wizard for multi-step requirements assessment"""

    form_list = [
        ('step1', CustomerRequirementsForm1),
        ('step2', CustomerRequirementsForm2),
        ('step3', CustomerRequirementsForm3),
    ]

    template_name = 'quotations/customer_requirements.html'

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)

        # Add current step information
        current_step = self.steps.current
        all_steps = list(self.form_list.keys())

        context.update({
            'current_step_number': all_steps.index(current_step) + 1,
            'total_steps': len(all_steps),
            'current_step_name': current_step,
        })

        return context

    def done(self, form_list, **kwargs):
        """Process completed form data"""

        # Combine all form data and convert Decimal objects to floats for session storage
        form_data = {}
        for form in form_list:
            for field_name, field_value in form.cleaned_data.items():
                # Convert Decimal objects to float for JSON serialization
                if hasattr(field_value, '__class__') and 'Decimal' in str(type(field_value)):
                    form_data[field_name] = float(field_value)
                else:
                    form_data[field_name] = field_value

        # Calculate system size if not already calculated
        if form_data.get('monthly_consumption') and not form_data.get('system_size'):
            # Rough calculation: monthly consumption / 120 kWh (average monthly generation per kW in Kenya)
            system_size = form_data['monthly_consumption'] // 120
            if system_size < 1:
                system_size = 1
            form_data['system_size'] = system_size

        # Store data in session for next step (quotation creation)
        self.request.session['customer_requirements'] = form_data
        self.request.session.modified = True

        # Redirect to quotation creation from requirements
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(reverse('quotations:create_from_requirements'))


class DefaultCheckedRadioSelect(forms.RadioSelect):
    """RadioSelect widget that checks the first option by default"""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        # If this is the first option and nothing is selected, check it
        if index == 0 and not selected:
            option['attrs']['checked'] = True
        return option


class QuotationCreateForm(forms.ModelForm):
    """Form for creating and editing quotations"""

    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        empty_label="Select Customer"
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.quotation_request = kwargs.pop('quotation_request', None)
        super().__init__(*args, **kwargs)

        # Allow all customers for quotation creation
        # Management roles (director, manager, sales_manager, sales_person) can access all customers
        if self.request and hasattr(self.request.user, 'role'):
            management_roles = ['super_admin', 'director', 'manager', 'sales_manager', 'sales_person', 'project_manager', 'inventory_manager']
            user_role = self.request.user.role

            if user_role in management_roles:
                self.fields['customer'].queryset = Customer.objects.all()
            else:
                # For customers or other roles, show no customers (they should use customer portal)
                self.fields['customer'].queryset = Customer.objects.none()
        else:
            # Fallback for safety
            self.fields['customer'].queryset = Customer.objects.all()

    def clean_customer(self):
        """Validate customer field against all customers, not just the filtered queryset"""
        customer = self.cleaned_data.get('customer')
        if customer:
            # Verify the customer exists in the database
            if not Customer.objects.filter(pk=customer.pk).exists():
                raise forms.ValidationError("Selected customer does not exist.")
        return customer

    def clean(self):
        cleaned_data = super().clean()
        customer = cleaned_data.get('customer')

        # Customer is required for quotation creation
        if not customer:
            self.add_error('customer', "Please select a customer for this quotation.")

        return cleaned_data

    class Meta:
        model = Quotation
        fields = [
            'quotation_type', 'system_type', 'system_capacity', 'estimated_generation',
            'installation_complexity', 'discount_amount', 'discount_percentage',
            'validity_days', 'payment_terms', 'delivery_time', 'warranty_terms',
            'notes', 'internal_notes', 'status'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'internal_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'payment_terms': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'warranty_terms': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class QuotationCreateFromRequestForm(QuotationCreateForm):
    """Form for creating quotations from requests - customer is auto-determined"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove customer field entirely since it's auto-determined from request
        if 'customer' in self.fields:
            del self.fields['customer']

        # Pre-fill from quotation request if provided
        if self.quotation_request:
            initial_data = {
                'system_type': self.quotation_request.system_type,
                'system_requirements': self.quotation_request.system_requirements,
                'title': f"Quotation for {self.quotation_request.customer_name}",
            }
            # Update instance with initial data if this is a new quotation
            if not self.instance.pk:
                for field, value in initial_data.items():
                    if field in self.fields:
                        self.fields[field].initial = value

    class Meta:
        model = Quotation
        fields = [
            'quotation_type', 'system_type', 'system_capacity', 'estimated_generation',
            'installation_complexity', 'discount_amount', 'discount_percentage',
            'validity_days', 'payment_terms', 'delivery_time', 'warranty_terms',
            'notes', 'internal_notes', 'status'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'internal_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'payment_terms': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'warranty_terms': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.request and self.request.user.is_staff:
            instance.created_by = self.request.user

        if commit:
            instance.save()

        return instance


class QuotationItemForm(forms.ModelForm):
    """Form for quotation items"""

    class Meta:
        model = QuotationItem
        fields = [
            'item_name', 'description', 'quantity', 'unit_price'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
        }


# Formsets for managing multiple items
QuotationItemFormSet = inlineformset_factory(
    Quotation,
    QuotationItem,
    form=QuotationItemForm,
    extra=1,
    can_delete=True,
    min_num=0,  # Changed to 0 to avoid validation errors on empty items
    validate_min=False
)
