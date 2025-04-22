from django.db import models
from django.utils import timezone

class Contact(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"

class ContactPageContent(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    address = models.TextField()
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    map_embed_code = models.TextField(help_text="Google Maps embed code")

    class Meta:
        verbose_name = "Contact Page Content"
        verbose_name_plural = "Contact Page Content"

    def __str__(self):
        return self.title
