# Nalytiq Data Platform - API Reference

## Base URL
```
Production: https://api.nalytiq.gov.rw
Development: http://localhost:8000
```

## Authentication

All protected endpoints require a Bearer token:
```http
Authorization: Bearer <access_token>
```

### Login
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=yourpassword
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## Health Endpoints

### Liveness Probe
```http
GET /health/live
```

### Readiness Probe
```http
GET /health/ready
```

### Full Health Check
```http
GET /health/
```

---

## Security & RBAC

### List Permissions
```http
GET /api/v1/security/rbac/permissions
```

### List Roles
```http
GET /api/v1/security/rbac/roles
```

### Assign Role to User
```http
POST /api/v1/security/rbac/users/{user_id}/roles
Content-Type: application/json

{
  "role": "platform_admin",
  "organization_code": null
}
```

### Check Permission
```http
GET /api/v1/security/rbac/check?user_id=xxx&permission=org:read
```

### Validate Password
```http
POST /api/v1/security/policies/password/validate
Content-Type: application/json

{
  "password": "MySecureP@ss123",
  "username": "testuser"
}
```

**Response:**
```json
{
  "valid": true,
  "issues": [],
  "strength_score": 100,
  "strength": "strong"
}
```

### Generate API Key
```http
POST /api/v1/security/policies/api-keys
Content-Type: application/json

{
  "name": "My API Key",
  "organization_code": "NISR",
  "permissions": ["catalog:read", "query:execute"],
  "expires_days": 90
}
```

---

## X-Road Infrastructure

### List Organizations
```http
GET /api/v1/xroad/organizations
```

### Register Organization
```http
POST /api/v1/xroad/organizations
Content-Type: application/json

{
  "code": "MINICT",
  "name": "Ministry of ICT",
  "member_class": "GOV",
  "member_type": "ministry",
  "contact_email": "info@minict.gov.rw"
}
```

### Get Organization
```http
GET /api/v1/xroad/organizations/{org_code}
```

### List Services
```http
GET /api/v1/xroad/services
```

### Register Service
```http
POST /api/v1/xroad/services
Content-Type: application/json

{
  "service_code": "population-stats",
  "name": "Population Statistics API",
  "provider_org_code": "NISR",
  "subsystem_code": "STATISTICS",
  "version": "v1",
  "service_type": "REST",
  "endpoint_url": "https://api.nisr.gov.rw/v1/population"
}
```

### Data Exchange
```http
POST /api/v1/xroad/exchange
Content-Type: application/json

{
  "client_org_code": "MINHEALTH",
  "client_subsystem": "HMIS",
  "service_code": "population-stats",
  "provider_org_code": "NISR",
  "method": "GET",
  "path": "/districts",
  "query_params": {"year": "2024"}
}
```

---

## API Gateway

### Gateway Status
```http
GET /api/v1/gateway/status
```

**Response:**
```json
{
  "status": "operational",
  "timestamp": "2024-01-18T12:00:00Z",
  "circuits": {
    "total": 5,
    "open": 0,
    "open_services": []
  },
  "rate_limiting": {
    "organizations_tracked": 12
  }
}
```

### Circuit Breakers
```http
GET /api/v1/gateway/circuits
```

### Call Service
```http
POST /api/v1/gateway/call
Content-Type: application/json

{
  "target_service": "population-stats",
  "method": "GET",
  "path": "/regions",
  "client_org": "MINHEALTH"
}
```

---

## Data Federation

### Catalog Statistics
```http
GET /api/v1/federation/catalog/statistics
```

**Response:**
```json
{
  "total_datasets": 45,
  "by_access_level": {
    "public": 30,
    "internal": 10,
    "restricted": 5
  },
  "by_type": {
    "statistics": 20,
    "registry": 15,
    "survey": 10
  }
}
```

### Search Datasets
```http
GET /api/v1/federation/catalog/datasets?query=population&type=statistics&access_level=public
```

### Register Dataset
```http
POST /api/v1/federation/catalog/datasets
Content-Type: application/json

{
  "name": "Rwanda Census 2024",
  "description": "National population census data",
  "data_type": "statistics",
  "access_level": "public",
  "owner_org_code": "NISR",
  "row_count": 13500000,
  "tags": ["census", "population", "demographics"]
}
```

