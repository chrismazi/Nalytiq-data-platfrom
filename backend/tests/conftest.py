"""
Test fixtures and configuration
"""

import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_client():
    """Create test client for the session"""
    from fastapi.testclient import TestClient
    from main import app
    
    with TestClient(app) as client:
        yield client


@pytest.fixture
def auth_headers(test_client) -> dict:
    """Get authenticated headers"""
    response = test_client.post(
        "/api/v1/auth/login",
        data={"username": "admin@nalytiq.rw", "password": "admin123"}
    )
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def sample_organization() -> dict:
    """Sample organization data"""
    from datetime import datetime
    return {
        "code": f"TEST-{int(datetime.now().timestamp())}",
        "name": "Test Organization",
        "member_class": "GOV",
        "member_type": "agency",
        "contact_email": "test@test.rw"
    }


@pytest.fixture
def sample_dataset() -> dict:
    """Sample dataset data"""
    from datetime import datetime
    return {
        "name": f"Test Dataset {datetime.now().timestamp()}",
        "description": "Test dataset for automated tests",
        "data_type": "statistics",
        "access_level": "public",
        "owner_org_code": "NISR",
        "row_count": 1000,
        "tags": ["test"]
    }


@pytest.fixture
def sample_service() -> dict:
    """Sample service data"""
    from datetime import datetime
    return {
        "service_code": f"test-svc-{int(datetime.now().timestamp())}",
        "name": "Test Service",
        "provider_org_code": "NISR",
        "subsystem_code": "STATISTICS",
        "version": "v1",
        "service_type": "REST"
    }
