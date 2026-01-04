from django import forms
from django.db import models
from .models import ChatRoom, Message


class ChatRoomForm(forms.ModelForm):
    """Form for creating and editing chat rooms"""

    class Meta:
        model = ChatRoom
        fields = ['name', 'room_type', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter room name (e.g., sales-team, project-alpha)',
            }),
            'room_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the purpose of this chat room (optional)',
            }),
        }

    def clean_name(self):
        """Validate room name format"""
        name = self.cleaned_data.get('name')
        if name:
            # Convert to lowercase and replace spaces with hyphens
            name = name.lower().replace(' ', '-')
            # Remove special characters except hyphens and underscores
            import re
            name = re.sub(r'[^a-z0-9\-_]', '', name)
            # Ensure it's not empty after cleaning
            if not name:
                raise forms.ValidationError("Room name cannot be empty after removing special characters.")
        return name

    def clean(self):
        cleaned_data = super().clean()
        room_type = cleaned_data.get('room_type')
        name = cleaned_data.get('name')

        # Validate room name uniqueness
        if name:
            existing_room = ChatRoom.objects.filter(name=name).exclude(pk=self.instance.pk if self.instance else None)
            if existing_room.exists():
                raise forms.ValidationError(f"A room with the name '{name}' already exists.")

        return cleaned_data


class MessageForm(forms.ModelForm):
    """Form for sending messages"""

    file_attachment = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'file-input',
            'accept': '.jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.txt,.zip,.rar',
            'style': 'display: none;',
        })
    )

    class Meta:
        model = Message
        fields = ['content', 'file_attachment']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control message-input',
                'rows': 1,
                'placeholder': 'Type your message...',
                'maxlength': '1000',
                'autocomplete': 'off',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].required = False  # Handle validation in view - either content or file is required

    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get('content', '').strip()
        file_attachment = cleaned_data.get('file_attachment')

        # Either content or file attachment is required
        if not content and not file_attachment:
            raise forms.ValidationError("Either message content or a file attachment is required.")

        if content and len(content) > 1000:
            raise forms.ValidationError("Message cannot exceed 1000 characters.")

        return cleaned_data

    def clean_file_attachment(self):
        file = self.cleaned_data.get('file_attachment')
        if file:
            # Validate file size (10MB limit)
            if file.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError("File size cannot exceed 10MB.")

            # Validate file type
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'text/plain',
                'application/zip', 'application/x-rar-compressed'
            ]

            if file.content_type not in allowed_types:
                # Also check file extension as fallback
                allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.doc', '.docx', '.txt', '.zip', '.rar']
                if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
                    raise forms.ValidationError(
                        "Unsupported file type. Allowed: Images, PDF, Word docs, Text files, ZIP archives."
                    )

        return file


class PrivateMessageForm(forms.Form):
    """Form for sending private messages to specific users"""

    recipient = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username or email',
            'autocomplete': 'off',
        })
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Type your private message...',
            'maxlength': '1000',
        })
    )

    def clean_recipient(self):
        recipient = self.cleaned_data.get('recipient')
        if recipient:
            from django.contrib.auth import get_user_model
            User = get_user_model()

            # Try to find user by username or email
            user = User.objects.filter(
                models.Q(username=recipient) |
                models.Q(email=recipient)
            ).first()

            if not user:
                raise forms.ValidationError("User not found.")
            if not user.is_active:
                raise forms.ValidationError("User account is not active.")

        return recipient

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if not content:
            raise forms.ValidationError("Message content cannot be empty.")
        if len(content) > 1000:
            raise forms.ValidationError("Message cannot exceed 1000 characters.")
        return content


class RoomInvitationForm(forms.Form):
    """Form for inviting users to private chat rooms"""

    usernames = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter usernames (one per line)',
        }),
        help_text="Enter one username per line"
    )

    def __init__(self, room=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room = room

    def clean_usernames(self):
        usernames_text = self.cleaned_data.get('usernames', '').strip()
        if not usernames_text:
            raise forms.ValidationError("Please enter at least one username.")

        from django.contrib.auth import get_user_model
        User = get_user_model()

        usernames = [u.strip() for u in usernames_text.split('\n') if u.strip()]
        valid_users = []
        invalid_usernames = []

        for username in usernames:
            try:
                user = User.objects.get(
                    models.Q(username=username) |
                    models.Q(email=username),
                    is_active=True
                )
                # Check if user is already a participant
                if self.room and self.room.participants.filter(id=user.id).exists():
                    invalid_usernames.append(f"{username} (already a participant)")
                else:
                    valid_users.append(user)
            except User.DoesNotExist:
                invalid_usernames.append(f"{username} (user not found)")

        if invalid_usernames:
            raise forms.ValidationError(
                f"The following usernames are invalid: {', '.join(invalid_usernames)}"
            )

        if not valid_users:
            raise forms.ValidationError("No valid users found.")

        return valid_users
