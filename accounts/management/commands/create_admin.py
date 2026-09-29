from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()


def get_credential(*names):
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return ''


class Command(BaseCommand):
    help = 'Create or update a superuser account'

    def handle(self, *args, **options):
        # Get credentials from environment variables
        username = get_credential('ADMIN_USERNAME', 'DJANGO_SUPERUSER_USERNAME')
        email = get_credential('ADMIN_EMAIL', 'DJANGO_SUPERUSER_EMAIL')
        password = get_credential('ADMIN_PASSWORD', 'DJANGO_SUPERUSER_PASSWORD')

        if not username or not email or not password:
            self.stdout.write(self.style.WARNING(
                'ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD (or DJANGO_SUPERUSER_* equivalents) must be set. Skipping admin creation.'
            ))
            return

        try:
            # Check if user already exists
            user = User.objects.filter(username=username).first()
            
            if user:
                # Update existing user's password and email
                user.email = email
                user.set_password(password)
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'✅ Superuser "{username}" updated!'))
                self.stdout.write(f'🔐 Password has been reset')
            else:
                # Create new superuser
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                self.stdout.write(self.style.SUCCESS(f'✅ Superuser "{username}" created!'))
            
            self.stdout.write(f'📧 Email: {email}')
            self.stdout.write('🔐 Password: ******** (masked)')
            self.stdout.write(f'\n📍 Login at: https://ai-club-ssnk.onrender.com/admin')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
