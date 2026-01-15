from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

User = get_user_model()

DEPARTMENT_GROUP_MAPPING = {
    'sales': ['sales'],
    'technical': ['technical', 'technician'],
    'management': ['management', 'director', 'manager'],
    'finance': ['finance'],
    'hr': ['hr', 'human resources'],
    'marketing': ['marketing'],
    'customer-service': ['customer-service', 'support'],
    'inventory': ['inventory'],
    'operations': ['operations', 'operational'],
    'projects': ['projects', 'project-manager'],
}

@receiver(post_save, sender=User)
def sync_department_groups(sender, instance, created, **kwargs):
    """
    Automatically sync user's department field with appropriate Django Groups
    for chat room access control
    """
    if not instance.department:
        return

    department_key = instance.department.lower().replace(' ', '-').replace('_', '-')

    # Find matching groups for this department
    target_groups = []
    for dept_key, group_names in DEPARTMENT_GROUP_MAPPING.items():
        if dept_key in department_key or any(g in department_key for g in group_names):
            target_groups.extend(group_names)
            break

    if not target_groups:
        # Fallback: use department name directly
        target_groups = [instance.department.lower().replace(' ', '-')]

    current_groups = set(instance.groups.values_list('name', flat=True))
    target_groups_set = set(target_groups)

    # Add missing department groups
    groups_to_add = target_groups_set - current_groups
    for group_name in groups_to_add:
        group, created = Group.objects.get_or_create(name=group_name)
        instance.groups.add(group)

    # Don't remove existing groups - only add department-specific ones
    # This preserves manually assigned groups like 'management', 'staff', etc.

    # Also add user to 'staff' group if they're an employee (not customer)
    if instance.role != 'customer':
        staff_group, created = Group.objects.get_or_create(name='staff')
        instance.groups.add(staff_group)
