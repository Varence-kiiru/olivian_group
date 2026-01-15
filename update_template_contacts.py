#!/usr/bin/env python

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olivian_solar.settings')
django.setup()

from apps.crm.models import EmailTemplate

def update_email_templates():
    """Update email templates to include staff member contact information for better lead control"""

    templates_to_update = EmailTemplate.objects.filter(is_active=True)

    signature_updates = [
        # Replace old signature formats with new contact-enabled format
        {
            'old': 'Best regards,\n<strong>{{assigned_to}}</strong>',
            'new': 'Best regards,<br>\n<strong>{{assigned_to}}</strong><br>\n<strong>{{assigned_to_department}}</strong><br>\n📞 {{assigned_to_phone}}<br>\n📧 {{assigned_to_email}}'
        },
        {
            'old': 'Best regards,<br>\n<strong>{{assigned_to}}</strong>',
            'new': 'Best regards,<br>\n<strong>{{assigned_to}}</strong><br>\n<strong>{{assigned_to_department}}</strong><br>\n📞 {{assigned_to_phone}}<br>\n📧 {{assigned_to_email}}'
        }
    ]

    contact_section_updates = [
        # Add contact sections where customers can easily reach the assigned representative
        {
            'old': '<h4>Your Sales Representative</h4>\n<p style="margin: 10px 0; color: #6c757d;"><strong>{{assigned_to|default:"Sales Team"}}</strong></p>\n<p style="margin: 5px 0;"><a href="tel:+254719728666" style="color: #28a745;">📞 +254 719 728 666</a></p>\n<p style="margin: 5px 0;"><a href="mailto:info@olivian.co.ke" style="color: #28a745;">📧 info@olivian.co.ke</a></p>',
            'new': '<h4>Your Dedicated Representative</h4>\n<p style="margin: 10px 0; color: #6c757d;"><strong>{{assigned_to}}</strong></p>\n<p style="margin: 5px 0;"><a href="tel:{{assigned_to_phone}}" style="color: #28a745;">📞 {{assigned_to_phone}}</a></p>\n<p style="margin: 5px 0;"><a href="mailto:{{assigned_to_email}}" style="color: #28a745;">📧 {{assigned_to_email}}</a></p>\n<p style="margin: 10px 0; font-size: 14px; color: #6c757d;">{{assigned_to_full_info}} - Your direct contact for all questions</p>'
        }
    ]

    updated_count = 0

    for template in templates_to_update:
        old_body = template.body
        new_body = old_body

        # Update signature sections
        for update in signature_updates:
            if update['old'] in new_body:
                new_body = new_body.replace(update['old'], update['new'])
                print(f"✓ Updated signature in {template.name}")

        # Update contact sections
        for update in contact_section_updates:
            if update['old'] in new_body:
                new_body = new_body.replace(update['old'], update['new'])
                print(f"✓ Updated contact section in {template.name}")

        # Add direct contact information where missing
        if '{{assigned_to_phone}}' not in new_body and '{{assigned_to}}' in new_body:
            # Look for signature patterns and add contact info
            if 'Best regards,<br>' in new_body and '{{assigned_to_phone}}' not in new_body:
                phone_addition = '<br>\n📞 Direct: {{assigned_to_phone}} | 📧 {{assigned_to_email}}'
                new_body = new_body.replace('Best regards,<br>', 'Best regards,<br>' + phone_addition)
                print(f"✓ Added contact info to signature in {template.name}")

        if old_body != new_body:
            template.body = new_body
            template.save()
            updated_count += 1

    print(f"\n✅ Successfully updated {updated_count} email templates with staff contact information")
    print("📊 This gives staff members full control over their assigned leads!")
if __name__ == '__main__':
    update_email_templates()
