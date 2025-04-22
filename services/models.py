from django.db import models
from django.utils.text import slugify

class ServicesBanner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300)
    image = models.ImageField(upload_to='services/')
    
    class Meta:
        verbose_name = "Services Banner"
        verbose_name_plural = "Services Banner"
    
    def __str__(self):
        return self.title
class Service(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.TextField(max_length=500)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Font Awesome class name (e.g. fas fa-cog)")
    image = models.ImageField(upload_to='services/')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']

class ServiceBenefit(models.Model):
    service = models.ForeignKey(Service, related_name='benefits', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Font Awesome class name")
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.service.title} - {self.title}"

    class Meta:
        ordering = ['order']
