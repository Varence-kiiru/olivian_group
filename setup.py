#!/usr/bin/env python
"""
Production Setup Script for Olivian Group Django Project
Optimized for shared hosting deployment (HostAfrica)
"""

import os
import sys
import subprocess

def run_command(command, description="", show_output=False):
    """Run a shell command and print status"""
    if description:
        print(f"\n[SETUP] {description}...")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if show_output and result.stdout:
            print(result.stdout)
        print(f"✓ SUCCESS: {description or 'Command'} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ ERROR: {description or 'Command'} failed: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False

def check_environment():
    """Check if we're in production environment"""
    return os.getenv('DJANGO_ENV') == 'production' or os.getenv('DEBUG') == 'False'

def install_packages():
    """Install packages for shared hosting"""
    print("\n[SETUP] Installing packages for shared hosting...")
    
    # Try pip install with --user flag for shared hosting
    commands = [
        ("pip install -r requirements.txt --user", "Installing packages with --user flag"),
        ("pip install -r requirements.txt", "Installing packages (fallback)")
    ]
    
    for cmd, desc in commands:
        if run_command(cmd, desc):
            return True
    
    print("WARNING: Package installation failed. Please install manually.")
    return False

def setup_production():
    """Setup for production environment"""
    print("\n" + "="*60)
    print("  OLIVIAN GROUP - PRODUCTION DEPLOYMENT SETUP")
    print("  Optimized for Shared Hosting (HostAfrica)")
    print("="*60)
    
    # Check Python version
    print(f"\n[INFO] Python version: {sys.version}")
    
    # Install packages first (Django needs to be installed before importing)
    if not install_packages():
        print("✗ Package installation failed. Cannot continue.")
        return False
    
    # Now import Django after installation
    try:
        import django
        from django.core.management import execute_from_command_line
        print("✓ Django modules imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Django: {e}")
        print("Please run: pip install -r requirements.txt --user")
        return False
    
    # Set production settings and add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olivian_solar.settings')
    
    # Setup Django
    try:
        print(f"[DEBUG] Attempting to import olivian_solar.settings...")
        import olivian_solar.settings
        print(f"[DEBUG] Settings imported successfully")
        django.setup()
        print("✓ Django environment initialized")
    except Exception as e:
        print(f"✗ Django setup failed: {e}")
        print(f"Current directory: {current_dir}")
        print(f"Python path: {sys.path[:3]}")
        
        # Try to diagnose the issue
        try:
            import olivian_solar
            print("✓ olivian_solar module can be imported")
        except ImportError as ie:
            print(f"✗ Cannot import olivian_solar: {ie}")
        
        try:
            from decouple import config
            print("✓ python-decouple imported successfully")
        except ImportError as ie:
            print(f"✗ Cannot import decouple: {ie}")
            print("Please install: pip install python-decouple --user")
        
        return False
    
    # Database operations
    print("\n[DATABASE] Setting up database...")
    
    # Create migrations (safer for production)
    try:
        execute_from_command_line(['manage.py', 'makemigrations', '--noinput'])
        print("✓ Migrations created")
    except Exception as e:
        print(f"⚠ Migration creation: {e}")
    
    # Apply migrations
    try:
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        print("✓ Database migrations applied")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        print("Please check database connection and run migrations manually")
        return False
    
    # Collect static files for production
    print("\n[STATIC] Collecting static files...")
    try:
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput', '--clear'])
        print("✓ Static files collected and cleared old files")
    except Exception as e:
        print(f"⚠ Static files collection: {e}")
    
    # Check for critical files
    critical_files = ['.env', 'olivian_solar/settings.py']
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"✓ Found {file_path}")
        else:
            print(f"⚠ Missing {file_path}")
    
    # Production checklist
    print("\n" + "="*60)
    print("  PRODUCTION DEPLOYMENT CHECKLIST")
    print("="*60)
    print("✓ 1. Install packages: pip install -r requirements.txt --user")
    print("✓ 2. Run migrations: python manage.py migrate")
    print("✓ 3. Collect static: python manage.py collectstatic --noinput")
    print("□ 4. Set environment variables in .env file:")
    print("    - DEBUG=False")
    print("    - SECRET_KEY=your-production-secret")
    print("    - DB_NAME, DB_USER, DB_PASSWORD")
    print("    - ALLOWED_HOSTS=['yourdomain.com', 'www.yourdomain.com']")
    print("□ 5. Configure shared hosting:")
    print("    - Point domain to public_html/olivian")
    print("    - Set Python app entry point to: olivian_solar/wsgi.py")
    print("    - Set static files path to: staticfiles/")
    print("□ 6. Test the deployment")
    print("□ 7. Create superuser: python manage.py createsuperuser")
    
    print("\n✓ PRODUCTION SETUP COMPLETED!")
    print("Your Olivian Group solar platform is ready for deployment.")
    
    return True

def setup_development():
    """Setup for development environment"""
    print("\n[DEV] Setting up development environment...")
    
    # Install packages first
    if not install_packages():
        print("✗ Package installation failed. Cannot continue.")
        return False
    
    # Import Django after installation
    try:
        import django
        from django.core.management import execute_from_command_line
        print("✓ Django modules imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Django: {e}")
        return False
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olivian_solar.settings')
    
    try:
        django.setup()
    except Exception as e:
        print(f"Django setup failed: {e}")
        print(f"Current directory: {current_dir}")
        return False
    
    # Standard development setup
    steps = [
        (['manage.py', 'makemigrations'], "Creating migrations"),
        (['manage.py', 'migrate'], "Applying migrations"),
        (['manage.py', 'collectstatic', '--noinput'], "Collecting static files"),
    ]
    
    for cmd, desc in steps:
        try:
            execute_from_command_line(cmd)
            print(f"✓ {desc}")
        except Exception as e:
            print(f"⚠ {desc}: {e}")
    
    # Optional superuser creation
    try:
        create_superuser = input("\nCreate superuser account? (y/n): ").lower()
        if create_superuser == 'y':
            execute_from_command_line(['manage.py', 'createsuperuser'])
    except (EOFError, KeyboardInterrupt):
        print("\nSkipping superuser creation...")
    
    print("\n✓ Development setup completed!")
    print("Run: python manage.py runserver")
    
    return True

if __name__ == "__main__":
    if check_environment():
        setup_production()
    else:
        setup_development()
