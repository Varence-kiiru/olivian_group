from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()

@register.simple_tag
def admin_url_exists(view_name):
    try:
        reverse(view_name)
        return True
    except NoReverseMatch:
        return False
