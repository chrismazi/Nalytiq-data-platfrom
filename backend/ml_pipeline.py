"""
Machine Learning Pipeline
Supports classification, regression, and feature analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, mean_absolute_error, r2_score,
    classification_report, confusion_matrix
)
import logging
import joblib
import os

logger = logging.getLogger(__name__)

class MLPipeline:
    """
    Comprehensive ML pipeline for classification and regression
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.model = None
        self.model_type = None
        self.feature_names = []
        self.target_name = None
        self.label_encoders = {}
        self.scaler = None
        self.trained = False
        
    def prepare_features(
        self,
        target: str,
        features: Optional[List[str]] = None,
        auto_select: bool = False,
        max_features: int = 50
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features for modeling
        """
        self.target_name = target
        
        # Validate target exists
        if target not in self.df.columns:
            raise ValueError(f"Target column '{target}' not found in dataset")
        
        # Select features
        if features is None:
            # Auto-select all columns except target
            features = [col for col in self.df.columns if col != target]
        
        # Validate features exist
        missing_features = [f for f in features if f not in self.df.columns]
        if missing_features:
            raise ValueError(f"Features not found: {', '.join(missing_features)}")
        
        # Filter to only numeric and categorical columns
        valid_features = []
        for col in features:
            if pd.api.types.is_numeric_dtype(self.df[col]) or \
               self.df[col].dtype in ['object', 'category']:
                valid_features.append(col)
        
        if not valid_features:
            raise ValueError("No valid features found (need numeric or categorical)")
        
        # Limit number of features if specified
        if len(valid_features) > max_features:
            logger.warning(f"Limiting features from {len(valid_features)} to {max_features}")
            valid_features = valid_features[:max_features]
        
        self.feature_names = valid_features
        
        # Prepare feature matrix
        X = self.df[valid_features].copy()
        y = self.df[target].copy()
        
        # Handle missing values
        X = X.fillna(X.mean() if pd.api.types.is_numeric_dtype(X) else X.mode().iloc[0])
        y = y.fillna(y.mean() if pd.api.types.is_numeric_dtype(y) else y.mode().iloc[0])
        
        # Encode categorical features
        for col in X.columns:
            if X[col].dtype in ['object', 'category']:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                self.label_encoders[col] = le
        
        # Encode target if classification
        if y.dtype in ['object', 'category']:
            le = LabelEncoder()
            y = le.fit_transform(y.astype(str))
            self.label_encoders[target] = le
            self.model_type = 'classification'
        else:
            self.model_type = 'regression'
        
        return X, y
    
    def train_model(
        self,
        target: str,
        features: Optional[List[str]] = None,
        test_size: float = 0.2,
        random_state: int = 42,
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
        cv_folds: int = 5
    ) -> Dict[str, Any]:
        """
        Train Random Forest model
        """
        logger.info(f"Training model for target: {target}")
        
        # Prepare data
        X, y = self.prepare_features(target, features)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y if self.model_type == 'classification' else None
        )
        
        # Initialize model
        if self.model_type == 'classification':
            self.model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_state,
                n_jobs=-1
            )
        else:
            self.model = RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_state,
                n_jobs=-1
            )
        
        # Train model
        logger.info("Training Random Forest model...")
        self.model.fit(X_train, y_train)
        self.trained = True
        
        # Make predictions
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        # Calculate metrics
        results = {
            'model_type': self.model_type,
            'target': target,
            'features': self.feature_names,
            'n_samples': len(X),
            'n_features': len(self.feature_names),
            'train_size': len(X_train),
            'test_size': len(X_test),
            'parameters': {
                'n_estimators': n_estimators,
                'max_depth': max_depth,
                'random_state': random_state
            }
        }
        
        if self.model_type == 'classification':
            # Classification metrics
            results['metrics'] = {
                'train_accuracy': float(accuracy_score(y_train, y_pred_train)),
                'test_accuracy': float(accuracy_score(y_test, y_pred_test)),
                'precision': float(precision_score(y_test, y_pred_test, average='weighted', zero_division=0)),
                'recall': float(recall_score(y_test, y_pred_test, average='weighted', zero_division=0)),
                'f1_score': float(f1_score(y_test, y_pred_test, average='weighted', zero_division=0))
            }
            
            # Cross-validation score
            try:
                cv_scores = cross_val_score(self.model, X, y, cv=cv_folds, scoring='accuracy')
                results['metrics']['cv_accuracy_mean'] = float(cv_scores.mean())
                results['metrics']['cv_accuracy_std'] = float(cv_scores.std())
            except Exception as e:
                logger.warning(f"Cross-validation failed: {e}")
            
            # Confusion matrix
            cm = confusion_matrix(y_test, y_pred_test)
            results['confusion_matrix'] = cm.tolist()
            
            # Classification report
            if target in self.label_encoders:
                target_names = self.label_encoders[target].classes_.tolist()
            else:
                target_names = [str(i) for i in np.unique(y_test)]
            
            report = classification_report(y_test, y_pred_test, target_names=target_names, output_dict=True, zero_division=0)
            results['classification_report'] = report
            
        else:
            # Regression metrics
            results['metrics'] = {
                'train_r2': float(r2_score(y_train, y_pred_train)),
                'test_r2': float(r2_score(y_test, y_pred_test)),
                'train_rmse': float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
                'test_rmse': float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
                'train_mae': float(mean_absolute_error(y_train, y_pred_train)),
                'test_mae': float(mean_absolute_error(y_test, y_pred_test))
            }
            
            # Cross-validation score
            try:
                cv_scores = cross_val_score(self.model, X, y, cv=cv_folds, scoring='r2')
                results['metrics']['cv_r2_mean'] = float(cv_scores.mean())
                results['metrics']['cv_r2_std'] = float(cv_scores.std())
            except Exception as e:
                logger.warning(f"Cross-validation failed: {e}")
        
        # Feature importance
        feature_importance = self.get_feature_importance()
        results['feature_importance'] = feature_importance
        
        # Model insights
        results['insights'] = self.generate_model_insights(results)
        
        logger.info(f"Model training complete. Test {self.model_type} score: {results['metrics']}")
        
        return results
    
    def get_feature_importance(self, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        Get feature importance rankings
        """
        if not self.trained or self.model is None:
            return []
        
        importances = self.model.feature_importances_
        feature_importance = [
            {
                'feature': feature,
                'importance': float(importance),
                'importance_pct': float(importance * 100)
            }
            for feature, importance in zip(self.feature_names, importances)
        ]
        
        # Sort by importance
        feature_importance.sort(key=lambda x: x['importance'], reverse=True)
        
        return feature_importance[:top_n]
    
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on new data
        """
        if not self.trained:
            raise ValueError("Model not trained yet")
        
        # Prepare features
        X = data[self.feature_names].copy()
        
        # Encode categorical features
        for col in X.columns:
            if col in self.label_encoders:
                X[col] = self.label_encoders[col].transform(X[col].astype(str))
        
        # Make predictions
        predictions = self.model.predict(X)
        
        # Decode predictions if classification
        if self.model_type == 'classification' and self.target_name in self.label_encoders:
            predictions = self.label_encoders[self.target_name].inverse_transform(predictions)
        
        return predictions
    
    def predict_proba(self, data: pd.DataFrame) -> np.ndarray:
        """
        Get prediction probabilities (classification only)
        """
        if not self.trained:
            raise ValueError("Model not trained yet")
        
        if self.model_type != 'classification':
            raise ValueError("Probabilities only available for classification")
        
        # Prepare features
        X = data[self.feature_names].copy()
        
        # Encode categorical features
        for col in X.columns:
            if col in self.label_encoders:
                X[col] = self.label_encoders[col].transform(X[col].astype(str))
        
        return self.model.predict_proba(X)
    
    def save_model(self, filepath: str):
        """
        Save trained model to disk
        """
        if not self.trained:
            raise ValueError("Model not trained yet")
        
        model_data = {
            'model': self.model,
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'target_name': self.target_name,
            'label_encoders': self.label_encoders
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """
        Load trained model from disk
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.model_type = model_data['model_type']
        self.feature_names = model_data['feature_names']
        self.target_name = model_data['target_name']
        self.label_encoders = model_data['label_encoders']
        self.trained = True
        
        logger.info(f"Model loaded from {filepath}")
    
    def generate_model_insights(self, results: Dict[str, Any]) -> List[str]:
        """
        Generate insights from model results
        """
        insights = []
        metrics = results['metrics']
        
        if self.model_type == 'classification':
            # Accuracy insights
            test_acc = metrics['test_accuracy']
            if test_acc > 0.9:
                insights.append("Excellent model performance (>90% accuracy)")
            elif test_acc > 0.8:
                insights.append("Good model performance (>80% accuracy)")
            elif test_acc > 0.7:
                insights.append("Acceptable model performance (>70% accuracy)")
            else:
                insights.append("Model performance needs improvement (<70% accuracy)")
            
            # Overfitting check
            train_acc = metrics['train_accuracy']
            if train_acc - test_acc > 0.1:
                insights.append("Potential overfitting detected (train-test gap >10%)")
            
            # F1 score
            if metrics['f1_score'] < 0.7:
                insights.append("Low F1 score - consider class balancing or more features")
        
        else:  # Regression
            # R² insights
            test_r2 = metrics['test_r2']
            if test_r2 > 0.9:
                insights.append("Excellent model fit (R² >0.9)")
            elif test_r2 > 0.7:
                insights.append("Good model fit (R² >0.7)")
            elif test_r2 > 0.5:
                insights.append("Moderate model fit (R² >0.5)")
            else:
                insights.append("Poor model fit (R² <0.5) - consider more features")
            
            # Overfitting check
            train_r2 = metrics['train_r2']
            if train_r2 - test_r2 > 0.1:
                insights.append("Potential overfitting detected (train-test R² gap >0.1)")
        
        # Feature importance insights
        feature_imp = results['feature_importance']
        if feature_imp:
            top_feature = feature_imp[0]
            if top_feature['importance_pct'] > 50:
                insights.append(f"Single dominant feature: {top_feature['feature']} ({top_feature['importance_pct']:.1f}%)")
            
            # Check for feature diversity
            top_5_importance = sum(f['importance_pct'] for f in feature_imp[:5])
            if top_5_importance > 90:
                insights.append("Top 5 features account for >90% importance - other features may be redundant")
        
        return insights
    
    def get_model_summary(self) -> Dict[str, Any]:
        """
        Get summary of trained model
        """
        if not self.trained:
            return {'error': 'Model not trained'}
        
        return {
            'model_type': self.model_type,
            'target': self.target_name,
            'n_features': len(self.feature_names),
            'features': self.feature_names,
            'algorithm': 'Random Forest',
            'n_estimators': self.model.n_estimators,
            'trained': True
        }
