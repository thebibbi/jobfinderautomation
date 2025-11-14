# Docker Setup Guide

Complete guide to running the Job Automation System with Docker.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                  (job-automation)                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────┐    ┌──────────┐    ┌──────────────┐   │
│  │  Frontend  │───→│ Backend  │───→│  PostgreSQL  │   │
│  │  (Next.js) │    │(FastAPI) │    │              │   │
│  │   :3000    │    │  :8000   │    │    :5432     │   │
│  └────────────┘    └──────┬───┘    └──────────────┘   │
│                           │                             │
│                           ↓                             │
│                    ┌──────────┐                         │
│                    │  Redis   │                         │
│                    │  Cache   │                         │
│                    │  :6379   │                         │
│                    └──────────┘                         │
│                           │                             │
│                           ↓                             │
│                    ┌──────────┐                         │
│                    │  Celery  │                         │
│                    │  Worker  │                         │
│                    └──────────┘                         │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| **frontend** | 3000 | Next.js web dashboard |
| **backend** | 8000 | FastAPI REST API & WebSocket server |
| **db** | 5432 | PostgreSQL database |
| **redis** | 6379 | Redis cache |
| **celery_worker** | - | Background task processor |
| **nginx** (optional) | 80/443 | Reverse proxy (production) |

## Prerequisites

- Docker 24.0+ ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose 2.0+ (included with Docker Desktop)
- 4GB+ RAM available
- 10GB+ disk space

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/jobfinderautomation.git
cd jobfinderautomation
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Minimum Required Configuration**:
```env
# Database
DATABASE_NAME=jobautomation
DATABASE_USER=postgres
DATABASE_PASSWORD=change_this_password

# Security
SECRET_KEY=generate_random_string_here

# Google OAuth (for Calendar/Drive integration)
GOOGLE_OAUTH_CREDENTIALS_PATH=/app/credentials/google_oauth_credentials.json
```

### 3. Start All Services

```bash
# Build and start all containers
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 4. Initialize Database

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head

# (Optional) Seed with sample data
docker-compose exec backend python scripts/seed_data.py
```

### 5. Access Services

- **Web Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

### 6. Load Chrome Extension

```bash
# Extension is in the `extension/` directory
# Open Chrome → Extensions → Load unpacked → Select extension/
```

---

## Environment Variables

### Required Variables

```env
# Database Configuration
DATABASE_NAME=jobautomation
DATABASE_USER=postgres
DATABASE_PASSWORD=your_secure_password

# Redis Configuration (defaults work for Docker)
REDIS_HOST=redis
REDIS_PORT=6379

# Security
SECRET_KEY=generate_with_python_secrets_token_urlsafe_32

# Google OAuth
GOOGLE_OAUTH_CREDENTIALS_PATH=/app/credentials/google_oauth_credentials.json
```

### Optional Variables

```env
# Environment
ENVIRONMENT=development  # or production

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your_app_password

# External APIs (for company research)
CLEARBIT_API_KEY=your_clearbit_key
CRUNCHBASE_API_KEY=your_crunchbase_key
```

### Generating Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Docker Commands

### Starting Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d backend

# Start with logs visible
docker-compose up

# Rebuild and start
docker-compose up -d --build
```

### Stopping Services

```bash
# Stop all services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (deletes data!)
docker-compose down -v
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Executing Commands

```bash
# Run command in backend container
docker-compose exec backend python script.py

# Open shell in backend container
docker-compose exec backend bash

# Run database migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### Monitoring

```bash
# View running containers
docker-compose ps

# View resource usage
docker stats

# View container details
docker-compose logs backend
```

---

## Development Workflow

### Hot Reload (Development Mode)

Both backend and frontend support hot reload:

**Backend** (already configured):
```yaml
# docker-compose.yml
backend:
  volumes:
    - ./backend:/app  # Source code mounted
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend** (uncomment in docker-compose.yml):
```yaml
frontend:
  volumes:
    - ./frontend:/app
    - /app/node_modules
  command: npm run dev
```

Changes to source code will automatically reload the service.

### Running Tests

```bash
# Backend tests
docker-compose exec backend pytest

# With coverage
docker-compose exec backend pytest --cov=app --cov-report=html

# Specific test file
docker-compose exec backend pytest tests/test_api/test_jobs.py

# Frontend tests (when implemented)
docker-compose exec frontend npm test
```

### Database Operations

```bash
# Access PostgreSQL CLI
docker-compose exec db psql -U postgres -d jobautomation

# Backup database
docker-compose exec db pg_dump -U postgres jobautomation > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres jobautomation < backup.sql

# View database logs
docker-compose logs db
```

### Redis Operations

```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# View cache keys
docker-compose exec redis redis-cli KEYS "*"

# Flush cache (clear all)
docker-compose exec redis redis-cli FLUSHALL

# View cache stats
docker-compose exec redis redis-cli INFO stats
```

---

## Production Deployment

