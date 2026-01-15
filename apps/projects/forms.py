from django import forms
from .models import Project


class ProjectForm(forms.ModelForm):
    """Custom form for Project with proper file handling"""
    
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'project_type', 'system_type', 'client', 
            'status', 'priority', 'completion_percentage', 'system_capacity', 
            'estimated_generation', 'installation_address', 'city', 'county', 
            'start_date', 'target_completion', 'actual_completion', 'duration_days',
            'contract_value', 'estimated_cost', 'actual_cost', 'project_manager', 
            'featured_image'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'project_type': forms.Select(attrs={'class': 'form-select'}),
            'system_type': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'completion_percentage': forms.NumberInput(attrs={'class': 'form-range', 'min': 0, 'max': 100}),
            'system_capacity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estimated_generation': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'installation_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'county': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'target_completion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actual_completion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'contract_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'actual_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'project_manager': forms.Select(attrs={'class': 'form-select'}),
            'featured_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
    
    def clean_featured_image(self):
        """Validate uploaded image"""
        image = self.cleaned_data.get('featured_image')
        
        if image:
            # Check file size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image file too large ( > 5MB )")
            
            # Check file extension
            if not image.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                raise forms.ValidationError("Unsupported image format. Please use PNG, JPG, JPEG, GIF, or WebP.")
        
        return image


class ProjectCreateForm(ProjectForm):
    """Form for creating new projects"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # For create forms, some fields can be optional initially
        self.fields['actual_completion'].required = False
        self.fields['actual_cost'].required = False
        self.fields['completion_percentage'].initial = 0
        self.fields['status'].initial = 'planning'
        
    def clean_actual_cost(self):
        """Ensure actual_cost has a default value"""
        actual_cost = self.cleaned_data.get('actual_cost')
        if actual_cost is None:
            return 0
        return actual_cost


class ProjectUpdateForm(ProjectForm):
    """Form for updating existing projects"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make some fields optional for updates
        self.fields['actual_cost'].required = False
        self.fields['project_manager'].required = False
        
        # Set default values for empty fields
        if self.instance and self.instance.pk:
            if not self.fields['actual_cost'].initial and not self.instance.actual_cost:
                self.fields['actual_cost'].initial = 0
                
    def clean_actual_cost(self):
        """Ensure actual_cost has a default value"""
        actual_cost = self.cleaned_data.get('actual_cost')
        if actual_cost is None:
            return 0
        return actual_cost
