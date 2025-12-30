from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from blog.models import BlogBanner, Category, Tag, Post, Comment

class BlogViewTests(TestCase):
    def setUp(self):
        self.client = Client()
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
        self.banner = BlogBanner.objects.create(
            title='Test Banner',
            subtitle='Test Subtitle',
            is_active=True
        )

    def test_blog_list_view(self):
        response = self.client.get(reverse('blog:blog'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/blog_list.html')
        self.assertIn('posts', response.context)
        self.assertIn('banner', response.context)

    def test_post_detail_view(self):
        response = self.client.get(reverse('blog:post_detail', kwargs={'slug': self.post.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_detail.html')
        self.assertEqual(response.context['post'], self.post)

    def test_category_posts_view(self):
        response = self.client.get(reverse('blog:category_posts', kwargs={'slug': self.category.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/category_posts.html')
        self.assertIn('category', response.context)
        self.assertIn('posts', response.context)

    def test_tag_posts_view(self):
        response = self.client.get(reverse('blog:tag_posts', kwargs={'slug': self.tag.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/tag_posts.html')
        self.assertIn('tag', response.context)
        self.assertIn('posts', response.context)

    def test_post_search(self):
        response = self.client.get(reverse('blog:blog'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('posts', response.context)
        self.assertIn(self.post, response.context['posts'])

class CommentViewTests(TestCase):
    def setUp(self):
        self.client = Client()
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
            content='Test content',
            status='published'
        )

    def test_add_comment(self):
        comment_data = {
            'name': 'Test Commenter',
            'email': 'test@example.com',
            'content': 'Test comment content'
        }
        response = self.client.post(
            reverse('blog:post_detail', kwargs={'slug': self.post.slug}),
            comment_data
        )
        self.assertEqual(response.status_code, 302)  # Redirect after successful comment
        self.assertTrue(Comment.objects.filter(post=self.post, name='Test Commenter').exists())