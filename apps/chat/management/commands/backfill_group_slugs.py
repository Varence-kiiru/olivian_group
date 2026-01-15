from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.utils.text import slugify
from apps.chat.models import GroupSlug


class Command(BaseCommand):
    help = 'Backfill GroupSlug entries for existing auth Groups'

    def handle(self, *args, **options):
        groups = Group.objects.all()
        created = 0
        updated = 0
        for g in groups:
            base = slugify(g.name) or 'group'
            slug = base
            counter = 1
            # Ensure unique slug across GroupSlug
            while GroupSlug.objects.filter(slug=slug).exclude(group=g).exists():
                slug = f"{base}-{counter}"
                counter += 1

            obj, ok = GroupSlug.objects.update_or_create(group=g, defaults={'slug': slug})
            if ok:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(f'Backfilled group slugs: created={created}, updated={updated}'))