### 1. Update Environment Variables

```env
ENVIRONMENT=production
DATABASE_PASSWORD=very_secure_password_here
SECRET_KEY=production_secret_key_32_chars_min
ALLOWED_ORIGINS=https://yourdomain.com
```

### 2. Use Production Docker Compose

```bash
# Use production override
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. Enable Nginx Reverse Proxy

```bash
# Start with nginx profile
docker-compose --profile production up -d
```

### 4. SSL/TLS Configuration

Create `nginx/nginx.conf`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # Frontend
    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }

    # WebSocket
    location /api/v1/ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
}
```

### 5. Health Checks

All services have health checks configured:

```bash
# Check health status
docker-compose ps

# Healthy services show:
# job-automation-backend   Up (healthy)
```

---

## Troubleshooting

### Backend Not Starting

**Problem**: Backend exits with database connection error

**Solution**:
```bash
# Check if database is healthy
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db

# Wait for health check, then restart backend
docker-compose restart backend
```

### Frontend Not Building

**Problem**: Frontend fails to build

**Solution**:
```bash
# Clear build cache
docker-compose build --no-cache frontend

# Check logs
docker-compose logs frontend

# Install dependencies manually
docker-compose run frontend npm install
```

### Port Already in Use

**Problem**: Port 3000 or 8000 already in use

**Solution**:
```bash
# Change ports in docker-compose.yml
# Frontend: "3001:3000" instead of "3000:3000"
# Backend: "8001:8000" instead of "8000:8000"

# Or stop conflicting service
lsof -ti:3000 | xargs kill
```

### Database Migration Fails

**Problem**: Alembic migration fails

**Solution**:
```bash
# Check current revision
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history

# Downgrade if needed
docker-compose exec backend alembic downgrade -1

# Upgrade again
docker-compose exec backend alembic upgrade head
```

### Redis Connection Issues

**Problem**: Backend can't connect to Redis

**Solution**:
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Restart Redis
docker-compose restart redis
```

### WebSocket Not Connecting

**Problem**: WebSocket connection fails in browser

**Solution**:
1. Check backend logs: `docker-compose logs backend`
2. Verify CORS settings in .env: `ALLOWED_ORIGINS=http://localhost:3000`
3. Check firewall rules
4. Test WebSocket endpoint: `wscat -c ws://localhost:8000/api/v1/ws`

### Out of Memory

**Problem**: Containers crashing with OOM

**Solution**:
```bash
# Increase Docker memory limit
# Docker Desktop → Settings → Resources → Memory: 4GB+

# Or limit service memory in docker-compose.yml:
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
```

---

## Monitoring & Maintenance

### View Resource Usage

```bash
# Real-time stats
docker stats

# Disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

### Backup Strategy

```bash
# Backup script (backup.sh)
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
docker-compose exec -T db pg_dump -U postgres jobautomation > "backups/db_$DATE.sql"

# Backup uploads
docker cp job-automation-backend:/app/uploads "backups/uploads_$DATE"

# Backup credentials
tar -czf "backups/credentials_$DATE.tar.gz" credentials/

echo "Backup completed: $DATE"
```

### Log Rotation

```bash
# Configure in docker-compose.yml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## Performance Tuning

### PostgreSQL

```bash
# Increase shared_buffers
docker-compose exec db psql -U postgres -c "ALTER SYSTEM SET shared_buffers = '256MB';"
docker-compose restart db
```

### Redis

```bash
# Increase max memory
docker-compose exec redis redis-cli CONFIG SET maxmemory 512mb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Backend (Uvicorn Workers)

```yaml
# docker-compose.yml
backend:
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Scaling

### Horizontal Scaling

```bash
# Scale celery workers
docker-compose up -d --scale celery_worker=3

# Scale backend (behind load balancer)
docker-compose up -d --scale backend=2
```

### Load Balancing

Add nginx service for load balancing multiple backend instances.

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/docker.yml
name: Docker Build

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build images
        run: docker-compose build

      - name: Run tests
        run: docker-compose run backend pytest

      - name: Push to registry
        run: |
          docker tag backend:latest registry.com/backend:latest
          docker push registry.com/backend:latest
```

---

## Clean Start (Reset Everything)

```bash
# Stop and remove everything
docker-compose down -v

# Remove all images
docker rmi $(docker images -q jobfinderautomation*)

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d

# Initialize database
docker-compose exec backend alembic upgrade head
```

---

## Support

- **Documentation**: [docs/](./docs/)
- **Issues**: GitHub Issues
- **Docker Hub**: (future)
- **Docker Logs**: `docker-compose logs -f`

## Next Steps

1. ✅ Services running: `docker-compose ps`
2. 🌐 Open dashboard: http://localhost:3000
3. 📚 Read API docs: http://localhost:8000/docs
4. 🧪 Run tests: `docker-compose exec backend pytest`
5. 🔧 Configure Google OAuth for Calendar integration
