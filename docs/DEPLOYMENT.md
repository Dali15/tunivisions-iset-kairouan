# Deployment Guide

Deploy Tunivisions Kairouan to production using the configured hosting platform.

## 🚀 Quick Deployment

### Option 1: Render.com ⭐ (Recommended - 5 minutes)

1. **Create Account** → [render.com](https://render.com)
2. **Create Web Service**
   - Click "New" → "Web Service"
   - Connect GitHub repository
   - Set these values:
   - **Build Command:** `pip install -r requirements.txt`
       - **Start Command:** `bash start.sh`

3. **Add Environment Variables**
   ```
   DEBUG=False
   SECRET_KEY=your-secret-key-here
    ALLOWED_HOSTS=tunivisions-iset-kairouan.onrender.com
   ```

4. **Deploy** → Click "Create Web Service"

✅ Done! Your app is live in ~5 minutes with free PostgreSQL database

`start.sh` already runs migrations and collects static files before launching Gunicorn, so a separate pre-deploy command is not required.

---

### Option 2: Railway.app (5 minutes)

1. Create account → [railway.app](https://railway.app)
2. Create new project
3. Import GitHub repository
4. Add environment variables
5. Deploy automatically

✅ Free tier with $5 monthly credits

---

### Option 3: PythonAnywhere (10 minutes)

1. Create account → [pythonanywhere.com](https://pythonanywhere.com)
2. Upload code via web interface
3. Configure virtual environment
4. Set up web app pointing to Django
5. Reload app

✅ Free tier available

---

### Option 4: Docker (Local or Cloud - 15 minutes)

**Local testing:**
```bash
docker-compose up
```

**Deploy to cloud:** Push Docker image to any cloud provider

---

## 🔧 Local Setup (5 minutes)

```bash
# Clone & setup
git clone https://github.com/yourusername/ai-club.git
cd ai-club

# Create environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install & migrate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser

# Run
python manage.py runserver
```

Visit → http://localhost:8000

---

## 📋 Before Deploying

**Security Checklist:**
- [ ] Generate new SECRET_KEY (use: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- [ ] Set DEBUG=False
- [ ] Update ALLOWED_HOSTS
- [ ] Add to .env (never commit .env)
- [ ] Verify no hardcoded secrets

**Database Setup:**
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Collect static files: `python manage.py collectstatic`

---

## 🐛 Troubleshooting

### Database Errors
```bash
python manage.py migrate --fake-initial
```

### Static Files Not Loading
```bash
python manage.py collectstatic --clear --noinput
```

### Port Already in Use
```bash
python manage.py runserver 8080
```

### Permission Errors
```bash
chmod +x manage.py  # macOS/Linux
```

---

## 📚 Additional Resources

- [Django Deployment Docs](https://docs.djangoproject.com/en/5.2/howto/deployment/)
- [Render Documentation](https://render.com/docs)
- [Railway Documentation](https://docs.railway.app/)

---

## ✅ Success Check

After deployment, verify:
- [ ] App loads without errors
- [ ] Database is connected
- [ ] Chat assistant works
- [ ] Admin panel is accessible
- [ ] Static files load properly
- [ ] HTTPS is enabled

---

**Questions?** See [CONTRIBUTING.md](CONTRIBUTING.md) or open an issue on GitHub.
