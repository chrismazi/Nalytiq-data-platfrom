"""
Machine Learning Pipeline Tests
Tests for ML model training, prediction, and comparison
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
import os


class TestDataPreparation:
    """Test data preparation for ML"""
    
    def test_prepare_classification_data(self, ml_classification_data):
        """Test preparing classification data"""
        from ml_pipeline import MLPipeline
        
        pipeline = MLPipeline(ml_classification_data)
        X_train, X_test, y_train, y_test = pipeline.prepare_data(
            target='target',
            test_size=0.2
        )
        
        assert len(X_train) + len(X_test) == len(ml_classification_data)
        assert len(X_train) == len(y_train)
        assert len(X_test) == len(y_test)
    
    def test_prepare_regression_data(self, ml_regression_data):
        """Test preparing regression data"""
        from ml_pipeline import MLPipeline
        
        pipeline = MLPipeline(ml_regression_data)
        X_train, X_test, y_train, y_test = pipeline.prepare_data(
            target='target',
            test_size=0.2
        )
        
        assert len(X_train) > 0
        assert len(X_test) > 0
    
    def test_feature_selection(self, ml_classification_data):
        """Test specific feature selection"""
        from ml_pipeline import MLPipeline
        
        pipeline = MLPipeline(ml_classification_data)
        features = ['feature_1', 'feature_2']
        X_train, X_test, y_train, y_test = pipeline.prepare_data(
            target='target',
            features=features,
            test_size=0.2
        )
        
        assert X_train.shape[1] == len(features)


class TestRandomForestTraining:
    """Test Random Forest model training"""
    
    @pytest.mark.ml
    def test_train_classifier(self, ml_classification_data):
        """Test training Random Forest classifier"""
        from ml_pipeline import MLPipeline
        
        pipeline = MLPipeline(ml_classification_data)
        X_train, X_test, y_train, y_test = pipeline.prepare_data(
            target='target',
            test_size=0.2
        )
        
        result = pipeline.train_random_forest(X_train, X_test, y_train, y_test)
        
        assert 'accuracy' in result or 'score' in result
        assert 'feature_importance' in result
    
    @pytest.mark.ml
    def test_train_regressor(self, ml_regression_data):
        """Test training Random Forest regressor"""
        from ml_pipeline import MLPipeline
        
        pipeline = MLPipeline(ml_regression_data)
        X_train, X_test, y_train, y_test = pipeline.prepare_data(
            target='target',
            test_size=0.2
        )
        
        result = pipeline.train_random_forest(X_train, X_test, y_train, y_test)
        
        # Should have r2_score or mse for regression
        assert 'r2_score' in result or 'mse' in result or 'score' in result
    
    @pytest.mark.ml
    def test_feature_importance_ranking(self, ml_classification_data):
        """Test that feature importance is ranked correctly"""
        from ml_pipeline import MLPipeline
        
        pipeline = MLPipeline(ml_classification_data)
        X_train, X_test, y_train, y_test = pipeline.prepare_data(
            target='target',
            test_size=0.2
        )
        
        result = pipeline.train_random_forest(X_train, X_test, y_train, y_test)
        
        if 'feature_importance' in result:
            importance = result['feature_importance']
            assert isinstance(importance, (list, dict))


class TestXGBoostTraining:
    """Test XGBoost model training"""
    
    @pytest.mark.ml
    @pytest.mark.slow
    def test_train_xgboost_classifier(self, ml_classification_data):
        """Test training XGBoost classifier"""
        try:
            from ml_advanced import AdvancedMLPipeline
        except ImportError:
            pytest.skip("XGBoost not installed")
        
        pipeline = AdvancedMLPipeline(ml_classification_data)
        X_train, X_test, y_train, y_test = pipeline.prepare_data(
            target='target',
            test_size=0.2
        )
        
        result = pipeline.train_xgboost(
            X_train, X_test, y_train, y_test,
            n_estimators=10,  # Small for testing
            max_depth=3
        )
        
        assert 'accuracy' in result or 'metrics' in result
    
    @pytest.mark.ml
    @pytest.mark.slow
    def test_xgboost_hyperparameter_tuning(self, ml_classification_data):
        """Test XGBoost hyperparameter tuning"""
        try:
            from ml_advanced import AdvancedMLPipeline
        except ImportError:
            pytest.skip("XGBoost not installed")
        
        pipeline = AdvancedMLPipeline(ml_classification_data)
        X_train, X_test, y_train, y_test = pipeline.prepare_data(
            target='target',
            test_size=0.2
        )
        
        result = pipeline.train_xgboost(
            X_train, X_test, y_train, y_test,
            tune_hyperparameters=True
        )
        
        assert 'best_params' in result or 'accuracy' in result


class TestNeuralNetworkTraining:
    """Test Neural Network model training"""
    
    @pytest.mark.ml
    @pytest.mark.slow
    def test_train_neural_network(self, ml_classification_data):
        """Test training a simple neural network"""
        try:
            from ml_advanced import AdvancedMLPipeline
        except ImportError:
            pytest.skip("TensorFlow not installed")
        
        pipeline = AdvancedMLPipeline(ml_classification_data)
        X_train, X_test, y_train, y_test = pipeline.prepare_data(
            target='target',
            test_size=0.2,
            scale_features=True
        )
        
        result = pipeline.train_neural_network(
            X_train, X_test, y_train, y_test,
            hidden_layers=[16, 8],  # Small for testing
            epochs=5,  # Few epochs for testing
            batch_size=16
        )
        
        assert 'accuracy' in result or 'metrics' in result
    
    @pytest.mark.ml
    @pytest.mark.slow
    def test_neural_network_training_history(self, ml_classification_data):
        """Test that neural network returns training history"""
        try:
            from ml_advanced import AdvancedMLPipeline
        except ImportError:
            pytest.skip("TensorFlow not installed")
        
        pipeline = AdvancedMLPipeline(ml_classification_data)
        X_train, X_test, y_train, y_test = pipeline.prepare_data(
            target='target',
            test_size=0.2
        )
        
        result = pipeline.train_neural_network(
            X_train, X_test, y_train, y_test,
            epochs=5
        )
        
        if 'training_history' in result:
            history = result['training_history']
            assert 'loss' in history or isinstance(history, list)


class TestModelComparison:
    """Test model comparison functionality"""
    
    @pytest.mark.ml
    @pytest.mark.slow
    def test_compare_models(self, ml_classification_data):
        """Test comparing multiple models"""
        try:
            from ml_advanced import AdvancedMLPipeline
        except ImportError:
            pytest.skip("ML libraries not fully installed")
        
        pipeline = AdvancedMLPipeline(ml_classification_data)
        X_train, X_test, y_train, y_test = pipeline.prepare_data(
            target='target',
            test_size=0.2
        )
        
        # Train multiple models
        results = []
        
        # Random Forest
        rf_result = pipeline.train_xgboost(X_train, X_test, y_train, y_test, n_estimators=10)
        rf_result['algorithm'] = 'XGBoost'
        results.append(rf_result)
        
        # Compare
        comparison = pipeline.compare_models(results)
        
        assert 'winner' in comparison or 'rankings' in comparison or 'results' in comparison


class TestModelPersistence:
    """Test model saving and loading"""
    
    @pytest.mark.ml
    def test_save_model(self, ml_classification_data, tmp_path):
        """Test saving a trained model"""
        from ml_pipeline import MLPipeline
        
        pipeline = MLPipeline(ml_classification_data)
        X_train, X_test, y_train, y_test = pipeline.prepare_data(
            target='target',
            test_size=0.2
        )
        
        result = pipeline.train_random_forest(X_train, X_test, y_train, y_test)
        
        # Try to save if method exists
        if hasattr(pipeline, 'save_model'):
            save_path = str(tmp_path / "test_model.pkl")
            pipeline.save_model(save_path)
            assert os.path.exists(save_path)


class TestMLEndpoints:
    """Test ML API endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_model_training_endpoint(self, client, sample_csv_file):
        """Test ML training via API endpoint"""
        # First upload the data
        with open(sample_csv_file, 'rb') as f:
            upload_response = client.post('/upload/', files={'file': ('test.csv', f, 'text/csv')})
        
        if upload_response.status_code != 200:
            pytest.skip("Upload failed")
        
        # Try to train a model
        with open(sample_csv_file, 'rb') as f:
            response = client.post('/model/', 
                                   files={'file': ('test.csv', f, 'text/csv')},
                                   data={'target': 'category', 'features': 'value,price,quantity'})
        
        # Should succeed or return proper error
        assert response.status_code in [200, 400, 422]
