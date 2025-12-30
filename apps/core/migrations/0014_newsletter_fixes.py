# Generated manually to fix newsletter issues

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_add_geographic_fields'),
    ]

    operations = [
        # Add missing fields to NewsletterCampaign
        migrations.AddField(
            model_name='newslettercampaign',
            name='template_type',
            field=models.CharField(default='default', help_text='Template type for rendering (default, promotional, etc.)', max_length=50),
        ),
        migrations.AddField(
            model_name='newslettercampaign',
            name='call_to_action_url',
            field=models.URLField(blank=True, default='', help_text='URL for the main call-to-action button', null=True),
        ),
        migrations.AddField(
            model_name='newslettercampaign',
            name='opens_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='newslettercampaign',
            name='clicks_count',
            field=models.PositiveIntegerField(default=0),
        ),

        # Add missing fields to NewsletterSendLog
        migrations.AddField(
            model_name='newslettersendlog',
            name='delivery_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed'), ('bounced', 'Bounced')], default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='newslettersendlog',
            name='email_address',
            field=models.EmailField(default='', help_text='Email address the newsletter was sent to'),
        ),
        migrations.AddField(
            model_name='newslettersendlog',
            name='opened_at',
            field=models.DateTimeField(blank=True, help_text='When the email was opened', null=True),
        ),
        migrations.AddField(
            model_name='newslettersendlog',
            name='clicked_at',
            field=models.DateTimeField(blank=True, help_text='When links were clicked', null=True),
        ),
        migrations.AddField(
            model_name='newslettersendlog',
            name='unsubscribed_at',
            field=models.DateTimeField(blank=True, help_text='When unsubscribed via this email', null=True),
        ),
    ]
