from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field

class ProjectsBanner(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='project_banners/')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Project Banners'
        ordering = ['title']

    def __str__(self):
        return self.title

class ProjectCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Project Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Project(models.Model):
    STATUS_CHOICES = (
        ('completed', 'Completed'),
        ('ongoing', 'Ongoing'),
        ('upcoming', 'Upcoming')
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(ProjectCategory, on_delete=models.CASCADE)
    client = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    duration = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    description = CKEditor5Field()
    challenge = CKEditor5Field()
    solution = CKEditor5Field()
    result = CKEditor5Field()
    main_image = models.ImageField(upload_to='projects/')
    start_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class ProjectImage(models.Model):
    project = models.ForeignKey(Project, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='projects/gallery/')
    caption = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Image for {self.project.title}"

class Testimonial(models.Model):
    project = models.ForeignKey(Project, related_name='testimonials', on_delete=models.CASCADE)
    client_name = models.CharField(max_length=100)
    client_position = models.CharField(max_length=100)
    client_company = models.CharField(max_length=100)
    content = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    image = models.ImageField(upload_to='testimonials/', blank=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Testimonial by {self.client_name}"
