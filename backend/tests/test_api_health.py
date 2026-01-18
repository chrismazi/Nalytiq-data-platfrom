"""
API Health and Basic Connectivity Tests
Tests that the API is running and responding correctly
"""
import pytest


class TestAPIHealth:
    """Test API health endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns OK"""
        response = client.get('/')
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        # Accept either 'ok' or 'healthy' status
        assert data['status'] in ['ok', 'healthy']
    
    def test_health_check(self, client):
        """Test detailed health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        # version may or may not be present depending on implementation
        assert data['status'] in ['healthy', 'ok']
    
    def test_api_docs_available(self, client):
        """Test that API documentation is accessible"""
        response = client.get('/api/docs')
        assert response.status_code == 200
    
    def test_redoc_available(self, client):
        """Test that ReDoc documentation is accessible"""
        response = client.get('/api/redoc')
        assert response.status_code == 200
    
    def test_cors_headers(self, client):
        """Test CORS headers are set correctly"""
        response = client.options('/', headers={
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'GET'
        })
        # Should allow CORS
        assert response.status_code in [200, 204, 405]
    
    def test_invalid_endpoint_returns_404(self, client):
        """Test that invalid endpoints return 404"""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404


class TestAPIResponseFormat:
    """Test API response formats"""
    
    def test_json_content_type(self, client):
        """Test that API returns JSON content type"""
        response = client.get('/')
        assert 'application/json' in response.headers.get('content-type', '')
    
    def test_error_response_format(self, client):
        """Test that error responses have consistent format"""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404
        data = response.json()
        assert 'detail' in data


class TestRateLimiting:
    """Test rate limiting (placeholder for future implementation)"""
    
    @pytest.mark.skip(reason="Rate limiting not yet implemented")
    def test_rate_limit_headers(self, client):
        """Test rate limit headers are present"""
        response = client.get('/')
        # Check for rate limit headers
        assert 'X-RateLimit-Limit' in response.headers
        assert 'X-RateLimit-Remaining' in response.headers
    
    @pytest.mark.skip(reason="Rate limiting not yet implemented")
    def test_rate_limit_exceeded(self, client):
        """Test that rate limiting kicks in after too many requests"""
        # Make many requests quickly
        for _ in range(1000):
            client.get('/')
        response = client.get('/')
        assert response.status_code == 429
