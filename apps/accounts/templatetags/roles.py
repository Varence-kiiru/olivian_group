from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def has_any_role(context, *roles):
    """Return True if current user has any of the provided roles.

    Usage:
      {% load roles %}
      {% if has_any_role 'super_admin' 'manager' %} ... {% endif %}
    """
    user = context.get('user')
    if not user or not hasattr(user, 'role'):
        return False
    return user.role in roles
