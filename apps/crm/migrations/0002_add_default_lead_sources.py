from django.db import migrations

def create_default_lead_sources(apps, schema_editor):
    LeadSource = apps.get_model('crm', 'LeadSource')
    default_sources = [
        {
            'name': 'Website',
            'description': 'Leads from company website',
            'is_active': True
        },
        {
            'name': 'Referral',
            'description': 'Referrals from existing customers',
            'is_active': True
        },
        {
            'name': 'Social Media',
            'description': 'Leads from social media platforms',
            'is_active': True
        },
        {
            'name': 'Trade Show',
            'description': 'Leads from trade shows and exhibitions',
            'is_active': True
        },
        {
            'name': 'Cold Call',
            'description': 'Leads from cold calling',
            'is_active': True
        },
        {
            'name': 'Google Ads',
            'description': 'Leads from Google Advertising',
            'is_active': True
        }
    ]
    
    for source in default_sources:
        LeadSource.objects.create(**source)

def remove_default_lead_sources(apps, schema_editor):
    LeadSource = apps.get_model('crm', 'LeadSource')
    LeadSource.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('crm', '0001_initial'),  # Adjust this to your actual initial migration
    ]

    operations = [
        migrations.RunPython(create_default_lead_sources, remove_default_lead_sources),
    ]