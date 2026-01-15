from django.core.management.base import BaseCommand
from django.core.management import call_command
from apps.core.models import CompanySettings


class Command(BaseCommand):
    help = 'Sets up the system after importing production database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-migrations',
            action='store_true',
            help='Skip running migrations',
        )

    def handle(self, *args, **options):
        """Setup system after database import"""
        self.stdout.write(
            self.style.SUCCESS('Setting up system after database import...\n')
        )

        # Run migrations if not skipped
        if not options['skip_migrations']:
            self.stdout.write('Running migrations...')
            call_command('migrate', verbosity=1)
            self.stdout.write(self.style.SUCCESS('✓ Migrations completed\n'))

        # Ensure company settings exist
        self.stdout.write('Ensuring company settings...')
        call_command('ensure_company_settings', verbosity=1)
        self.stdout.write(self.style.SUCCESS('✓ Company settings ensured\n'))

        # Collect static files
        self.stdout.write('Collecting static files...')
        try:
            call_command('collectstatic', '--noinput', verbosity=1)
            self.stdout.write(self.style.SUCCESS('✓ Static files collected\n'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Static files warning: {e}\n'))

        # Check system
        self.stdout.write('Performing system check...')
        try:
            call_command('check', verbosity=1)
            self.stdout.write(self.style.SUCCESS('✓ System check passed\n'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'System check failed: {e}\n'))

        # Detect environment
        from django.conf import settings
        is_production = not getattr(settings, 'DEBUG', True)
        
        if is_production:
            next_steps = (
                '🎉 Production setup completed! Your system should now be ready.\n'
                '\nNext steps:\n'
                '1. Create a superuser: python manage.py createsuperuser\n'
                '2. Restart your web server/application\n'
                '3. Access admin at: https://olivian.co.ke/admin/\n'
                '4. Test the blog at: https://olivian.co.ke/blog/\n'
                '\n✅ The blog admin error should now be resolved!'
            )
        else:
            next_steps = (
                '🎉 Setup completed! Your system should now be ready to use.\n'
                '\nNext steps:\n'
                '1. Create a superuser: python manage.py createsuperuser\n'
                '2. Start the development server: python manage.py runserver\n'
                '3. Access admin at: http://localhost:8000/admin/\n'
            )
        
        self.stdout.write(self.style.SUCCESS(next_steps))
