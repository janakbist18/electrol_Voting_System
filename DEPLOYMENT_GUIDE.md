# Nepal Voting System - Deployment Guide

## Pre-Deployment Checklist

### Security

- [ ] Generate new `SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up SSL/HTTPS certificates
- [ ] Enable CSRF protection
- [ ] Configure CORS properly
- [ ] Enable security headers (HSTS, X-Frame-Options, etc.)
- [ ] Set up rate limiting
- [ ] Configure reCAPTCHA keys

### Database

- [ ] Set up PostgreSQL database
- [ ] Create database user with proper permissions
- [ ] Test database connection
- [ ] Plan backup strategy

### External Services

- [ ] Set up SendGrid account for email
- [ ] Configure Twilio for SMS (optional)
- [ ] Set up Google OAuth credentials
- [ ] Configure reCAPTCHA v3
- [ ] Set up Redis instance
- [ ] Configure Sentry for error tracking

### Monitoring

- [ ] Set up monitoring/alerting
- [ ] Configure logging
- [ ] Set up uptime monitoring
- [ ] Plan backup schedule

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/nepal-voting-system.git
cd nepal_voting
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with local settings
```

### 5. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_constituencies_csv
python manage.py createsuperuser
```

### 6. Load Demo Data (Optional)

```bash
python manage.py seed_demo_data
```

### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 8. Run Development Server

```bash
python manage.py runserver
```

Access at: http://localhost:8000

---

## Docker Deployment

### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "nepal_voting.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

### 2. Create docker-compose.yml

```yaml
version: "3.8"

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build: .
    command: gunicorn nepal_voting.wsgi:application --bind 0.0.0.0:8000 --workers 4
    environment:
      - DEBUG=False
      - DB_HOST=db
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - REDIS_HOST=redis
    volumes:
      - ./:/app
      - static_volume:/app/static
      - media_volume:/app/media
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery:
    build: .
    command: celery -A nepal_voting worker -l info
    environment:
      - DEBUG=False
      - DB_HOST=db
      - CELERY_BROKER_URL=redis://redis:6379/0
      - REDIS_HOST=redis
    depends_on:
      - db
      - redis
      - web

  celery-beat:
    build: .
    command: celery -A nepal_voting beat -l info
    environment:
      - DEBUG=False
      - DB_HOST=db
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### 3. Build and Run

```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py seed_constituencies_csv
```

---

## Cloud Deployment (Heroku)

### 1. Install Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Windows
choco install heroku-cli
```

### 2. Create Heroku App

```bash
heroku login
heroku create your-app-name
```

### 3. Add PostgreSQL Add-on

```bash
heroku addons:create heroku-postgresql:standard-0
```

### 4. Add Redis Add-on

```bash
heroku addons:create heroku-redis:premium-0
```

### 5. Set Environment Variables

```bash
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=your-secret-key
heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com
# Set all other variables...
```

### 6. Create Procfile

```
web: gunicorn nepal_voting.wsgi:application --log-file -
worker: celery -A nepal_voting worker -l info
beat: celery -A nepal_voting beat -l info
```

### 7. Deploy

```bash
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
heroku run python manage.py seed_constituencies_csv
```

---

## AWS Deployment (EC2 + RDS)

### 1. Launch EC2 Instance

```bash
# Ubuntu 22.04 LTS, t3.medium or larger
# Security group: Open ports 80, 443, 22
```

### 2. Setup Server

```bash
# SSH into instance
ssh -i key.pem ubuntu@your-instance-ip

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3.11 python3-pip python3-venv postgresql-client nginx supervisor

# Create app directory
sudo mkdir -p /var/www/nepal-voting
sudo chown ubuntu:ubuntu /var/www/nepal-voting
```

### 3. Setup Application

```bash
cd /var/www/nepal-voting
git clone https://github.com/yourusername/nepal-voting-system.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
nano .env  # Edit with your settings
```

### 4. Setup RDS Database

- Create RDS PostgreSQL instance
- Configure security groups to allow EC2 access
- Update DB_HOST in .env

### 5. Setup Nginx

```bash
sudo nano /etc/nginx/sites-available/nepal-voting
```

```nginx
upstream nepal_voting {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://nepal_voting;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/nepal-voting/static/;
    }

    location /media/ {
        alias /var/www/nepal-voting/media/;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/nepal-voting /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Setup Supervisor for Gunicorn

```bash
sudo nano /etc/supervisor/conf.d/nepal-voting.conf
```

```ini
[program:nepal-voting]
directory=/var/www/nepal-voting
command=/var/www/nepal-voting/venv/bin/gunicorn \
    nepal_voting.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --timeout 120

user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/nepal-voting.log

environment=PATH="/var/www/nepal-voting/venv/bin",SECRET_KEY="...",DEBUG="False"
```

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start nepal-voting
```

### 7. Setup SSL with Let's Encrypt

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
```

Update Nginx to use SSL:

```bash
sudo nano /etc/nginx/sites-available/nepal-voting
# Add SSL configuration
sudo systemctl restart nginx
```

### 8. Setup Celery

```bash
sudo nano /etc/supervisor/conf.d/nepal-voting-celery.conf
```

```ini
[program:nepal-voting-celery]
directory=/var/www/nepal-voting
command=/var/www/nepal-voting/venv/bin/celery \
    -A nepal_voting worker -l info

user=ubuntu
autostart=true
autorestart=true
stdout_logfile=/var/log/nepal-voting-celery.log
stderr_logfile=/var/log/nepal-voting-celery-error.log

[program:nepal-voting-celery-beat]
directory=/var/www/nepal-voting
command=/var/www/nepal-voting/venv/bin/celery \
    -A nepal_voting beat -l info

user=ubuntu
autostart=true
autorestart=true
stdout_logfile=/var/log/nepal-voting-celery-beat.log
```

---

## Database Backup Strategy

### Automated Backups

```bash
# Create backup script
nano /var/www/nepal-voting/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/backups/nepal-voting"
DB_NAME="nepal_voting_db"
DB_USER="nepal_voting_user"

mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > \
    $BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete
```

```bash
chmod +x /var/www/nepal-voting/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /var/www/nepal-voting/backup.sh
```

---

## Monitoring & Logging

### Sentry Integration

```python
# Add to settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False
)
```

### Health Check Endpoint

```python
# Add to urls.py
path('health/', views.health_check, name='health_check'),
```

---

## Security Best Practices

1. **Keep Dependencies Updated**

   ```bash
   pip install -U pip
   pip install --upgrade -r requirements.txt
   ```

2. **Run Security Checks**

   ```bash
   python manage.py check --deploy
   ```

3. **Monitor Suspicious Activity**
   - Review SuspiciousActivity model daily
   - Set up alerts for repeated failures
   - Monitor login attempts

4. **Regular Audits**
   - Review AuditLog entries weekly
   - Monitor admin actions
   - Check vote encryption integrity

5. **Backup Strategy**
   - Daily automated backups
   - Test restore procedures monthly
   - Store backups off-site

---

## Troubleshooting

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -h your-db-host -U username -d database_name

# Check Django connection
python manage.py dbshell
```

### Celery Issues

```bash
# Check Celery worker status
celery -A nepal_voting inspect active

# Debug Celery tasks
celery -A nepal_voting events
```

### Static Files Issues

```bash
# Collect static files
python manage.py collectstatic --clear --noinput

# Check permissions
ls -la /var/www/nepal-voting/static/
```

### Permission Issues

```bash
# Fix file permissions
sudo chown -R ubuntu:ubuntu /var/www/nepal-voting
chmod -R 755 /var/www/nepal-voting
```
