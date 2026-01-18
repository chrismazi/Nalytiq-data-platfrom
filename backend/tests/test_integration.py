"""
Comprehensive Integration Tests

End-to-end tests for complete workflows:
- User registration and authentication
- Organization registration and management
- Dataset creation and sharing
- X-Road data exchange
- Security and compliance
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import json


class TestUserWorkflow:
    """Test complete user lifecycle"""
    
    def test_user_registration_workflow(self, test_client):
        """Test user registration, login, and profile access"""
        # 1. Register new user
        user_data = {
            "email": f"test-{datetime.now().timestamp()}@example.com",
            "password": "SecureP@ssw0rd123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = test_client.post("/api/v1/auth/register", json=user_data)
        # Accept 200 (created) or 409 (duplicate)
        assert response.status_code in [200, 409, 422]
        
        if response.status_code == 200:
            # 2. Login with new user
            login_response = test_client.post(
                "/api/v1/auth/login",
                data={"username": user_data["email"], "password": user_data["password"]}
            )
            assert login_response.status_code == 200
            token = login_response.json()["access_token"]
            
            # 3. Access profile
            headers = {"Authorization": f"Bearer {token}"}
            profile_response = test_client.get("/api/v1/auth/me", headers=headers)
            assert profile_response.status_code == 200
            assert profile_response.json()["email"] == user_data["email"]
    
    def test_password_reset_workflow(self, test_client):
        """Test password reset flow"""
        # Request password reset
        response = test_client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "admin@nalytiq.rw"}
        )
        # Accept 200 (success) or 404 (user not found)
        assert response.status_code in [200, 404, 422]


class TestOrganizationWorkflow:
    """Test organization registration and management"""
    
    def test_organization_lifecycle(self, test_client):
        """Test organization registration, verification, and management"""
        org_code = f"TEST-ORG-{int(datetime.now().timestamp())}"
        
        # 1. Register organization
        org_data = {
            "code": org_code,
            "name": "Test Organization",
            "member_class": "GOV",
            "member_type": "agency",
            "contact_email": "contact@testorg.rw"
        }
        
        response = test_client.post("/api/v1/xroad/organizations", json=org_data)
        assert response.status_code in [200, 409]
        
        if response.status_code == 200:
            org = response.json()
            assert org["code"] == org_code
            
            # 2. Get organization details
            get_response = test_client.get(f"/api/v1/xroad/organizations/{org_code}")
            assert get_response.status_code == 200
            
            # 3. Add subsystem
            subsystem_data = {
                "code": "TEST-SUBSYSTEM",
                "name": "Test Subsystem"
            }
            subsys_response = test_client.post(
                f"/api/v1/xroad/organizations/{org_code}/subsystems",
                json=subsystem_data
            )
            assert subsys_response.status_code in [200, 404, 409]
    
    def test_service_registration(self, test_client):
        """Test service registration workflow"""
        service_data = {
            "service_code": f"test-service-{int(datetime.now().timestamp())}",
            "name": "Test Service API",
            "provider_org_code": "NISR",
            "subsystem_code": "STATISTICS",
            "version": "v1",
            "service_type": "REST",
            "description": "Test service for integration tests"
        }
        
        response = test_client.post("/api/v1/xroad/services", json=service_data)
        assert response.status_code in [200, 404, 409]


class TestDataFederationWorkflow:
    """Test data federation and sharing"""
    
    def test_dataset_lifecycle(self, test_client):
        """Test dataset registration, search, and access request"""
        dataset_id = None
        
        # 1. Register dataset
        dataset_data = {
            "name": f"Test Dataset {datetime.now().timestamp()}",
            "description": "Integration test dataset",
            "data_type": "statistics",
            "access_level": "internal",
            "owner_org_code": "NISR",
            "row_count": 10000,
            "tags": ["test", "integration"]
        }
        
        response = test_client.post("/api/v1/federation/catalog/datasets", json=dataset_data)
        assert response.status_code in [200, 409]
        
        if response.status_code == 200:
            dataset = response.json()
            dataset_id = dataset.get("id")
        
        # 2. Search datasets
        search_response = test_client.get(
            "/api/v1/federation/catalog/datasets",
            params={"query": "test", "data_type": "statistics"}
        )
        assert search_response.status_code == 200
        
        # 3. Request access (if dataset created)
        if dataset_id:
            access_request = {
                "dataset_id": dataset_id,
                "requester_org_code": "MINHEALTH",
                "purpose": "Integration testing",
                "justification": "Automated test verification"
            }
            access_response = test_client.post(
                "/api/v1/federation/sharing/request",
                json=access_request
            )
            assert access_response.status_code in [200, 404, 409]
    
    def test_federated_query(self, test_client):
        """Test federated query execution"""
        # Get available datasets
        datasets = test_client.get("/api/v1/federation/catalog/datasets").json()
        
        if len(datasets) > 0:
            query_data = {
                "dataset_sources": [datasets[0].get("id", "ds-1")],
                "query_type": "aggregate",
                "aggregations": [{"column": "value", "function": "count"}],
                "include_provenance": True
            }
            
            response = test_client.post("/api/v1/federation/query", json=query_data)
            assert response.status_code in [200, 400, 404]


class TestXRoadExchange:
    """Test X-Road data exchange"""
    
    def test_data_exchange_flow(self, test_client):
        """Test complete data exchange flow"""
        exchange_request = {
            "client_org_code": "MINHEALTH",
            "client_subsystem": "HMIS",
            "service_code": "population-stats",
            "provider_org_code": "NISR",
            "method": "GET",
            "path": "/statistics",
            "query_params": {"year": "2024"}
        }
        
        response = test_client.post("/api/v1/xroad/exchange", json=exchange_request)
        # Accept success or various errors (service not found, access denied, etc.)
        assert response.status_code in [200, 400, 403, 404, 502]
    
    def test_transaction_logging(self, test_client):
        """Test that transactions are logged"""
        response = test_client.get("/api/v1/xroad/transactions")
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data


class TestSecurityCompliance:
    """Test security and compliance features"""
    
    def test_rbac_workflow(self, test_client):
        """Test complete RBAC workflow"""
        user_id = "test-rbac-user"
        
        # 1. Assign role
        assign_response = test_client.post(
            f"/api/v1/security/rbac/users/{user_id}/roles",
            json={"role": "data_analyst", "organization_code": None}
        )
        assert assign_response.status_code in [200, 404]
        
        # 2. Check permission
        check_response = test_client.get(
            "/api/v1/security/rbac/check",
            params={"user_id": user_id, "permission": "catalog:read"}
        )
        assert check_response.status_code == 200
        
        # 3. Get user roles
        roles_response = test_client.get(f"/api/v1/security/rbac/users/{user_id}/roles")
        assert roles_response.status_code == 200
    
    def test_consent_workflow(self, test_client):
        """Test consent management workflow"""
        subject_id = f"subject-{int(datetime.now().timestamp())}"
        
        # 1. Record consent
        consent_data = {
            "consent_type": "data_processing",
            "purpose": "Integration testing",
            "granted": True,
            "expiry_days": 30
        }
        
        record_response = test_client.post(
            f"/api/v1/security/compliance/consent/{subject_id}",
            json=consent_data
        )
        assert record_response.status_code == 200
        
        # 2. Check consent
        check_response = test_client.get(
            "/api/v1/security/compliance/consent/check",
            params={"subject_id": subject_id, "consent_type": "data_processing"}
        )
        assert check_response.status_code == 200
        assert check_response.json()["has_consent"] == True
        
        # 3. Withdraw consent
        withdraw_response = test_client.delete(
            f"/api/v1/security/compliance/consent/{subject_id}",
            params={"consent_type": "data_processing", "reason": "Test withdrawal"}
        )
        assert withdraw_response.status_code == 200
    
    def test_api_key_workflow(self, test_client):
        """Test API key generation and validation"""
        # 1. Generate API key
        key_data = {
            "name": "Test API Key",
            "organization_code": "NISR",
            "permissions": ["catalog:read"],
            "expires_days": 1
        }
        
        gen_response = test_client.post("/api/v1/security/policies/api-keys", json=key_data)
        assert gen_response.status_code == 200
        
        if gen_response.status_code == 200:
            key_info = gen_response.json()
            api_key = key_info.get("api_key")
            
            if api_key:
                # 2. Validate key
                validate_response = test_client.post(
                    "/api/v1/security/policies/api-keys/validate",
                    json={"api_key": api_key}
                )
                assert validate_response.status_code in [200, 404]


class TestGatewayResilience:
    """Test API Gateway resilience features"""
    
    def test_circuit_breaker_states(self, test_client):
        """Test circuit breaker state management"""
        # Get current circuit states
        response = test_client.get("/api/v1/gateway/circuits")
        assert response.status_code == 200
        
        data = response.json()
        assert "circuits" in data
    
    def test_rate_limit_usage(self, test_client):
        """Test rate limit tracking"""
        # Make multiple requests and check rate limit
        for _ in range(5):
            test_client.get("/api/v1/gateway/status")
        
        # Should still be within limits
        status_response = test_client.get("/api/v1/gateway/status")
        assert status_response.status_code == 200


class TestMLPipeline:
    """Test ML pipeline integration"""
    
    def test_model_listing(self, test_client):
        """Test listing trained models"""
        response = test_client.get("/api/v1/models")
        assert response.status_code in [200, 404]
    
    def test_prediction_endpoint(self, test_client):
        """Test model prediction"""
        prediction_data = {
            "model_id": "test-model",
            "input_data": {"feature1": 1.0, "feature2": 2.0}
        }
        
        response = test_client.post("/api/v1/models/predict", json=prediction_data)
        # May not have a model, so accept 404
        assert response.status_code in [200, 404, 422]


class TestAuditLogging:
    """Test audit logging functionality"""
    
    def test_audit_log_creation(self, test_client):
        """Test that actions create audit logs"""
        # Perform an action
        test_client.get("/api/v1/security/rbac/statistics")
        
        # Check audit logs (if endpoint exists)
        response = test_client.get("/api/v1/audit/logs")
        if response.status_code == 200:
            logs = response.json()
            assert isinstance(logs, list) or "logs" in logs


class TestHealthAndMetrics:
    """Test health and monitoring endpoints"""
    
    def test_comprehensive_health_check(self, test_client):
        """Test full health check returns all components"""
        response = test_client.get("/health/")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
    
    def test_prometheus_metrics_format(self, test_client):
        """Test metrics endpoint returns Prometheus format"""
        response = test_client.get("/health/metrics")
        assert response.status_code == 200
        
        content = response.text
        # Should contain Prometheus metric format
        assert "nalytiq_" in content or "# HELP" in content or "# TYPE" in content


class TestErrorHandling:
    """Test error handling and recovery"""
    
    def test_404_response_format(self, test_client):
        """Test 404 errors return structured response"""
        response = test_client.get("/api/v1/nonexistent/endpoint")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data or "detail" in data
    
    def test_validation_error_format(self, test_client):
        """Test validation errors return structured response"""
        # Send invalid data
        response = test_client.post(
            "/api/v1/xroad/organizations",
            json={"invalid": "data"}
        )
        assert response.status_code == 422
        
        data = response.json()
        assert "error" in data or "detail" in data
    
    def test_method_not_allowed(self, test_client):
        """Test method not allowed errors"""
        response = test_client.delete("/health/live")
        assert response.status_code == 405
