from django import forms
from .models import Comment, Post, Category, Tag, BlogBanner

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'email', 'content']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Email'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Your Comment',
                'rows': 4
            })
        }

class SearchForm(forms.Form):
    query = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search posts...'
        })
    )

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'slug', 'category', 'tags', 'featured_image', 'excerpt',
                 'content', 'meta_title', 'meta_description', 'meta_keywords',
                 'canonical_url', 'is_featured', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'featured_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            # Remove required attribute for CKEditor5 integration
            'content': forms.Textarea(attrs={'class': 'form-control ckeditor-textarea', 'rows': 10}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-control'}),
            'canonical_url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove required attribute from content field for CKEditor5 integration
        self.fields['content'].widget.attrs.pop('required', None)

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
        }

class BlogBannerForm(forms.ModelForm):
    class Meta:
        model = BlogBanner
        fields = ['title', 'subtitle', 'background_image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'subtitle': forms.TextInput(attrs={'class': 'form-control'}),
            'background_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
