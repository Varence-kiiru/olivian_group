from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.text import slugify
from blog.models import BlogBanner, Category, Tag, Post, Comment

class BlogBannerTests(TestCase):
    def setUp(self):
        self.banner = BlogBanner.objects.create(
            title='Test Banner',
            subtitle='Test Subtitle',
            is_active=True
        )

    def test_banner_str(self):
        self.assertEqual(str(self.banner), 'Test Banner')

    def test_active_banner_uniqueness(self):
        second_banner = BlogBanner.objects.create(
            title='Second Banner',
            subtitle='Another Subtitle',
            is_active=True
        )
        self.banner.refresh_from_db()
        self.assertFalse(self.banner.is_active)
        self.assertTrue(second_banner.is_active)

class CategoryTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description'
        )

    def test_category_str(self):
        self.assertEqual(str(self.category), 'Test Category')

    def test_category_slug_generation(self):
        self.assertEqual(self.category.slug, 'test-category')

class TagTests(TestCase):
    def setUp(self):
        self.tag = Tag.objects.create(name='Test Tag')

    def test_tag_str(self):
        self.assertEqual(str(self.tag), 'Test Tag')

    def test_tag_slug_generation(self):
        self.assertEqual(self.tag.slug, 'test-tag')

class PostTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.category = Category.objects.create(name='Test Category')
        self.tag = Tag.objects.create(name='Test Tag')
        self.post = Post.objects.create(
            title='Test Post',
            author=self.user,
            category=self.category,
            excerpt='Test excerpt',
            content='Test content',
            status='published'
        )
        self.post.tags.add(self.tag)

    def test_post_str(self):
        self.assertEqual(str(self.post), 'Test Post')

    def test_post_slug_generation(self):
        self.assertEqual(self.post.slug, 'test-post')

    def test_post_absolute_url(self):
        expected_url = f'/blog/{self.post.slug}/'
        self.assertEqual(self.post.get_absolute_url(), expected_url)

class CommentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.category = Category.objects.create(name='Test Category')
        self.post = Post.objects.create(
            title='Test Post',
            author=self.user,
            category=self.category,
            excerpt='Test excerpt',
            content='Test content'
        )
        self.comment = Comment.objects.create(
            post=self.post,
            name='Test Commenter',
            email='test@example.com',
            content='Test comment content',
            is_approved=True
        )

    def test_comment_str(self):
        expected_str = f'Comment by Test Commenter on Test Post'
        self.assertEqual(str(self.comment), expected_str)

    def test_comment_ordering(self):
        self.assertEqual(Comment._meta.ordering, ['-created_at'])