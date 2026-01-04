from django import template
import hashlib

register = template.Library()

@register.filter
def get_avatar_color(user):
    """Generate a consistent color based on user's name"""
    colors = [
        '#4e73df',  # Blue
        '#1cc88a',  # Green
        '#36b9cc',  # Cyan
        '#f6c23e',  # Yellow
        '#e74a3b',  # Red
        '#6f42c1',  # Purple
        '#5a5c69',  # Gray
    ]
    
    # Create hash from user's full name
    name_hash = hashlib.md5(
        f"{user.get('first_name', '')}{user.get('last_name', '')}".encode()
    ).hexdigest()
    
    # Use hash to pick a color
    color_index = int(name_hash, 16) % len(colors)
    return colors[color_index]