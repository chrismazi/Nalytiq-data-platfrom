"""
Pytest Configuration and Fixtures
Provides test client, test database, and mock data for all tests
"""
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from fastapi import FastAPI
import pandas as pd
import numpy as np

# Test configuration
TEST_DB_PATH = tempfile.mktemp(suffix='.db')
TEST_UPLOAD_DIR = tempfile.mkdtemp()


@pytest.fixture(scope="session")
def test_app():
    """Create a test FastAPI application"""
    # Set test environment variables
    os.environ['DATABASE_URL'] = f'sqlite:///{TEST_DB_PATH}'
    os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only-minimum-32-chars'
    os.environ['LOG_LEVEL'] = 'ERROR'
    
    # Import main app after setting env vars
    from main import app
    
    yield app
    
    # Cleanup
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    if os.path.exists(TEST_UPLOAD_DIR):
        shutil.rmtree(TEST_UPLOAD_DIR)


@pytest.fixture(scope="session")
def client(test_app):
    """Create a test client"""
    with TestClient(test_app) as c:
        yield c


@pytest.fixture
def sample_csv_data():
    """Generate sample CSV data for testing"""
    np.random.seed(42)
    data = {
        'id': range(1, 101),
        'name': [f'Item_{i}' for i in range(1, 101)],
        'category': np.random.choice(['A', 'B', 'C', 'D'], 100),
        'value': np.random.randint(100, 1000, 100),
        'price': np.round(np.random.uniform(10.0, 100.0, 100), 2),
        'quantity': np.random.randint(1, 50, 100),
        'date': pd.date_range('2024-01-01', periods=100, freq='D').strftime('%Y-%m-%d'),
        'is_active': np.random.choice([True, False], 100),
        'region': np.random.choice(['North', 'South', 'East', 'West'], 100),
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_csv_file(sample_csv_data, tmp_path):
    """Create a temporary CSV file for upload testing"""
    file_path = tmp_path / "test_data.csv"
    sample_csv_data.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def sample_excel_file(sample_csv_data, tmp_path):
    """Create a temporary Excel file for upload testing"""
    file_path = tmp_path / "test_data.xlsx"
    sample_csv_data.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def ml_classification_data():
    """Generate sample data for ML classification testing"""
    np.random.seed(42)
    n_samples = 200
    
    # Create features
    X1 = np.random.randn(n_samples)
    X2 = np.random.randn(n_samples)
    X3 = np.random.randn(n_samples)
    
    # Create target with some relationship to features
    y = ((X1 + X2 - X3) > 0).astype(int)
    
    data = {
        'feature_1': X1,
        'feature_2': X2,
        'feature_3': X3,
        'category_a': np.random.choice(['cat', 'dog', 'bird'], n_samples),
        'category_b': np.random.choice(['high', 'medium', 'low'], n_samples),
        'target': y
    }
    return pd.DataFrame(data)


@pytest.fixture
def ml_regression_data():
    """Generate sample data for ML regression testing"""
    np.random.seed(42)
    n_samples = 200
    
    X1 = np.random.randn(n_samples)
    X2 = np.random.randn(n_samples)
    X3 = np.random.uniform(0, 10, n_samples)
    
    # Target with linear relationship + noise
    y = 3 * X1 + 2 * X2 + 0.5 * X3 + np.random.randn(n_samples) * 0.5
    
    data = {
        'feature_1': X1,
        'feature_2': X2,
        'feature_3': X3,
        'target': y
    }
    return pd.DataFrame(data)


@pytest.fixture
def test_user_credentials():
    """Test user credentials"""
    return {
        'email': 'test@nalytiq.rw',
        'password': 'TestPassword123!'
    }


@pytest.fixture
def auth_token(client, test_user_credentials):
    """Register and login a test user, return the auth token"""
    # Register
    register_response = client.post('/auth/register', data={
        'email': test_user_credentials['email'],
        'password': test_user_credentials['password'],
        'role': 'analyst'
    })
    
    # Login
    login_response = client.post('/auth/login', data={
        'email': test_user_credentials['email'],
        'password': test_user_credentials['password']
    })
    
    if login_response.status_code == 200:
        return login_response.json().get('access_token')
    return None


@pytest.fixture
def auth_headers(auth_token):
    """Return headers with authorization token"""
    if auth_token:
        return {'Authorization': f'Bearer {auth_token}'}
    return {}


@pytest.fixture
def data_with_missing_values():
    """Generate data with missing values for testing cleaning"""
    np.random.seed(42)
    data = {
        'id': range(1, 51),
        'value_a': [None if i % 7 == 0 else np.random.randint(1, 100) for i in range(50)],
        'value_b': [None if i % 5 == 0 else np.random.uniform(10, 50) for i in range(50)],
        'category': [None if i % 10 == 0 else np.random.choice(['X', 'Y', 'Z']) for i in range(50)],
        'complete': list(range(100, 150))
    }
    return pd.DataFrame(data)


@pytest.fixture
def data_with_outliers():
    """Generate data with outliers for testing"""
    np.random.seed(42)
    values = np.random.normal(50, 10, 100)
    # Add outliers
    values[5] = 500  # High outlier
    values[20] = -100  # Low outlier
    values[50] = 1000  # Extreme outlier
    
    data = {
        'id': range(1, 101),
        'value': values,
        'category': np.random.choice(['A', 'B', 'C'], 100)
    }
    return pd.DataFrame(data)


# Markers for test categories
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "auth: marks tests that require authentication")
    config.addinivalue_line("markers", "ml: marks tests for machine learning features")