### Request Dataset Access
```http
POST /api/v1/federation/sharing/request
Content-Type: application/json

{
  "dataset_id": "dataset-uuid",
  "requester_org_code": "MINHEALTH",
  "purpose": "Health planning analysis",
  "justification": "Required for district-level health resource allocation"
}
```

### Execute Federated Query
```http
POST /api/v1/federation/query
Content-Type: application/json

{
  "dataset_sources": ["dataset-1", "dataset-2"],
  "query_type": "aggregate",
  "aggregations": [
    {"column": "population", "function": "sum"},
    {"column": "age", "function": "avg"}
  ],
  "group_by": ["district"],
  "filters": {"year": 2024},
  "include_provenance": true
}
```

---

## Compliance

### Record Consent
```http
POST /api/v1/security/compliance/consent/{subject_id}
Content-Type: application/json

{
  "consent_type": "data_processing",
  "purpose": "Statistical analysis",
  "granted": true,
  "expiry_days": 365
}
```

### Check Consent
```http
GET /api/v1/security/compliance/consent/check?subject_id=xxx&consent_type=data_processing
```

### Report Data Breach
```http
POST /api/v1/security/compliance/breach
Content-Type: application/json

{
  "description": "Unauthorized access detected",
  "severity": "high",
  "affected_datasets": ["dataset-1"],
  "affected_subjects_count": 1500,
  "data_categories_affected": ["personal", "health"]
}
```

### Generate Compliance Report
```http
GET /api/v1/security/compliance/report?regulation=gdpr&days=30
```

---

## Error Responses

All errors follow this format:
```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "status_code": 422,
    "details": {
      "validation_errors": [
        {"field": "email", "message": "Invalid email format", "type": "value_error"}
      ]
    }
  },
  "metadata": {
    "timestamp": "2024-01-18T12:00:00Z",
    "path": "/api/v1/users",
    "correlation_id": "abc-123-def"
  }
}
```

### Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `authentication_error` | 401 | Invalid or missing credentials |
| `authorization_error` | 403 | Insufficient permissions |
| `not_found` | 404 | Resource not found |
| `validation_error` | 422 | Request validation failed |
| `rate_limit_exceeded` | 429 | Too many requests |
| `internal_error` | 500 | Server error |
| `xroad_error` | 502 | X-Road communication error |

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| API (authenticated) | 1000 | 1 minute |
| API (anonymous) | 100 | 1 minute |
| Login | 5 | 1 minute |
| Data Export | 10 | 1 hour |

---

## Pagination

List endpoints support pagination:
```http
GET /api/v1/federation/catalog/datasets?skip=0&limit=20
```

**Response:**
```json
{
  "items": [...],
  "total": 150,
  "skip": 0,
  "limit": 20,
  "has_more": true
}
```

---

## Webhooks

Configure webhooks for real-time notifications:
```http
POST /api/v1/webhooks
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["dataset.created", "access.approved", "breach.reported"],
  "secret": "your-webhook-secret"
}
```

---

## SDK & Libraries

### Python
```python
from nalytiq import NalytiqClient

client = NalytiqClient(
    base_url="https://api.nalytiq.gov.rw",
    api_key="your-api-key"
)

# Search datasets
datasets = client.catalog.search(query="census", access_level="public")

# Execute query
result = client.federation.query(
    sources=["dataset-1"],
    aggregations=[{"column": "population", "function": "sum"}]
)
```

### JavaScript
```javascript
import { NalytiqClient } from '@nalytiq/sdk';

const client = new NalytiqClient({
  baseUrl: 'https://api.nalytiq.gov.rw',
  apiKey: 'your-api-key'
});

// Search datasets
const datasets = await client.catalog.search({
  query: 'census',
  accessLevel: 'public'
});
```

---

## OpenAPI Specification

Full OpenAPI 3.0 specification available at:
- Swagger UI: https://api.nalytiq.gov.rw/docs
- ReDoc: https://api.nalytiq.gov.rw/redoc
- OpenAPI JSON: https://api.nalytiq.gov.rw/openapi.json
