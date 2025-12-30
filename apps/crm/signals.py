from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Lead, Opportunity, Activity


@receiver(pre_save, sender=Lead)
def update_lead_last_contact(sender, instance, **kwargs):
    """Update last_contact_date when lead status changes"""
    if instance.pk:
        try:
            old_instance = Lead.objects.get(pk=instance.pk)
            if old_instance.status != instance.status and instance.status in ['contacted', 'qualified']:
                instance.last_contact_date = timezone.now().date()
        except Lead.DoesNotExist:
            pass


@receiver(post_save, sender=Lead)
def create_opportunity_from_qualified_lead(sender, instance, created, **kwargs):
    """Automatically create opportunity when lead is qualified"""
    if not created and instance.status == 'qualified' and not hasattr(instance, 'opportunity'):
        Opportunity.objects.create(
            name=f"{instance.title} - {instance.contact.get_full_name()}",
            lead=instance,
            contact=instance.contact,
            company=instance.company,
            stage='qualification',
            probability=25,
            value=instance.estimated_value or 0,
            expected_close_date=instance.expected_close_date or timezone.now().date(),
            assigned_to=instance.assigned_to,
            description=instance.description,
            created_by=instance.created_by
        )


@receiver(pre_save, sender=Activity)
def update_activity_completion(sender, instance, **kwargs):
    """Update completion datetime when activity status changes to completed"""
    if instance.status == 'completed' and not instance.completed_datetime:
        instance.completed_datetime = timezone.now()
    elif instance.status != 'completed':
        instance.completed_datetime = None


@receiver(post_save, sender=Activity)
def update_lead_follow_up(sender, instance, created, **kwargs):
    """Update lead's next follow-up date based on activity"""
    if instance.lead and instance.status == 'completed':
        # Set next follow-up based on activity outcome
        if 'follow' in instance.outcome.lower() or 'call back' in instance.outcome.lower():
            # Extract follow-up date from outcome or set default
            next_date = timezone.now().date() + timezone.timedelta(days=7)  # Default 1 week
            instance.lead.next_follow_up = next_date
            instance.lead.save(update_fields=['next_follow_up'])
