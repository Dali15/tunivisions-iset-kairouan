import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_club.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()


def get_credential(*names):
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return ''


# Create superuser with credentials from environment
username = get_credential('ADMIN_USERNAME', 'DJANGO_SUPERUSER_USERNAME')
email = get_credential('ADMIN_EMAIL', 'DJANGO_SUPERUSER_EMAIL')
password = get_credential('ADMIN_PASSWORD', 'DJANGO_SUPERUSER_PASSWORD')

if not username or not email or not password:
    print('ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD (or DJANGO_SUPERUSER_* equivalents) must be set. Skipping superuser creation.', flush=True)
    raise SystemExit(0)

if not User.objects.filter(username=username).exists():
    print(f"Creating superuser '{username}'...", flush=True)
    User.objects.create_superuser(username=username, email=email, password=password, role='owner')
    print(f"✅ Superuser '{username}' created successfully!", flush=True)
else:
    print(f"⚠️  User '{username}' already exists. Updating credentials...", flush=True)
    user = User.objects.get(username=username)
    user.set_password(password)
    user.email = email
    user.is_staff = True
    user.is_superuser = True
    user.role = 'owner'
    user.save()
    print(f"✅ User '{username}' updated! Password reset, promoted to superuser & role set to Owner.", flush=True)

print(f"   Email: {email}", flush=True)
print("   Password: ******** (masked)", flush=True)

