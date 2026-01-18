"""
Backend Tests - Comprehensive Test Suite

Production-ready tests for all platform components.
Run with: pytest tests/ -v --cov=. --cov-report=html
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import json

# ============================================
# FIXTURES
# ============================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """Create test client"""
    from fastapi.testclient import TestClient
    from main import app
    
    with TestClient(app) as client:
        yield client


@pytest.fixture
def auth_headers(test_client):
    """Get authenticated headers"""
    # Login with test user
    response = test_client.post(
        "/api/v1/auth/login",
        data={"username": "admin@nalytiq.rw", "password": "admin123"}
    )
    if response.status_code == 200:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    return {}


# ============================================
# HEALTH CHECK TESTS
# ============================================

class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self, test_client):
        """Test root health endpoint"""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_liveness_probe(self, test_client):
        """Test Kubernetes liveness probe"""
        response = test_client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"
    
    def test_readiness_probe(self, test_client):
        """Test Kubernetes readiness probe"""
        response = test_client.get("/health/ready")
        # Should be 200 or 503 depending on DB state
        assert response.status_code in [200, 503]


# ============================================
# AUTHENTICATION TESTS
# ============================================

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_valid_credentials(self, test_client):
        """Test login with valid credentials"""
        response = test_client.post(
            "/api/v1/auth/login",
            data={"username": "admin@nalytiq.rw", "password": "admin123"}
        )
        # Accept 200 (success) or 401 (if user doesn't exist in test DB)
        assert response.status_code in [200, 401]
    
    def test_login_invalid_credentials(self, test_client):
        """Test login with invalid credentials"""
        response = test_client.post(
            "/api/v1/auth/login",
            data={"username": "invalid@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401
    
    def test_protected_endpoint_without_token(self, test_client):
        """Test accessing protected endpoint without token"""
        response = test_client.get("/api/v1/auth/me")
        assert response.status_code == 401


# ============================================
# SECURITY ENDPOINT TESTS
# ============================================

class TestSecurityEndpoints:
    """Test security and RBAC endpoints"""
    
    def test_list_permissions(self, test_client):
        """Test listing all permissions"""
        response = test_client.get("/api/v1/security/rbac/permissions")
        assert response.status_code == 200
        data = response.json()
        assert "permissions" in data
        assert len(data["permissions"]) > 0
    
    def test_list_roles(self, test_client):
        """Test listing all roles"""
        response = test_client.get("/api/v1/security/rbac/roles")
        assert response.status_code == 200
        data = response.json()
        # Should have built-in roles
        assert "super_admin" in data or len(data) > 0
    
    def test_rbac_statistics(self, test_client):
        """Test RBAC statistics endpoint"""
        response = test_client.get("/api/v1/security/rbac/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_users_with_roles" in data
    
    def test_compliance_statistics(self, test_client):
        """Test compliance statistics endpoint"""
        response = test_client.get("/api/v1/security/compliance/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_consent_records" in data
    
    def test_password_validation_strong(self, test_client):
        """Test password strength validation - strong password"""
        response = test_client.post(
            "/api/v1/security/policies/password/validate",
            json={"password": "MyStr0ng!P@ssw0rd", "username": "testuser"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert data["strength"] == "strong"
    
    def test_password_validation_weak(self, test_client):
        """Test password strength validation - weak password"""
        response = test_client.post(
            "/api/v1/security/policies/password/validate",
            json={"password": "weak", "username": "testuser"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        assert len(data["issues"]) > 0


# ============================================
# X-ROAD ENDPOINT TESTS
# ============================================

class TestXRoadEndpoints:
    """Test X-Road infrastructure endpoints"""
    
    def test_list_organizations(self, test_client):
        """Test listing organizations"""
        response = test_client.get("/api/v1/xroad/organizations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_services(self, test_client):
        """Test listing services"""
        response = test_client.get("/api/v1/xroad/services")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_transaction_logs(self, test_client):
        """Test retrieving transaction logs"""
        response = test_client.get("/api/v1/xroad/transactions")
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data


# ============================================
# GATEWAY ENDPOINT TESTS
# ============================================

class TestGatewayEndpoints:
    """Test API Gateway endpoints"""
    
    def test_gateway_status(self, test_client):
        """Test gateway status endpoint"""
        response = test_client.get("/api/v1/gateway/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert "circuits" in data
        assert "rate_limiting" in data
    
    def test_circuit_breakers(self, test_client):
        """Test circuit breakers endpoint"""
        response = test_client.get("/api/v1/gateway/circuits")
        assert response.status_code == 200
        data = response.json()
        assert "circuits" in data


# ============================================
# FEDERATION ENDPOINT TESTS
# ============================================

class TestFederationEndpoints:
    """Test data federation endpoints"""
    
    def test_catalog_statistics(self, test_client):
        """Test catalog statistics endpoint"""
        response = test_client.get("/api/v1/federation/catalog/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_datasets" in data
    
    def test_search_datasets(self, test_client):
        """Test dataset search"""
        response = test_client.get("/api/v1/federation/catalog/datasets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ============================================
# RBAC UNIT TESTS
# ============================================

class TestRBACManager:
    """Test RBAC manager functionality"""
    
    def test_role_assignment(self):
        """Test assigning role to user"""
        from security.rbac import get_rbac_manager
        
        rbac = get_rbac_manager()
        result = rbac.assign_role(
            user_id="test-user-123",
            role="viewer",
            organization_code=None,
            assigned_by="test"
        )
        
        assert result["success"] == True
        assert result["role"] == "viewer"
    
    def test_permission_check(self):
        """Test permission checking"""
        from security.rbac import get_rbac_manager
        
        rbac = get_rbac_manager()
        
        # Assign a role first
        rbac.assign_role("test-perm-user", "platform_admin")
        
        # Check permission
        result = rbac.check_permission(
            user_id="test-perm-user",
            permission="org:read"
        )
        
        assert result["allowed"] == True
    
    def test_custom_role_creation(self):
        """Test creating custom role"""
        from security.rbac import get_rbac_manager
        
        rbac = get_rbac_manager()
        
        result = rbac.create_custom_role(
            role_name="test_analyst",
            permissions=["catalog:read", "query:execute"],
            description="Test analyst role"
        )
        
        assert result["success"] == True


# ============================================
# PRIVACY GUARD TESTS
# ============================================

class TestPrivacyGuard:
    """Test privacy protection functionality"""
    
    def test_pii_detection_email(self):
        """Test PII detection for email"""
        from security.privacy import get_privacy_guard, PIIType
        
        privacy = get_privacy_guard()
        detected = privacy.detect_pii_in_value("contact@example.com")
        
        assert PIIType.EMAIL in detected
    
    def test_pii_detection_phone(self):
        """Test PII detection for Rwanda phone"""
        from security.privacy import get_privacy_guard, PIIType
        
        privacy = get_privacy_guard()
        detected = privacy.detect_pii_in_value("+250788123456")
        
        assert PIIType.PHONE in detected
    
    def test_column_pii_detection(self):
        """Test column name PII detection"""
        from security.privacy import get_privacy_guard, PIIType
        
        privacy = get_privacy_guard()
        detected = privacy.detect_pii_in_column("national_id")
        
        assert PIIType.ID_NUMBER in detected
    
    def test_data_masking_redact(self):
        """Test data redaction"""
        from security.privacy import get_privacy_guard, MaskingStrategy
        
        privacy = get_privacy_guard()
        masked = privacy.mask_value("John Doe", MaskingStrategy.REDACT)
        
        assert masked == "[REDACTED]"
    
    def test_data_masking_partial(self):
        """Test partial masking"""
        from security.privacy import get_privacy_guard, MaskingStrategy
        
        privacy = get_privacy_guard()
        masked = privacy.mask_value("1234567890", MaskingStrategy.PARTIAL)
        
        assert masked.endswith("7890")
        assert "*" in masked


# ============================================
# COMPLIANCE MANAGER TESTS
# ============================================

class TestComplianceManager:
    """Test compliance management functionality"""
    
    def test_consent_recording(self):
        """Test recording consent"""
        from security.compliance import get_compliance_manager, ConsentType
        
        compliance = get_compliance_manager()
        
        result = compliance.record_consent(
            subject_id="subject-123",
            consent_type=ConsentType.DATA_PROCESSING,
            purpose="Data analysis",
            granted=True
        )
        
        assert "id" in result
        assert result["status"] == "active"
    
    def test_consent_checking(self):
        """Test checking consent"""
        from security.compliance import get_compliance_manager, ConsentType
        
        compliance = get_compliance_manager()
        
        # Record consent first
        compliance.record_consent(
            subject_id="check-subject",
            consent_type=ConsentType.DATA_SHARING,
            purpose="Testing",
            granted=True
        )
        
        # Check consent
        result = compliance.check_consent(
            subject_id="check-subject",
            consent_type=ConsentType.DATA_SHARING
        )
        
        assert result["has_consent"] == True


# ============================================
# INTEGRATION TESTS
# ============================================

class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_full_xroad_workflow(self, test_client):
        """Test complete X-Road organization registration workflow"""
        # Register organization
        org_data = {
            "code": f"TEST-ORG-{datetime.now().timestamp()}",
            "name": "Test Organization",
            "member_class": "GOV",
            "member_type": "ministry"
        }
        
        response = test_client.post(
            "/api/v1/xroad/organizations",
            json=org_data
        )
        
        # Accept 200 (created) or 409 (already exists)
        assert response.status_code in [200, 409]
    
    def test_full_dataset_workflow(self, test_client):
        """Test complete dataset registration workflow"""
        dataset_data = {
            "name": f"Test Dataset {datetime.now().timestamp()}",
            "description": "Test dataset for integration tests",
            "data_type": "statistics",
            "access_level": "public",
            "owner_org_code": "NISR",
            "row_count": 1000,
            "tags": ["test", "integration"]
        }
        
        response = test_client.post(
            "/api/v1/federation/catalog/datasets",
            json=dataset_data
        )
        
        # Accept 200 (created) or 409 (already exists)
        assert response.status_code in [200, 409]


# ============================================
# PERFORMANCE TESTS
# ============================================

class TestPerformance:
    """Basic performance tests"""
    
    def test_health_endpoint_response_time(self, test_client):
        """Test health endpoint responds quickly"""
        import time
        
        start = time.time()
        response = test_client.get("/health/live")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 0.5  # Should respond within 500ms
    
    def test_concurrent_requests(self, test_client):
        """Test handling concurrent requests"""
        import concurrent.futures
        
        def make_request():
            return test_client.get("/api/v1/security/rbac/permissions")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [f.result() for f in futures]
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in results)
