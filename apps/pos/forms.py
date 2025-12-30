from django import forms
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import (
    Terminal, CashierSession, Sale, Payment, 
    CashMovement, Discount, Store
)
from apps.quotations.models import Customer

User = get_user_model()


class SessionStartForm(forms.Form):
    """Form for starting a cashier session"""
    terminal = forms.ModelChoiceField(
        queryset=Terminal.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the terminal to start session on"
    )
    opening_cash = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=Decimal('1000.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Opening cash amount'
        }),
        help_text="Amount of cash in drawer at start of session"
    )
    opening_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional notes about session start...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Get available terminals for this user's store
            # For now, get all available terminals (simplified for debugging)
            available_terminals = Terminal.objects.filter(
                is_active=True,
                current_cashier__isnull=True  # Not in use
            )
            
            self.fields['terminal'].queryset = available_terminals
            
            if not available_terminals.exists():
                # If no terminals available, still show all terminals for debugging
                self.fields['terminal'].queryset = Terminal.objects.filter(is_active=True)
                self.fields['terminal'].help_text = "All terminals are in use. Please select one anyway to debug."
        else:
            # Show all terminals if no user provided
            self.fields['terminal'].queryset = Terminal.objects.filter(is_active=True)


class CustomerForm(forms.ModelForm):
    """Form for creating/editing customers using unified Customer model"""
    # Additional fields for POS-specific data entry
    first_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = Customer
        fields = [
            'name', 'email', 'phone', 'address', 'city', 'postal_code',
            'company_name', 'business_type', 'tax_number', 
            'monthly_consumption', 'average_monthly_bill', 'roof_area'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+254-xxx-xxx-xxx'
            }),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'business_type': forms.Select(attrs={'class': 'form-control'}),
            'tax_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'KRA PIN (for corporate customers)'
            }),
            'monthly_consumption': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'average_monthly_bill': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'roof_area': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional for quick customer creation
        for field in self.fields.values():
            field.required = False
        
        # Only require essential fields
        self.fields['name'].required = True
        self.fields['email'].required = True
        self.fields['phone'].required = True
        
        # Set focus on name
        self.fields['name'].widget.attrs['autofocus'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        name = cleaned_data.get('name')
        
        # If first_name and last_name are provided, use them to build the name
        if first_name or last_name:
            full_name = f"{first_name or ''} {last_name or ''}".strip()
            if full_name:
                cleaned_data['name'] = full_name
        
        return cleaned_data


class QuickCustomerForm(forms.Form):
    """Simplified form for quick customer creation during sale"""
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Customer name'
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
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'customer@email.com'
        })
    )
    
    def save(self):
        """Create customer from form data"""
        name_parts = self.cleaned_data['name'].split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        customer = Customer.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone=self.cleaned_data.get('phone', ''),
            email=self.cleaned_data.get('email', ''),
            customer_type='walk_in'
        )
        return customer


class SaleForm(forms.ModelForm):
    """Form for sale creation"""
    class Meta:
        model = Sale
        fields = ['customer', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Sale notes (optional)...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].required = False
        self.fields['customer'].queryset = Customer.objects.all().order_by('-created_at')[:20]


class PaymentForm(forms.ModelForm):
    """Form for processing payments"""
    class Meta:
        model = Payment
        fields = ['payment_type', 'amount', 'transaction_id', 'notes']
        widgets = {
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Payment amount'
            }),
            'transaction_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Transaction reference (optional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Payment notes...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        sale_total = kwargs.pop('sale_total', None)
        super().__init__(*args, **kwargs)
        
        if sale_total:
            self.fields['amount'].initial = sale_total
        
        self.fields['transaction_id'].required = False
        self.fields['notes'].required = False


class CashPaymentForm(forms.Form):
    """Specialized form for cash payments"""
    amount_received = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'step': '0.01',
            'placeholder': 'Amount received'
        })
    )
    
    def __init__(self, *args, **kwargs):
        sale_total = kwargs.pop('sale_total', Decimal('0.00'))
        super().__init__(*args, **kwargs)
        
        self.sale_total = sale_total
        self.fields['amount_received'].initial = sale_total
    
    def clean_amount_received(self):
        amount = self.cleaned_data['amount_received']
        if amount < self.sale_total:
            raise forms.ValidationError(
                f"Amount received (KES {amount}) is less than sale total (KES {self.sale_total})"
            )
        return amount
    
    @property
    def change_amount(self):
        if self.is_valid():
            return self.cleaned_data['amount_received'] - self.sale_total
        return Decimal('0.00')


class MPesaPaymentForm(forms.Form):
    """Form for M-Pesa payments"""
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '254712345678',
            'pattern': '[0-9]{12}'
        }),
        help_text="Customer's M-Pesa phone number (12 digits starting with 254)"
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'readonly': True
        })
    )
    
    def __init__(self, *args, **kwargs):
        sale_total = kwargs.pop('sale_total', Decimal('0.00'))
        super().__init__(*args, **kwargs)
        self.fields['amount'].initial = sale_total
    
    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        # Remove any spaces or dashes
        phone = phone.replace(' ', '').replace('-', '')
        
        # Ensure it starts with 254
        if not phone.startswith('254'):
            if phone.startswith('0'):
                phone = '254' + phone[1:]
            elif phone.startswith('7') or phone.startswith('1'):
                phone = '254' + phone
            else:
                raise forms.ValidationError("Invalid phone number format")
        
        # Validate length
        if len(phone) != 12:
            raise forms.ValidationError("Phone number must be 12 digits long")
        
        return phone


class CashMovementForm(forms.ModelForm):
    """Form for cash drawer movements"""
    class Meta:
        model = CashMovement
        fields = ['movement_type', 'amount', 'reason', 'notes']
        widgets = {
            'movement_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Amount'
            }),
            'reason': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Reason for cash movement'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)
        
        self.session = session
        self.fields['notes'].required = False


class DiscountForm(forms.ModelForm):
    """Form for applying discounts"""
    class Meta:
        model = Discount
        fields = ['name', 'code', 'discount_type', 'percentage_value', 'fixed_amount']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'discount_type': forms.Select(attrs={'class': 'form-control'}),
            'percentage_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'max': '100',
                'min': '0'
            }),
            'fixed_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            })
        }


class DiscountApplicationForm(forms.Form):
    """Form for applying discount to sale"""
    discount_code = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter discount code',
            'autocomplete': 'off'
        })
    )
    
    def clean_discount_code(self):
        code = self.cleaned_data['discount_code'].upper()
        
        try:
            discount = Discount.objects.get(code=code, is_active=True)
            if not discount.is_valid:
                raise forms.ValidationError("This discount code is not valid or has expired")
            return code
        except Discount.DoesNotExist:
            raise forms.ValidationError("Invalid discount code")


class ProductSearchForm(forms.Form):
    """Form for searching products in POS"""
    query = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, SKU, or barcode...',
            'autocomplete': 'off'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.products.models import ProductCategory
        self.fields['category'].queryset = ProductCategory.objects.filter(is_active=True)


class SessionCloseForm(forms.Form):
    """Form for closing cashier session"""
    closing_cash = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'step': '0.01',
            'placeholder': 'Actual cash count'
        }),
        help_text="Count all cash in drawer and enter total amount"
    )
    closing_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Session closing notes (optional)...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        expected_cash = kwargs.pop('expected_cash', None)
        super().__init__(*args, **kwargs)
        
        if expected_cash:
            self.fields['closing_cash'].initial = expected_cash
            self.fields['closing_cash'].help_text += f" (Expected: KES {expected_cash:,.2f})"


# Import required modules at the top
from django.db.models import Q
