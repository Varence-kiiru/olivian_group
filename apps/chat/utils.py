from django.utils.text import slugify


def get_user_group_slugs(user):
    """Return a set of slugs for the groups a user belongs to.

    Prefers stored `GroupSlug` values if available; falls back to slugify(group.name).
    """
    slugs = set()
    try:
        from .models import GroupSlug
        # Map existing GroupSlug objects
        group_slugs = {gs.group_id: gs.slug for gs in GroupSlug.objects.filter(group__in=user.groups.all())}
        for g in user.groups.all():
            slug = group_slugs.get(g.id) or slugify(g.name)
            slugs.add(slug)
    except Exception:
        # Fallback: slugify names
        for g in user.groups.all():
            slugs.add(slugify(g.name))
    return slugs
