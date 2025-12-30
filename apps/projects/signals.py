from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.chat.models import ChatRoom
from .models import Project

User = get_user_model()


@receiver(post_save, sender=Project)
def create_project_chat_room(sender, instance, created, **kwargs):
    """
    Automatically create a chat room for new projects
    """
    if not created:
        return  # Only create for new projects

    # Check if this project should have a chat room
    statuses_for_chat = ['lead', 'quoted', 'approved', 'planning', 'scheduled', 'in_progress']

    if instance.status not in statuses_for_chat:
        return  # Skip projects that don't need chat rooms

    room_name = f"project-{instance.project_number.lower()}"

    # Check if room already exists
    if ChatRoom.objects.filter(name=room_name).exists():
        return

    # Get participants - project manager and team members
    participants = []

    # Add project manager
    if instance.project_manager and instance.project_manager.is_active:
        participants.append(instance.project_manager)

    # Add installation team members
    for user in instance.installation_team.filter(is_active=True):
        if user not in participants:
            participants.append(user)

    # Get a superuser for room creation
    superuser = User.objects.filter(is_superuser=True, is_active=True).first()
    if not superuser:
        superuser = User.objects.filter(is_staff=True, is_active=True).first()
    if not superuser:
        return  # Cannot create room without an admin user

    try:
        # Create the chat room
        room = ChatRoom.objects.create(
            name=room_name,
            room_type='project',
            description=f'Communication room for project: {instance.name}',
            project=instance,
            created_by=superuser,
        )

        # Add participants
        if participants:
            room.participants.set(participants)
            room.save()

        print(f"Created chat room '{room_name}' for project '{instance.name}' with {len(participants)} participants")

    except Exception as e:
        print(f"Error creating chat room for project {instance.project_number}: {e}")


@receiver(pre_save, sender=Project)
def update_project_chat_room_participants(sender, instance, **kwargs):
    """
    Update participants in project chat room when project team changes
    """
    if instance.pk:  # Only for existing projects
        try:
            old_project = Project.objects.get(pk=instance.pk)

            # Check if team members changed
            old_team_ids = set(old_project.installation_team.values_list('id', flat=True))
            new_team_ids = set(instance.installation_team.values_list('id', flat=True))

            # Check if project manager changed
            old_manager_id = old_project.project_manager.id if old_project.project_manager else None
            new_manager_id = instance.project_manager.id if instance.project_manager else None

            if old_team_ids != new_team_ids or old_manager_id != new_manager_id:
                # Team changed, update chat room participants
                try:
                    room_name = f"project-{instance.project_number.lower()}"
                    room = ChatRoom.objects.get(name=room_name, room_type='project')

                    participants = []

                    # Add new project manager
                    if instance.project_manager and instance.project_manager.is_active:
                        participants.append(instance.project_manager)

                    # Add new installation team members
                    for user in instance.installation_team.filter(is_active=True):
                        if user not in participants:
                            participants.append(user)

                    room.participants.set(participants)
                    room.save()

                    print(f"Updated participants in chat room '{room_name}' for project '{instance.name}'")

                except ChatRoom.DoesNotExist:
                    # Room doesn't exist, that will be handled by post_save signal
                    pass

        except Project.DoesNotExist:
            pass  # New project
        except Exception as e:
            print(f"Error updating project chat room participants: {e}")
