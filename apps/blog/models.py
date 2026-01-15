from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field

class BlogBanner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    background_image = models.ImageField(upload_to='blog/banners/%Y/%m/')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Blog Banner"
        verbose_name_plural = "Blog Banners"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Ensure only one active banner at a time
        if self.is_active:
            BlogBanner.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)
    featured_image = models.ImageField(upload_to='blog/posts/')
    excerpt = models.TextField(max_length=500)
    content = CKEditor5Field()
    meta_title = models.CharField(max_length=70, blank=True, help_text='SEO optimized title (max 70 characters)')
    meta_description = models.CharField(max_length=160, blank=True, help_text='SEO optimized description (max 160 characters)')
    meta_keywords = models.CharField(max_length=255, blank=True, help_text='Comma-separated keywords for SEO')
    canonical_url = models.URLField(blank=True, help_text='Canonical URL for SEO (if different from current URL)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=[
        ('draft', 'Draft'),
        ('published', 'Published')
    ], default='draft')
    views = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = slugify(self.title)
            # Ensure uniqueness by appending a number if needed
            original_slug = self.slug
            counter = 1
            while Post.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    likes_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['created_at']  # Changed to chronological for nested display

    def __str__(self):
        return f'Comment by {self.name} on {self.post.title}'

    def get_replies(self):
        return self.replies.filter(is_approved=True)

    def is_top_level(self):
        return self.parent is None

class CommentLike(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_likes')
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['comment', 'ip_address']
        ordering = ['-created_at']

class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes')
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['post', 'ip_address']
        ordering = ['-created_at']
