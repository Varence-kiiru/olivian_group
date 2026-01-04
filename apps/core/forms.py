from django import forms
from django.core.exceptions import ValidationError
from .models import (
    ContactMessage, NewsletterSubscriber, CompanySettings,
    NewsletterCampaign, LegalDocument, ServiceArea, HolidayOffer,
    TeamMember, ProjectShowcase, Testimonial, CookieConsent
)

class FlexibleDecimalField(forms.DecimalField):
    """
    Decimal field that accepts more precision in input than stored.
    Automatically rounds to the specified decimal places.
    """

    def __init__(self, auto_round_to=None, *args, **kwargs):
        # Temporarily set higher limits for input acceptance
        kwargs.setdefault('max_digits', 30)
        kwargs.setdefault('decimal_places', 20)
        super().__init__(*args, **kwargs)
        self.auto_round_to = auto_round_to

    def to_python(self, value):
        """
        Convert input to Python decimal, allowing more precision than stored.
        """
        if value is None or value == '':
            return None

        # Convert to string first to handle high precision input
        if isinstance(value, (int, float, str)):
            value_str = str(value).strip()
            # Count decimal places in input
            if '.' in value_str:
                decimal_part = value_str.split('.')[1]
                input_decimals = len(decimal_part.rstrip('0'))
                # If input has more decimals than we want to store, round it
                if input_decimals > self.auto_round_to:
                    # Parse as float and round
                    try:
                        float_val = float(value_str)
                        rounded_val = round(float_val, self.auto_round_to)
                        value_str = f"{rounded_val:.{self.auto_round_to}f}".rstrip('0').rstrip('.')
                    except (ValueError, TypeError):
                        pass  # Keep original value_str

            # Now convert using parent method with our processed value
            try:
                return super().to_python(value_str)
            except (ValueError, TypeError, ValidationError):
                # If conversion fails, try the original value
                return super().to_python(value)

        return super().to_python(value)

    def clean(self, value):
        """
        Clean the value, ensuring it's rounded to our desired precision.
        """
        value = self.to_python(value)
        self.validate(value)
        self.run_validators(value)
        return value

