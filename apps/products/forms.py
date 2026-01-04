from django import forms
from django.forms import inlineformset_factory
from taggit.forms import TagWidget
from .models import Product, ProductImage, ProductDocument, ProductCategory


class ProductForm(forms.ModelForm):
    """Form for staff/management product management"""

    class Meta:
        model = Product
        fields = [
            # Basic Information
            'name', 'slug', 'sku', 'product_type', 'category', 'brand', 'model_number',

            # Description
            'short_description', 'description', 'features', 'applications',

            # Technical Specifications
            'power_rating', 'power_rating_kva', 'efficiency', 'voltage', 'current', 'dimensions',
            'weight', 'operating_temperature', 'warranty_years', 'certifications',

            # Pricing
            'cost_price', 'selling_price', 'sale_price', 'minimum_order_quantity',

            # Inventory
            'track_quantity', 'quantity_in_stock', 'low_stock_threshold', 'allow_backorders',

            # Marketing
            'meta_title', 'meta_description', 'featured', 'status', 'tags',

            # Customer Visibility
            'show_to_customers', 'customer_inquiry_only',

            # Files and Documents
            'installation_manual', 'datasheet',
        ]

        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Detailed product description...'
            }),
            'short_description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Brief product summary...'
            }),
            'features': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Key features (one per line)...'
            }),
            'applications': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Use cases/applications...'
            }),
            'tags': TagWidget(),
            'meta_title': forms.TextInput(attrs={
                'placeholder': 'SEO title...'
            }),
            'meta_description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'SEO description...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make certain fields required for staff management
        self.fields['name'].required = True
        self.fields['sku'].required = True
        self.fields['category'].required = True
        self.fields['product_type'].required = True

        # Add help text for important fields
        self.fields['sku'].help_text = "Unique product identifier"
        self.fields['slug'].help_text = "URL-friendly version of the name (auto-generated if empty)"
        self.fields['show_to_customers'].help_text = "Uncheck to hide this product from customer website"
        self.fields['customer_inquiry_only'].help_text = "Product visible but requires customer inquiry for pricing/quotes"

        # Set default status for new products
        if not self.instance.pk:
            self.fields['status'].initial = 'draft'

    def clean_sku(self):
        """Ensure SKU is unique"""
        sku = self.cleaned_data.get('sku')
        if sku:
            queryset = Product.objects.filter(sku=sku)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError("A product with this SKU already exists.")
        return sku

    def clean(self):
        cleaned_data = super().clean()
        selling_price = cleaned_data.get('selling_price')
        cost_price = cleaned_data.get('cost_price')
        sale_price = cleaned_data.get('sale_price')

        # Validate pricing logic
        if selling_price and cost_price and selling_price < cost_price:
            raise forms.ValidationError("Selling price cannot be lower than cost price.")

        if sale_price and selling_price and sale_price >= selling_price:
            raise forms.ValidationError("Sale price must be lower than regular selling price.")

        return cleaned_data


# Inline formsets for related models
ProductImageFormSet = inlineformset_factory(
    Product,
    ProductImage,
    fields=['id', 'image', 'alt_text', 'is_primary', 'sort_order'],
    extra=1,
    can_delete=True
)

ProductDocumentFormSet = inlineformset_factory(
    Product,
    ProductDocument,
    fields=['id', 'title', 'document_type', 'file', 'description'],
    extra=1,
    can_delete=True
)
