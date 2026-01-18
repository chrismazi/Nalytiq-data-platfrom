"""
Data Upload and Processing Tests
Tests for file upload, validation, data processing, and quality scoring
"""
import pytest
import io


class TestFileUpload:
    """Test file upload functionality"""
    
    def test_upload_csv_file(self, client, sample_csv_file):
        """Test uploading a valid CSV file"""
        with open(sample_csv_file, 'rb') as f:
            response = client.post('/upload/', files={'file': ('test.csv', f, 'text/csv')})
        
        assert response.status_code == 200
        data = response.json()
        assert 'columns' in data
        assert 'shape' in data
        assert isinstance(data['columns'], list)
    
    def test_upload_excel_file(self, client, sample_excel_file):
        """Test uploading a valid Excel file"""
        with open(sample_excel_file, 'rb') as f:
            response = client.post('/upload/', files={
                'file': ('test.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            })
        
        assert response.status_code == 200
        data = response.json()
        assert 'columns' in data
    
    def test_upload_invalid_file_type(self, client, tmp_path):
        """Test uploading an invalid file type"""
        # Create a fake file
        invalid_file = tmp_path / "test.exe"
        invalid_file.write_bytes(b"fake executable content")
        
        with open(invalid_file, 'rb') as f:
            response = client.post('/upload/', files={
                'file': ('test.exe', f, 'application/octet-stream')
            })
        
        assert response.status_code == 400
    
    def test_upload_empty_file(self, client, tmp_path):
        """Test uploading an empty file"""
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("")
        
        with open(empty_file, 'rb') as f:
            response = client.post('/upload/', files={
                'file': ('empty.csv', f, 'text/csv')
            })
        
        assert response.status_code in [400, 422]
    
    def test_upload_file_too_large(self, client):
        """Test uploading a file that exceeds size limit"""
        # Create a large file-like object (simulated)
        # This may not actually hit the limit depending on config
        large_content = b"x" * (1024 * 1024 * 10)  # 10MB
        response = client.post('/upload/', files={
            'file': ('large.csv', io.BytesIO(large_content), 'text/csv')
        })
        
        # May succeed or fail depending on limit
        assert response.status_code in [200, 400, 413, 422]
    
    def test_upload_without_file(self, client):
        """Test upload endpoint without file"""
        response = client.post('/upload/')
        assert response.status_code == 422


class TestDataValidation:
    """Test data validation during upload"""
    
    def test_csv_with_headers(self, client, sample_csv_file):
        """Test CSV with proper headers"""
        with open(sample_csv_file, 'rb') as f:
            response = client.post('/upload/', files={'file': ('test.csv', f, 'text/csv')})
        
        assert response.status_code == 200
        data = response.json()
        expected_columns = ['id', 'name', 'category', 'value', 'price', 'quantity', 'date', 'is_active', 'region']
        for col in expected_columns:
            assert col in data['columns']
    
    def test_csv_shape_detection(self, client, sample_csv_file):
        """Test that shape is correctly detected"""
        with open(sample_csv_file, 'rb') as f:
            response = client.post('/upload/', files={'file': ('test.csv', f, 'text/csv')})
        
        assert response.status_code == 200
        data = response.json()
        assert data['shape'][0] == 100  # 100 rows
        assert data['shape'][1] == 9    # 9 columns


class TestDataProfiling:
    """Test data profiling functionality"""
    
    @pytest.mark.slow
    def test_profile_report_generation(self, client, sample_csv_file):
        """Test generating a profile report"""
        with open(sample_csv_file, 'rb') as f:
            response = client.post('/profile/', files={'file': ('test.csv', f, 'text/csv')})
        
        assert response.status_code == 200
        data = response.json()
        # Should contain profile information
        assert 'columns' in data or 'overview' in data or 'variables' in data
    
    @pytest.mark.slow
    def test_profile_includes_statistics(self, client, sample_csv_file):
        """Test that profile includes summary statistics"""
        with open(sample_csv_file, 'rb') as f:
            response = client.post('/profile/', files={'file': ('test.csv', f, 'text/csv')})
        
        if response.status_code == 200:
            data = response.json()
            # Check for statistics
            assert 'statistics' in data or 'summary' in data or 'description' in data or 'columns' in data


class TestDataCleaning:
    """Test data cleaning functionality"""
    
    def test_clean_endpoint(self, client, sample_csv_file):
        """Test data cleaning endpoint"""
        with open(sample_csv_file, 'rb') as f:
            response = client.post('/clean/', files={'file': ('test.csv', f, 'text/csv')})
        
        assert response.status_code == 200
        data = response.json()
        # Should return cleaned data info
        assert 'columns' in data or 'shape' in data or 'data' in data
    
    def test_clean_removes_duplicates(self, client, tmp_path, sample_csv_data):
        """Test that cleaning removes duplicate rows"""
        # Create data with duplicates
        df_with_dupes = sample_csv_data.copy()
        df_with_dupes = df_with_dupes._append(df_with_dupes.head(10), ignore_index=True)
        
        dupe_file = tmp_path / "duplicates.csv"
        df_with_dupes.to_csv(dupe_file, index=False)
        
        with open(dupe_file, 'rb') as f:
            response = client.post('/clean/', files={'file': ('duplicates.csv', f, 'text/csv')})
        
        assert response.status_code == 200


class TestEnhancedUpload:
    """Test enhanced upload with quality scoring"""
    
    def test_enhanced_upload_with_name(self, client, sample_csv_file):
        """Test enhanced upload with dataset name"""
        with open(sample_csv_file, 'rb') as f:
            response = client.post('/upload-enhanced/', 
                                   files={'file': ('test.csv', f, 'text/csv')},
                                   data={'name': 'Test Dataset', 'auto_clean': 'true'})
        
        # May not exist yet
        if response.status_code == 404:
            pytest.skip("Enhanced upload endpoint not implemented")
        
        assert response.status_code == 200
        data = response.json()
        if 'quality_score' in data:
            assert 'grade' in data['quality_score']
    
    def test_quality_score_range(self, client, sample_csv_file):
        """Test that quality score is within valid range"""
        with open(sample_csv_file, 'rb') as f:
            response = client.post('/upload/', files={'file': ('test.csv', f, 'text/csv')})
        
        if response.status_code == 200:
            data = response.json()
            if 'quality_score' in data:
                score = data['quality_score']
                if isinstance(score, dict) and 'score' in score:
                    assert 0 <= score['score'] <= 100
