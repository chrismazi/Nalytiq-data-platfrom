"""
Advanced Machine Learning Module with:
- XGBoost (Classification & Regression)
- Neural Networks (TensorFlow/Keras)
- Hyperparameter Tuning
- Model Comparison
- Feature Engineering
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import joblib
import json
from datetime import datetime
import logging

# Scikit-learn
from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, mean_absolute_error, r2_score,
    classification_report, confusion_matrix
)

# XGBoost
import xgboost as xgb

# TensorFlow/Keras
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, callbacks

logger = logging.getLogger(__name__)

class AdvancedMLPipeline:
    """Advanced ML Pipeline with multiple algorithms"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_names = []
        self.target_name = None
        self.problem_type = None
        
    def prepare_data(self, target: str, features: List[str] = None,
                    test_size: float = 0.2, scale_features: bool = True):
        """Prepare data for training"""
        self.target_name = target
        
        # Auto-select features if not provided
        if features is None:
            features = [col for col in self.df.columns if col != target]
        
        self.feature_names = features
        
        # Separate features and target
        X = self.df[features].copy()
        y = self.df[target].copy()
        
        # Determine problem type
        n_unique = y.nunique()
        if n_unique <= 10:
            self.problem_type = 'classification'
            # Encode target
            self.encoders['target'] = LabelEncoder()
            y = self.encoders['target'].fit_transform(y)
        else:
            self.problem_type = 'regression'
        
        # Handle categorical features
        categorical_cols = X.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            self.encoders[col] = le
        
        # Handle missing values
        X = X.fillna(X.mean())
        
        # Scale features
        if scale_features:
            self.scalers['features'] = StandardScaler()
            X = pd.DataFrame(
                self.scalers['features'].fit_transform(X),
                columns=X.columns,
                index=X.index
            )
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        return X_train, X_test, y_train, y_test
    
    def train_xgboost(self, X_train, X_test, y_train, y_test,
                     n_estimators: int = 100, max_depth: int = 6,
                     learning_rate: float = 0.1, tune_hyperparameters: bool = False) -> Dict:
        """Train XGBoost model"""
        logger.info(f"Training XGBoost for {self.problem_type}")
        start_time = datetime.now()
        
        if self.problem_type == 'classification':
            model = xgb.XGBClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                random_state=42,
                eval_metric='logloss'
            )
        else:
            model = xgb.XGBRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                random_state=42
            )
        
        # Hyperparameter tuning
        if tune_hyperparameters:
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [3, 6, 9],
                'learning_rate': [0.01, 0.1, 0.3]
            }
            
            grid_search = GridSearchCV(
                model, param_grid, cv=3, n_jobs=-1, verbose=1
            )
            grid_search.fit(X_train, y_train)
            model = grid_search.best_estimator_
            best_params = grid_search.best_params_
        else:
            model.fit(X_train, y_train)
            best_params = None
        
        # Predictions
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        # Calculate metrics
        if self.problem_type == 'classification':
            metrics = {
                'train_accuracy': float(accuracy_score(y_train, y_pred_train)),
                'test_accuracy': float(accuracy_score(y_test, y_pred_test)),
                'precision': float(precision_score(y_test, y_pred_test, average='weighted')),
                'recall': float(recall_score(y_test, y_pred_test, average='weighted')),
                'f1_score': float(f1_score(y_test, y_pred_test, average='weighted')),
                'confusion_matrix': confusion_matrix(y_test, y_pred_test).tolist()
            }
        else:
            metrics = {
                'train_r2': float(r2_score(y_train, y_pred_train)),
                'test_r2': float(r2_score(y_test, y_pred_test)),
                'train_rmse': float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
                'test_rmse': float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
                'train_mae': float(mean_absolute_error(y_train, y_pred_train)),
                'test_mae': float(mean_absolute_error(y_test, y_pred_test))
            }
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train, y_train, cv=5)
        metrics['cv_score_mean'] = float(cv_scores.mean())
        metrics['cv_score_std'] = float(cv_scores.std())
        
        training_time = (datetime.now() - start_time).total_seconds()
        
        self.models['xgboost'] = model
        
        return {
            'algorithm': 'XGBoost',
            'problem_type': self.problem_type,
            'metrics': metrics,
            'feature_importance': feature_importance.to_dict('records'),
            'best_params': best_params,
            'training_time_seconds': training_time,
            'n_features': len(self.feature_names),
            'n_samples_train': len(X_train),
            'n_samples_test': len(X_test)
        }
    
    def train_neural_network(self, X_train, X_test, y_train, y_test,
                            hidden_layers: List[int] = [64, 32],
                            dropout_rate: float = 0.2,
                            epochs: int = 50,
                            batch_size: int = 32) -> Dict:
        """Train Neural Network with TensorFlow"""
        logger.info(f"Training Neural Network for {self.problem_type}")
        start_time = datetime.now()
        
        # Build model
        model = models.Sequential()
        
        # Input layer
        model.add(layers.Dense(hidden_layers[0], activation='relu', 
                              input_shape=(X_train.shape[1],)))
        model.add(layers.Dropout(dropout_rate))
        
        # Hidden layers
        for units in hidden_layers[1:]:
            model.add(layers.Dense(units, activation='relu'))
            model.add(layers.Dropout(dropout_rate))
        
        # Output layer
        if self.problem_type == 'classification':
            n_classes = len(np.unique(y_train))
            if n_classes == 2:
                model.add(layers.Dense(1, activation='sigmoid'))
                loss = 'binary_crossentropy'
            else:
                model.add(layers.Dense(n_classes, activation='softmax'))
                loss = 'sparse_categorical_crossentropy'
            metrics_list = ['accuracy']
        else:
            model.add(layers.Dense(1))
            loss = 'mse'
            metrics_list = ['mae']
        
        # Compile model
        model.compile(
            optimizer='adam',
            loss=loss,
            metrics=metrics_list
        )
        
        # Callbacks
        early_stopping = callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        # Train model
        history = model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            callbacks=[early_stopping],
            verbose=0
        )
        
        # Predictions
        y_pred_train = model.predict(X_train, verbose=0)
        y_pred_test = model.predict(X_test, verbose=0)
        
        # Calculate metrics
        if self.problem_type == 'classification':
            if len(np.unique(y_train)) == 2:
                y_pred_train = (y_pred_train > 0.5).astype(int).flatten()
                y_pred_test = (y_pred_test > 0.5).astype(int).flatten()
            else:
                y_pred_train = y_pred_train.argmax(axis=1)
                y_pred_test = y_pred_test.argmax(axis=1)
            
            metrics = {
                'train_accuracy': float(accuracy_score(y_train, y_pred_train)),
                'test_accuracy': float(accuracy_score(y_test, y_pred_test)),
                'precision': float(precision_score(y_test, y_pred_test, average='weighted')),
                'recall': float(recall_score(y_test, y_pred_test, average='weighted')),
                'f1_score': float(f1_score(y_test, y_pred_test, average='weighted')),
                'confusion_matrix': confusion_matrix(y_test, y_pred_test).tolist()
            }
        else:
            y_pred_train = y_pred_train.flatten()
            y_pred_test = y_pred_test.flatten()
            
            metrics = {
                'train_r2': float(r2_score(y_train, y_pred_train)),
                'test_r2': float(r2_score(y_test, y_pred_test)),
                'train_rmse': float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
                'test_rmse': float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
                'train_mae': float(mean_absolute_error(y_train, y_pred_train)),
                'test_mae': float(mean_absolute_error(y_test, y_pred_test))
            }
        
        training_time = (datetime.now() - start_time).total_seconds()
        
        self.models['neural_network'] = model
        
        return {
            'algorithm': 'Neural Network',
            'problem_type': self.problem_type,
            'metrics': metrics,
            'architecture': {
                'hidden_layers': hidden_layers,
                'dropout_rate': dropout_rate,
                'total_params': model.count_params()
            },
            'training_history': {
                'loss': [float(x) for x in history.history['loss']],
                'val_loss': [float(x) for x in history.history['val_loss']]
            },
            'training_time_seconds': training_time,
            'epochs_trained': len(history.history['loss']),
            'n_features': len(self.feature_names),
            'n_samples_train': len(X_train),
            'n_samples_test': len(X_test)
        }
    
    def compare_models(self, results: List[Dict]) -> Dict:
        """Compare multiple model results"""
        comparison = {
            'models': [],
            'best_model': None,
            'comparison_metric': None
        }
        
        # Determine comparison metric
        if self.problem_type == 'classification':
            comparison_metric = 'test_accuracy'
        else:
            comparison_metric = 'test_r2'
        
        comparison['comparison_metric'] = comparison_metric
        
        # Compare models
        best_score = -np.inf
        best_model = None
        
        for result in results:
            model_summary = {
                'algorithm': result['algorithm'],
                'score': result['metrics'].get(comparison_metric, 0),
                'training_time': result['training_time_seconds']
            }
            comparison['models'].append(model_summary)
            
            if model_summary['score'] > best_score:
                best_score = model_summary['score']
                best_model = result['algorithm']
        
        comparison['best_model'] = best_model
        comparison['best_score'] = best_score
        
        return comparison
    
    def save_model(self, model_name: str, algorithm: str, save_path: str):
        """Save trained model"""
        model = self.models.get(algorithm.lower().replace(' ', '_'))
        
        if model is None:
            raise ValueError(f"Model {algorithm} not trained yet")
        
        # Save model
        if algorithm == 'Neural Network':
            model.save(f"{save_path}/{model_name}_nn.keras")
        else:
            joblib.dump(model, f"{save_path}/{model_name}_{algorithm.lower()}.pkl")
        
        # Save encoders and scalers
        joblib.dump(self.encoders, f"{save_path}/{model_name}_encoders.pkl")
        joblib.dump(self.scalers, f"{save_path}/{model_name}_scalers.pkl")
        
        # Save metadata
        metadata = {
            'model_name': model_name,
            'algorithm': algorithm,
            'problem_type': self.problem_type,
            'feature_names': self.feature_names,
            'target_name': self.target_name,
            'created_at': datetime.now().isoformat()
        }
        
        with open(f"{save_path}/{model_name}_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Model saved to {save_path}/{model_name}")
    
    def suggest_features(self, X: pd.DataFrame) -> Dict:
        """Suggest feature engineering opportunities"""
        suggestions = {
            'polynomial_features': [],
            'interaction_features': [],
            'binning_candidates': [],
            'log_transform_candidates': []
        }
        
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        
        # Suggest polynomial features for skewed distributions
        for col in numeric_cols:
            skew = X[col].skew()
            if abs(skew) > 1:
                suggestions['polynomial_features'].append({
                    'column': col,
                    'skewness': float(skew),
                    'suggestion': 'square' if skew > 0 else 'sqrt'
                })
        
        # Suggest interaction features for correlated pairs
        corr_matrix = X[numeric_cols].corr().abs()
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if 0.5 < corr_matrix.iloc[i, j] < 0.95:
                    suggestions['interaction_features'].append({
                        'col1': corr_matrix.columns[i],
                        'col2': corr_matrix.columns[j],
                        'correlation': float(corr_matrix.iloc[i, j])
                    })
        
        # Suggest binning for high-cardinality features
        for col in numeric_cols:
            n_unique = X[col].nunique()
            if n_unique > 50:
                suggestions['binning_candidates'].append({
                    'column': col,
                    'unique_values': int(n_unique),
                    'suggested_bins': min(10, n_unique // 10)
                })
        
        # Suggest log transform for positive skewed features
        for col in numeric_cols:
            if (X[col] > 0).all():
                skew = X[col].skew()
                if skew > 1:
                    suggestions['log_transform_candidates'].append({
                        'column': col,
                        'skewness': float(skew)
                    })
        
        return suggestions
