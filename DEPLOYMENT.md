# Nalytiq Data Platform - Production Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Development Setup](#development-setup)
4. [Production Deployment](#production-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [Configuration](#configuration)
8. [Database Setup](#database-setup)
9. [Monitoring](#monitoring)
10. [Security](#security)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **OS**: Ubuntu 22.04+ / RHEL 8+ / Windows Server 2022
- **CPU**: 4+ cores (8+ recommended for production)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Disk**: 50GB+ SSD

### Software Requirements
- Python 3.12+
- Node.js 20+
- PostgreSQL 16+
- Redis 7+
- Docker 24+ (for containerized deployment)
- Kubernetes 1.28+ (for K8s deployment)

---

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/chrismazi/Nalytiq-data-platfrom.git
cd Nalytiq-data-platfrom
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp env.production.example .env

# Edit .env with your settings
# IMPORTANT: Generate a secure SECRET_KEY:
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Start development server
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
# From project root
npm install
npm run dev
```

### 4. Access Application
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Development Setup

### Database (SQLite - Development)
```bash
# SQLite is configured by default for development
# No additional setup required
```

### Database (PostgreSQL - Development)
```bash
# Start PostgreSQL
docker run -d \
  --name nalytiq-postgres \
  -e POSTGRES_USER=nalytiq \
  -e POSTGRES_PASSWORD=devpassword \
  -e POSTGRES_DB=nalytiq_db \
  -p 5432:5432 \
  postgres:16-alpine

# Update .env
USE_SQLITE=false
POSTGRES_HOST=localhost
POSTGRES_PASSWORD=devpassword
```

### Redis (Optional for Development)
```bash
docker run -d \
  --name nalytiq-redis \
  -p 6379:6379 \
  redis:7-alpine
```

### Run Database Migrations
```bash
cd backend
alembic upgrade head
```

---

## Production Deployment

### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.12 python3.12-venv postgresql-16 redis-server nginx certbot

# Create application user
sudo useradd -m -s /bin/bash nalytiq
sudo mkdir -p /opt/nalytiq
sudo chown nalytiq:nalytiq /opt/nalytiq
```

### 2. Database Setup
```bash
# Create PostgreSQL database
sudo -u postgres psql << EOF
CREATE USER nalytiq WITH PASSWORD 'YOUR_SECURE_PASSWORD';
CREATE DATABASE nalytiq_db OWNER nalytiq;
GRANT ALL PRIVILEGES ON DATABASE nalytiq_db TO nalytiq;
EOF
```

### 3. Application Deployment
```bash
# As nalytiq user
sudo su - nalytiq
cd /opt/nalytiq

# Clone repository
git clone https://github.com/chrismazi/Nalytiq-data-platfrom.git app
cd app/backend

# Setup Python environment
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Configure environment
cp env.production.example .env
# Edit .env with production settings
```

### 4. Systemd Service
```bash
# Create /etc/systemd/system/nalytiq-api.service
sudo cat > /etc/systemd/system/nalytiq-api.service << EOF
[Unit]
Description=Nalytiq API
After=network.target postgresql.service redis.service

[Service]
User=nalytiq
Group=nalytiq
WorkingDirectory=/opt/nalytiq/app/backend
Environment="PATH=/opt/nalytiq/app/backend/venv/bin"
ExecStart=/opt/nalytiq/app/backend/venv/bin/gunicorn main:app \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --access-logfile /var/log/nalytiq/access.log \
    --error-logfile /var/log/nalytiq/error.log

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable nalytiq-api
sudo systemctl start nalytiq-api
```

### 5. Nginx Configuration
```bash
# See nginx/nginx.conf for full configuration
sudo cp nginx/nginx.conf /etc/nginx/nginx.conf
sudo nginx -t
sudo systemctl reload nginx
```

### 6. SSL Certificate
```bash
sudo certbot --nginx -d nalytiq.gov.rw -d api.nalytiq.gov.rw
```

---

## Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
# Set environment variables
export POSTGRES_PASSWORD=your_secure_password
export SECRET_KEY=your_64_char_secret_key

# Start all services
docker-compose -f docker-compose.production.yml up -d

# View logs
docker-compose -f docker-compose.production.yml logs -f api
```

### Scaling
```bash
# Scale API workers
docker-compose -f docker-compose.production.yml up -d --scale api=3
```

---

## Kubernetes Deployment

### 1. Create Namespace
```bash
kubectl create namespace nalytiq
```

### 2. Create Secrets
```bash
kubectl create secret generic nalytiq-secrets \
  --namespace nalytiq \
  --from-literal=postgres-password=YOUR_PASSWORD \
  --from-literal=secret-key=YOUR_SECRET_KEY \
  --from-literal=redis-password=YOUR_REDIS_PASSWORD
```

### 3. Deploy
```bash
kubectl apply -f k8s/ --namespace nalytiq
```

### 4. Check Status
```bash
kubectl get pods -n nalytiq
kubectl get services -n nalytiq
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment mode | `development` |
| `DEBUG` | Debug mode | `false` |
| `SECRET_KEY` | JWT secret (64+ chars) | Required |
| `POSTGRES_HOST` | Database host | `localhost` |
| `POSTGRES_PORT` | Database port | `5432` |
| `POSTGRES_USER` | Database user | `nalytiq` |
| `POSTGRES_PASSWORD` | Database password | Required |
| `POSTGRES_DB` | Database name | `nalytiq_db` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3000"]` |

### Feature Flags

| Flag | Description | Default |
|------|-------------|---------|
| `ENABLE_DOCS` | API documentation | `true` |
| `ENABLE_WEBSOCKETS` | WebSocket support | `true` |
| `ENABLE_ML_TRAINING` | ML training features | `true` |
| `ENABLE_XROAD` | X-Road integration | `true` |

---

## Database Setup

### Create Tables
```bash
cd backend
alembic upgrade head
```

### Create Migration
```bash
alembic revision --autogenerate -m "description"
```

### Backup
```bash
pg_dump -U nalytiq nalytiq_db > backup_$(date +%Y%m%d).sql
```

### Restore
```bash
psql -U nalytiq nalytiq_db < backup_20240118.sql
```

---

## Monitoring

### Prometheus Metrics
- Endpoint: `http://localhost:8000/health/metrics`
- Dashboard: http://localhost:9090

### Grafana
- URL: http://localhost:3001
- Default credentials: admin/admin

### Health Checks
```bash
# Liveness
curl http://localhost:8000/health/live

# Readiness
curl http://localhost:8000/health/ready

# Full health
curl http://localhost:8000/health/
```

### Logs
```bash
# Docker
docker-compose logs -f api

# Systemd
journalctl -u nalytiq-api -f

# File logs
tail -f /var/log/nalytiq/access.log
```

---

## Security

### Security Checklist
- [ ] Generate secure SECRET_KEY (64+ characters)
- [ ] Use strong database passwords
- [ ] Enable HTTPS with valid certificates
- [ ] Configure firewall (allow only 80, 443)
- [ ] Set up regular backups
- [ ] Enable audit logging
- [ ] Configure rate limiting
- [ ] Set up intrusion detection

### Password Policy
- Minimum 12 characters
- Uppercase + lowercase + digits + special
- 90-day expiry
- 5-attempt lockout

### Security Headers
All responses include:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=63072000`

---

## Troubleshooting

### Common Issues

**API not starting**
```bash
# Check logs
journalctl -u nalytiq-api -n 100

# Check port
netstat -tlnp | grep 8000
```

**Database connection failed**
```bash
# Test connection
psql -h localhost -U nalytiq -d nalytiq_db

# Check PostgreSQL status
systemctl status postgresql
```

**Redis connection failed**
```bash
# Test connection
redis-cli ping

# Check Redis status
systemctl status redis
```

**Frontend build failed**
```bash
# Clear cache
rm -rf .next node_modules
npm install
npm run build
```

### Support
- Documentation: https://docs.nalytiq.gov.rw
- Issues: https://github.com/chrismazi/Nalytiq-data-platfrom/issues
- Email: support@nalytiq.gov.rw

---

## License

Copyright © 2024-2026 National Institute of Statistics of Rwanda (NISR)
All rights reserved.
