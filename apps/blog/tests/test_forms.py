from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from blog.models import Post, Comment
from blog.forms import CommentForm

class CommentFormTests(TestCase):
    def test_valid_comment_form(self):
        form_data = {
            'name': 'Test Commenter',
            'email': 'test@example.com',
            'content': 'Test comment content'
        }
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_comment_form(self):
        # Test empty form
        form = CommentForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 3)  # name, email, and content are required

        # Test invalid email
        form_data = {
            'name': 'Test Commenter',
            'email': 'invalid-email',
            'content': 'Test comment content'
        }
        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_comment_form_clean(self):
        # Test content with potentially harmful HTML
        form_data = {
            'name': 'Test Commenter',
            'email': 'test@example.com',
            'content': '<script>alert("harmful");</script>Test content'
        }
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertNotIn('<script>', form.cleaned_data['content'])