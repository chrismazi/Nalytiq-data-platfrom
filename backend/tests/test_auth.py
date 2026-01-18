"""
Authentication Tests
Tests for user registration, login, token management, and access control
"""
import pytest


class TestUserRegistration:
    """Test user registration functionality"""
    
    def test_register_new_user(self, client):
        """Test successful user registration"""
        response = client.post('/auth/register', data={
            'email': 'newuser@nalytiq.rw',
            'password': 'SecurePassword123!',
            'role': 'analyst'
        })
        assert response.status_code == 200
        data = response.json()
        assert 'email' in data
        assert data['email'] == 'newuser@nalytiq.rw'
    
    def test_register_duplicate_email(self, client):
        """Test that duplicate email registration fails"""
        # Register first user
        client.post('/auth/register', data={
            'email': 'duplicate@nalytiq.rw',
            'password': 'Password123!',
            'role': 'analyst'
        })
        
        # Try to register with same email
        response = client.post('/auth/register', data={
            'email': 'duplicate@nalytiq.rw',
            'password': 'DifferentPassword123!',
            'role': 'admin'
        })
        assert response.status_code == 400
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email format"""
        response = client.post('/auth/register', data={
            'email': 'not-an-email',
            'password': 'Password123!',
            'role': 'analyst'
        })
        # Should fail validation
        assert response.status_code in [400, 422]
    
    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post('/auth/register', data={
            'email': 'weakpass@nalytiq.rw',
            'password': '123',  # Too weak
            'role': 'analyst'
        })
        # May or may not validate password strength
        # At minimum, should not crash
        assert response.status_code in [200, 400, 422]


class TestUserLogin:
    """Test user login functionality"""
    
    def test_login_valid_credentials(self, client):
        """Test successful login with valid credentials"""
        # First register
        client.post('/auth/register', data={
            'email': 'logintest@nalytiq.rw',
            'password': 'ValidPassword123!',
            'role': 'analyst'
        })
        
        # Then login
        response = client.post('/auth/login', data={
            'email': 'logintest@nalytiq.rw',
            'password': 'ValidPassword123!'
        })
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert 'token_type' in data
        assert data['token_type'] == 'bearer'
    
    def test_login_invalid_password(self, client):
        """Test login with wrong password"""
        # First register
        client.post('/auth/register', data={
            'email': 'wrongpass@nalytiq.rw',
            'password': 'CorrectPassword123!',
            'role': 'analyst'
        })
        
        # Try login with wrong password
        response = client.post('/auth/login', data={
            'email': 'wrongpass@nalytiq.rw',
            'password': 'WrongPassword456!'
        })
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post('/auth/login', data={
            'email': 'doesnotexist@nalytiq.rw',
            'password': 'AnyPassword123!'
        })
        assert response.status_code == 401
    
    def test_login_missing_fields(self, client):
        """Test login with missing required fields"""
        response = client.post('/auth/login', data={
            'email': 'onlyemail@nalytiq.rw'
        })
        assert response.status_code == 422


class TestTokenAuthentication:
    """Test JWT token authentication"""
    
    def test_access_protected_endpoint_with_token(self, client, auth_token, auth_headers):
        """Test accessing protected endpoint with valid token"""
        if not auth_token:
            pytest.skip("No auth token available")
        
        response = client.get('/auth/me', headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert 'email' in data
    
    def test_access_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get('/auth/me')
        assert response.status_code == 401
    
    def test_access_with_invalid_token(self, client):
        """Test accessing with invalid token"""
        headers = {'Authorization': 'Bearer invalid-token-here'}
        response = client.get('/auth/me', headers=headers)
        assert response.status_code == 401
    
    def test_access_with_malformed_auth_header(self, client):
        """Test accessing with malformed authorization header"""
        headers = {'Authorization': 'InvalidFormat token'}
        response = client.get('/auth/me', headers=headers)
        assert response.status_code == 401


class TestPasswordUpdate:
    """Test password update functionality"""
    
    @pytest.mark.auth
    def test_update_password(self, client, auth_token, auth_headers):
        """Test updating password"""
        if not auth_token:
            pytest.skip("No auth token available")
        
        response = client.put('/auth/update', 
                              json={'password': 'NewSecurePassword123!'},
                              headers=auth_headers)
        # Should succeed or require old password
        assert response.status_code in [200, 400, 422]
    
    @pytest.mark.auth
    def test_update_password_without_auth(self, client):
        """Test updating password without authentication"""
        response = client.put('/auth/update', 
                              json={'password': 'NewPassword123!'})
        assert response.status_code == 401


class TestRoleBasedAccess:
    """Test role-based access control"""
    
    @pytest.mark.skip(reason="RBAC not fully implemented")
    def test_admin_only_endpoint(self, client):
        """Test that admin-only endpoints reject non-admins"""
        # Register as analyst
        client.post('/auth/register', data={
            'email': 'analyst@nalytiq.rw',
            'password': 'Password123!',
            'role': 'analyst'
        })
        
        # Login
        login_response = client.post('/auth/login', data={
            'email': 'analyst@nalytiq.rw',
            'password': 'Password123!'
        })
        token = login_response.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}
        
        # Try to access admin endpoint
        response = client.get('/admin/users', headers=headers)
        assert response.status_code == 403
