# Deployment Guide - Nalytiq Platform

##  Production Deployment Checklist

### **Pre-Deployment Steps**

#### 1. **Environment Configuration** 
- [ ] Copy `env.example` to `.env.local` (frontend)
- [ ] Copy `backend/env.example` to `backend/.env`
- [ ] Update `SECRET_KEY` with a strong 32+ character key
- [ ] Configure `CORS_ORIGINS` with your production domain
- [ ] Set `LOG_LEVEL` to `WARNING` or `ERROR` for production
- [ ] Configure database URL if using external database

#### 2. **Security Hardening**
- [ ] Generate secure `SECRET_KEY`: `openssl rand -hex 32`
- [ ] Update CORS to only allow your frontend domain
- [ ] Enable HTTPS in production
- [ ] Set up rate limiting
- [ ] Configure CSP headers
- [ ] Enable security headers (HSTS, X-Frame-Options, etc.)

#### 3. **Dependencies**
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
npm install --legacy-peer-deps
```

#### 4. **Build Frontend**
```bash
npm run build
```

---

##  Docker Deployment

### **Backend Dockerfile**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create log directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Frontend Dockerfile**
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy application
COPY . .

# Build
RUN npm run build

# Production image
FROM node:18-alpine

WORKDIR /app

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/next.config.mjs ./

RUN npm install --production --legacy-peer-deps

EXPOSE 3000

CMD ["npm", "start"]
```

### **Docker Compose**
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - LOG_LEVEL=INFO
    volumes:
      - ./backend/logs:/app/logs
      - ./backend/users.db:/app/users.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3

  frontend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_BACKEND_URL=http://backend:8000
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
```

---

##  Cloud Deployment Options

### **Option 1: Vercel (Frontend) + Railway/Render (Backend)**

#### **Frontend on Vercel**
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod

# Set environment variables in Vercel dashboard
# NEXT_PUBLIC_BACKEND_URL=https://your-backend.railway.app
```

#### **Backend on Railway**
1. Connect GitHub repository
2. Select `backend` directory
3. Add environment variables in Railway dashboard
4. Deploy automatically on push

### **Option 2: AWS Deployment**

#### **Backend on AWS Elastic Beanstalk**
```bash
# Install EB CLI
pip install awsebcli

# Initialize
cd backend
eb init -p python-3.10 nalytiq-backend

# Create environment
eb create nalytiq-prod

# Deploy
eb deploy
```

#### **Frontend on AWS Amplify**
1. Connect to GitHub repository
2. Configure build settings
3. Add environment variables
4. Deploy

### **Option 3: DigitalOcean App Platform**

**app.yaml**
```yaml
name: nalytiq
services:
  - name: backend
    dockerfile_path: backend/Dockerfile
    github:
      repo: your-repo/nisr-data-platform
      branch: main
      deploy_on_push: true
    envs:
      - key: SECRET_KEY
        value: ${SECRET_KEY}
      - key: CORS_ORIGINS
        value: ${FRONTEND_URL}
    http_port: 8000
    health_check:
      http_path: /health

  - name: frontend
    dockerfile_path: Dockerfile
    github:
      repo: your-repo/nisr-data-platform
      branch: main
    envs:
      - key: NEXT_PUBLIC_BACKEND_URL
        value: ${BACKEND_URL}
    http_port: 3000
    routes:
      - path: /
```

---

##  SSL/HTTPS Configuration

### **Let's Encrypt with Nginx**
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d nalytiq.rw -d www.nalytiq.rw

# Auto-renewal
sudo certbot renew --dry-run
```

### **Nginx Configuration**
```nginx
# /etc/nginx/sites-available/nalytiq
server {
    listen 80;
    server_name nalytiq.rw www.nalytiq.rw;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name nalytiq.rw www.nalytiq.rw;

    ssl_certificate /etc/letsencrypt/live/nalytiq.rw/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/nalytiq.rw/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

##  Monitoring & Logging

### **Application Logging**
- Logs are stored in `backend/app.log`
- Rotation: 10MB per file, 5 backup files
- Configure log shipping to services like:
  - AWS CloudWatch
  - Datadog
  - Loggly
  - Papertrail

### **Health Checks**
- Backend: `GET /health`
- Database status included in health response
- Set up uptime monitoring with:
  - UptimeRobot
  - Pingdom
  - Better Uptime

### **Error Tracking**
```typescript
// Add Sentry integration (optional)
// Install: npm install @sentry/nextjs

// next.config.mjs
import { withSentryConfig } from '@sentry/nextjs';

const config = {
  // ... your config
};

export default withSentryConfig(config, {
  org: "your-org",
  project: "nalytiq",
});
```

---

##  Database Migration

### **SQLite to PostgreSQL (Recommended for Production)**

1. **Install PostgreSQL**
```bash
pip install psycopg2-binary
```

2. **Update `backend/config.py`**
```python
DATABASE_URL: str = os.getenv(
    "DATABASE_URL", 
    "postgresql://user:password@localhost/nalytiq"
)
```

3. **Migrate Data**
```python
# migration script
import sqlite3
import psycopg2

# Connect to SQLite
sqlite_conn = sqlite3.connect('users.db')
sqlite_cur = sqlite_conn.cursor()

# Connect to PostgreSQL
pg_conn = psycopg2.connect(DATABASE_URL)
pg_cur = pg_conn.cursor()

# Create table
pg_cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL
    )
""")

# Migrate data
sqlite_cur.execute("SELECT email, password, role FROM users")
for row in sqlite_cur.fetchall():
    pg_cur.execute(
        "INSERT INTO users (email, password, role) VALUES (%s, %s, %s)",
        row
    )

pg_conn.commit()
```

---

##  CI/CD Pipeline

### **GitHub Actions**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run tests
        run: pytest

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Railway
        uses: railway-app/cli@v1
        with:
          railway-token: ${{ secrets.RAILWAY_TOKEN }}
          service: backend

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          vercel-args: '--prod'
```

---

##  Performance Optimization

### **Backend**
```python
# Add caching
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_computation(data):
    # Your expensive operation
    pass
```

### **Frontend**
```typescript
// Use React.memo for expensive components
export const ExpensiveComponent = React.memo(({ data }) => {
  // Component logic
});

// Lazy load routes
const Dashboard = lazy(() => import('./pages/dashboard'));
```

---

##  Post-Deployment Verification

- [ ] All endpoints return expected responses
- [ ] Health check endpoint returns 200
- [ ] File uploads work correctly
- [ ] Authentication flow works
- [ ] Data export functionality works
- [ ] Charts render properly
- [ ] Error handling displays user-friendly messages
- [ ] Toast notifications appear
- [ ] Mobile responsiveness verified
- [ ] SSL certificate valid
- [ ] CORS configured correctly
- [ ] Logs being written
- [ ] Monitoring alerts configured

---

## Troubleshooting

### **Common Issues**

**Backend won't start**
```bash
# Check logs
tail -f backend/app.log

# Verify dependencies
pip list

# Check port
lsof -i :8000
```

**Frontend build fails**
```bash
# Clear cache
rm -rf .next node_modules
npm install --legacy-peer-deps
npm run build
```

**Database connection issues**
```bash
# Check database
sqlite3 backend/users.db ".tables"

# Test connection
python -c "import sqlite3; print('OK')"
```

---

##  Support

For deployment issues:
- Email: support@nalytiq.rw
- Documentation: /README.md
- Issues: GitHub Issues

---

**Deployment prepared by:** Chris Mazimpaka  
**Last updated:** 2025-01-29  
**Version:** 1.0.0
