from django.db import models
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
import io
import sys
from django_ckeditor_5.fields import CKEditor5Field
from django.utils.text import slugify

class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='site/')
    favicon = models.ImageField(upload_to='site/')
    copyright_text = models.TextField()

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

class MainMenu(models.Model):
    title = models.CharField(max_length=100)
    url = models.CharField(max_length=200)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

class SocialLink(models.Model):
    name = models.CharField(max_length=50)
    url = models.URLField()
    icon_class = models.CharField(max_length=50)

class FooterSection(models.Model):
    title = models.CharField(max_length=100)
   
class FooterLink(models.Model):
    section = models.ForeignKey(FooterSection, related_name='links', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    url = models.CharField(max_length=200)

class ContactInfo(models.Model):
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20)
    address = models.TextField()

    class Meta:
        verbose_name = 'Contact Information'
        verbose_name_plural = 'Contact Information'

class Newsletter(models.Model):
    # Newsletter settings
    title = models.CharField(max_length=200, default="Subscribe to Our Newsletter")
    description = models.TextField(default="Stay updated with our latest news and offers.")
   
    # Subscriber fields
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    confirmation_token = models.CharField(max_length=64, blank=True, null=True)
    confirmed = models.BooleanField(default=False)
   
    # Track user preferences
    interests = models.CharField(max_length=255, blank=True, help_text="Comma-separated list of interests")
   
    class Meta:
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'
   
    def __str__(self):
        return self.email

class HeroBanner(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='hero_banners/')
    link_url = models.CharField(max_length=200)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

class WelcomeSection(models.Model):
    title = models.CharField(max_length=200)
    content = CKEditor5Field()

    def __str__(self):
        return self.title

class WhatWeDoItem(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='what_we_do/')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

class QuoteRequest(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    company = models.CharField(max_length=200, blank=True)
    product_interest = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('declined', 'Declined')
    ], default='new')

    def __str__(self):
        return f"Quote Request from {self.name}"

class QuoteFollowUp(models.Model):
    """Model for tracking follow-ups on quote requests"""
    quote_request = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name='followups')
    notes = models.TextField()
    follow_up_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
   
    class Meta:
        ordering = ['-follow_up_date']
   
    def __str__(self):
        return f"Follow-up on {self.quote_request.name}'s request"

class AdminNotification(models.Model):
    """Model for storing admin notifications"""
    NOTIFICATION_TYPES = (
        ('quote', 'Quote Request'),
        ('contact', 'Contact Form'),
        ('order', 'New Order'),
        ('system', 'System Notification'),
    )
   
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
   
    class Meta:
        ordering = ['-created_at']
   
    def __str__(self):
        return self.title

class AboutBanner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300)
    image = models.ImageField(upload_to='about/')
   
    def __str__(self):
        return self.title

class Achievement(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.ImageField(upload_to='achievements/')
    order = models.IntegerField(default=0)
   
    class Meta:
        ordering = ['order']

class AboutSection(models.Model):
    title = models.CharField(max_length=200)
    content = CKEditor5Field()
    image = models.ImageField(upload_to='about/')
   
    def __str__(self):
        return self.title

class TeamSection(models.Model):
    introduction = CKEditor5Field()

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    qualifications = models.TextField()
    photo = models.ImageField(upload_to='team/')
    order = models.IntegerField(default=0)
   
    class Meta:
        ordering = ['order']

class ContactSection(models.Model):
    title = models.CharField(max_length=200)
    address = models.TextField()
    map_embed_code = models.TextField()
    cta_title = models.CharField(max_length=200)
    cta_description = models.TextField()
    cta_button_text = models.CharField(max_length=50)
    cta_button_link = models.CharField(max_length=200)

class PolicyPage(models.Model):
    POLICY_TYPES = (
        ('privacy', 'Privacy Policy'),
        ('terms', 'Terms & Conditions'),
        ('refund', 'Return & Refund Policy'),
        ('shipping', 'Shipping & Delivery'),
        ('faq', 'FAQs'),
        ('environment', 'Environmental Commitment'),
        ('certifications', 'Certifications & Standards'),
    )
   
    title = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=POLICY_TYPES, unique=True)
    content = CKEditor5Field()
    slug = models.SlugField(unique=True, blank=True)
    meta_description = models.TextField(blank=True, help_text="Description for search engines")
    last_updated = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)
   
    class Meta:
        verbose_name = "Policy Page"
        verbose_name_plural = "Policy Pages"
   
    def __str__(self):
        return self.title
   
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class FAQItem(models.Model):
    question = models.CharField(max_length=255)
    answer = CKEditor5Field()
    category = models.CharField(max_length=100, blank=True)
    order = models.IntegerField(default=0)
   
    class Meta:
        ordering = ['order', 'question']
        verbose_name = "FAQ Item"
        verbose_name_plural = "FAQ Items"

    def __str__(self):
        return self.question

class Certification(models.Model):
    name = models.CharField(max_length=200)
    description = CKEditor5Field()
    logo = models.ImageField(
        upload_to='certifications/',
        blank=True,
        help_text="Recommended size: 400x300 pixels or smaller. Images will be resized automatically."
    )
    issue_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    issuing_authority = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
   
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Certification"
        verbose_name_plural = "Certifications"
   
    def __str__(self):
        return self.name
   
    def save(self, *args, **kwargs):
        # Process the image if it exists
        if self.logo and hasattr(self.logo, 'file'):
            # Open the uploaded image
            img = Image.open(self.logo)
           
            # Calculate new dimensions while maintaining aspect ratio
            max_size = (400, 300)  # Maximum width and height
            img.thumbnail(max_size, Image.LANCZOS)
           
            # Save the resized image
            output = io.BytesIO()
            img_format = 'PNG' if self.logo.name.lower().endswith('.png') else 'JPEG'
            img.save(output, format=img_format, quality=85)
            output.seek(0)
           
            # Replace the image field with the resized image
            self.logo = InMemoryUploadedFile(
                output, 'ImageField',
                self.logo.name,
                f'image/{img_format.lower()}',
                sys.getsizeof(output),
                None
            )
       
        super().save(*args, **kwargs)