class ContactForm(forms.ModelForm):
    """Contact form for website submissions"""

    class Meta:
        model = ContactMessage
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'location', 'property_type', 'monthly_bill',
            'inquiry_type', 'message', 'subscribe_newsletter', 'agree_privacy'
        ]

        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your last name',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+254 7XX XXX XXX',
                'required': True
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Nairobi, Karen'
            }),
            'property_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'monthly_bill': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount in KES',
                'min': '0',
                'step': '0.01'
            }),
            'inquiry_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Tell us about your solar energy needs...',
                'required': True
            }),
            'subscribe_newsletter': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'agree_privacy': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'required': True
            })
        }

        labels = {
            'first_name': 'First Name *',
            'last_name': 'Last Name *',
            'email': 'Email Address *',
            'phone': 'Phone Number *',
            'location': 'Location',
            'property_type': 'Property Type',
            'monthly_bill': 'Monthly Electricity Bill (KES)',
            'inquiry_type': 'Inquiry Type',
            'message': 'Message *',
            'subscribe_newsletter': 'Subscribe to our newsletter for solar tips and updates',
            'agree_privacy': 'I agree to the Privacy Policy and Terms of Service *'
        }

    def clean_agree_privacy(self):
        """Ensure privacy policy is agreed to"""
        agree = self.cleaned_data.get('agree_privacy')
        if not agree:
            raise forms.ValidationError("You must agree to the Privacy Policy and Terms of Service to submit this form.")
        return agree

    def clean_phone(self):
        """Basic phone number validation"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove spaces and special characters for validation
            clean_phone = ''.join(filter(str.isdigit, phone))
            if len(clean_phone) < 10:
                raise forms.ValidationError("Please enter a valid phone number.")
        return phone

class NewsletterSubscriptionForm(forms.ModelForm):
    """Newsletter subscription form - legacy support"""

    class Meta:
        model = NewsletterSubscriber
        fields = ['email', 'first_name', 'last_name']

        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address',
                'required': True
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name (optional)'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name (optional)'
            })
        }

class CompanySettingsForm(forms.ModelForm):
    """Custom form for CompanySettings with proper decimal field handling"""

    # Use flexible decimal fields for coordinates
    latitude = FlexibleDecimalField(
        max_digits=18,
        decimal_places=14,
        auto_round_to=14,
        required=False,
        help_text="Latitude coordinate for company location"
    )
    longitude = FlexibleDecimalField(
        max_digits=18,
        decimal_places=14,
        auto_round_to=14,
        required=False,
        help_text="Longitude coordinate for company location"
    )

    class Meta:
        model = CompanySettings
        fields = '__all__'


class NewsletterCampaignForm(forms.ModelForm):
    """Custom form for NewsletterCampaign with validation"""

    class Meta:
        model = NewsletterCampaign
        fields = ['title', 'subject', 'preview_text', 'content', 'template_type',
                 'call_to_action_text', 'call_to_action_url', 'status', 'scheduled_for']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 15,
                'class': 'form-control',
                'placeholder': 'Enter your newsletter content here...'
            }),
            'preview_text': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Brief preview text shown in email clients'
            }),
            'scheduled_for': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        scheduled_for = cleaned_data.get('scheduled_for')

        # Validation logic
        if status == 'scheduled' and not scheduled_for:
            raise forms.ValidationError("Scheduled campaigns must have a scheduled date and time.")

        call_to_action_text = cleaned_data.get('call_to_action_text')
        call_to_action_url = cleaned_data.get('call_to_action_url')

        # Both CTA fields must be filled or both empty
        if (call_to_action_text and not call_to_action_url) or (call_to_action_url and not call_to_action_text):
            raise forms.ValidationError("Both Call to Action text and URL must be provided together.")

        return cleaned_data

    def clean_content(self):
        """Validate newsletter content"""
        content = self.cleaned_data.get('content')
        if content and len(content.strip()) < 10:
            raise forms.ValidationError("Newsletter content must be at least 10 characters long.")
        return content


class LegalDocumentForm(forms.ModelForm):
    """Custom form for LegalDocument with HTML validation"""

    class Meta:
        model = LegalDocument
        fields = ['document_type', 'title', 'content', 'short_description', 'version', 'effective_date']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 20,
                'class': 'form-control',
                'placeholder': 'Enter the full document content here...'
            }),
            'short_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Brief summary for meta descriptions'
            }),
            'effective_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }

    def clean_content(self):
        """Basic HTML validation for legal documents"""
        content = self.cleaned_data.get('content')
        if content:
            # Check for basic HTML structure
            if '<' in content and '>' in content:
                # Basic check - ensure opening and closing tags
                pass  # Could add more sophisticated HTML validation here
            elif len(content.strip()) < 50:
                raise forms.ValidationError("Document content must be at least 50 characters long.")
        return content

    def clean_version(self):
        """Validate version format"""
        version = self.cleaned_data.get('version')
        if version:
            # Allow formats like 1.0, 1.1, 2.0, etc.
            import re
            if not re.match(r'^\d+\.\d+$', version):
                raise forms.ValidationError("Version must be in format X.Y (e.g., 1.0, 2.1)")
        return version


class ServiceAreaForm(forms.ModelForm):
    """Custom form for ServiceArea with coordinate handling"""

    # Use flexible decimal fields for coordinates (same as CompanySettings)
    latitude = FlexibleDecimalField(
        max_digits=10,
        decimal_places=8,
        auto_round_to=8,  # Service areas use 8 decimal places
        required=False,
        help_text="Latitude coordinate for service area center"
    )
    longitude = FlexibleDecimalField(
        max_digits=11,
        decimal_places=8,
        auto_round_to=8,
        required=False,
        help_text="Longitude coordinate for service area center"
    )

    class Meta:
        model = ServiceArea
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Describe the service area coverage...'
            }),
            'boundary_geojson': forms.Textarea(attrs={
                'rows': 10,
                'class': 'form-control',
                'placeholder': 'GeoJSON polygon data for service area boundary'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')
        radius_km = cleaned_data.get('radius_km')

        # If radius is specified, coordinates are required
        if radius_km and (latitude is None or longitude is None):
            raise forms.ValidationError("Coordinates are required when specifying a service radius.")

        return cleaned_data


class HolidayOfferForm(forms.ModelForm):
    """Custom form for HolidayOffer with date validation"""

    class Meta:
        model = HolidayOffer
        fields = '__all__'
        widgets = {
            'banner_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Special Holiday Discount: 20% Off!'
            }),
            'discount_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Detailed discount information...'
            }),
            'special_benefits': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Additional benefits or terms...'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        discount_percentage = cleaned_data.get('discount_percentage')
        discount_description = cleaned_data.get('discount_description')

        # If discount percentage is set, description should be provided
        if discount_percentage and not discount_description:
            raise forms.ValidationError("Please provide discount details when setting a discount percentage.")

        # Validate discount percentage range
        if discount_percentage is not None and (discount_percentage <= 0 or discount_percentage > 100):
            raise forms.ValidationError("Discount percentage must be between 1 and 100.")

        return cleaned_data


class TeamMemberForm(forms.ModelForm):
    """Custom form for TeamMember profiles"""

    class Meta:
        model = TeamMember
        fields = '__all__'
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 6,
                'class': 'form-control',
                'placeholder': 'Brief biography of the team member...'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }

    def clean_email(self):
        """Validate email format"""
        email = self.cleaned_data.get('email')
        if email and '@' not in email:
            raise forms.ValidationError("Please enter a valid email address.")
        return email


class ProjectShowcaseForm(forms.ModelForm):
    """Custom form for ProjectShowcase entries"""

    class Meta:
        model = ProjectShowcase
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 6,
                'class': 'form-control',
                'placeholder': 'Detailed description of the project...'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'completion_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }

    def clean_capacity(self):
        """Validate capacity format"""
        capacity = self.cleaned_data.get('capacity')
        if capacity:
            # Basic validation for capacity strings like "10kW", "200kW", "1.5MW"
            import re
            if not re.match(r'^\d+(\.\d+)?\s*(kW|MW)$', capacity.strip()):
                raise forms.ValidationError("Capacity must be in format like '10kW', '200kW', or '1.5MW'.")
        return capacity


class TestimonialForm(forms.ModelForm):
    """Custom form for Testimonial entries"""

    class Meta:
        model = Testimonial
        fields = '__all__'
        widgets = {
            'quote': forms.Textarea(attrs={
                'rows': 6,
                'class': 'form-control',
                'placeholder': 'Customer testimonial quote...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Westlands, Nairobi'
            }),
        }

    def clean_rating(self):
        """Validate rating range"""
        rating = self.cleaned_data.get('rating')
        if rating is not None and (rating < 1 or rating > 5):
            raise forms.ValidationError("Rating must be between 1 and 5 stars.")
        return rating


class CookieConsentForm(forms.ModelForm):
    """Custom form for CookieConsent management"""

    class Meta:
        model = CookieConsent
        fields = ['essential_consent', 'analytics_consent', 'marketing_consent',
                 'preferences_consent', 'social_consent']
        widgets = {
            'essential_consent': forms.Select(attrs={'class': 'form-select'}),
            'analytics_consent': forms.Select(attrs={'class': 'form-select'}),
            'marketing_consent': forms.Select(attrs={'class': 'form-select'}),
            'preferences_consent': forms.Select(attrs={'class': 'form-select'}),
            'social_consent': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        essential_consent = cleaned_data.get('essential_consent')

        # Essential cookies are always required to be granted
        if essential_consent != 'granted':
            raise forms.ValidationError("Essential cookies must always be granted.")

        return cleaned_data
