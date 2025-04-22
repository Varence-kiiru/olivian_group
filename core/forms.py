from django import forms
from .models import QuoteRequest, Newsletter

class QuoteRequestForm(forms.ModelForm):
    class Meta:
        model = QuoteRequest
        fields = ['name', 'email', 'phone', 'company', 'product_interest', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Phone Number'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Company (Optional)'}),
            'product_interest': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product/Service of Interest (Optional)'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Tell us about your requirements', 'rows': 4}),
        }
