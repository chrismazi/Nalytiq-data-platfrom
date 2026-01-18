"""
Advanced ML Capabilities

Enhanced machine learning features:
- AutoML with hyperparameter optimization
- Model versioning and registry
- Feature engineering automation
- Model explanation (SHAP)
- A/B testing for models
- Ensemble methods
"""

import logging
import uuid
import os
import json
import pickle
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from sklearn.model_selection import cross_val_score, GridSearchCV, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    VotingClassifier, VotingRegressor, StackingClassifier, StackingRegressor
)
from sklearn.linear_model import LogisticRegression, Ridge, Lasso, ElasticNet
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, mean_absolute_error, r2_score
)
import joblib

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"


class ModelStatus(str, Enum):
    DRAFT = "draft"
    TRAINING = "training"
    TRAINED = "trained"
    DEPLOYED = "deployed"
    ARCHIVED = "archived"


@dataclass
class ModelVersion:
    """Model version metadata"""
    version_id: str
    model_id: str
    version_number: int
    created_at: str
    created_by: Optional[str]
    metrics: Dict[str, float]
    hyperparameters: Dict[str, Any]
    feature_importance: Dict[str, float]
    file_path: str
    status: ModelStatus
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        return data


@dataclass
class ModelInfo:
    """Model registry entry"""
    model_id: str
    name: str
    model_type: ModelType
    algorithm: str
    target_column: str
    feature_columns: List[str]
    created_at: str
    created_by: Optional[str]
    current_version: int
    versions: List[str]  # version_ids
    production_version: Optional[str]
    description: str = ""
    tags: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['model_type'] = self.model_type.value
        return data


class AutoMLEngine:
    """Automated Machine Learning Engine"""
    
    CLASSIFICATION_MODELS = {
        'random_forest': {
            'model': RandomForestClassifier,
            'params': {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
        },
        'gradient_boosting': {
            'model': GradientBoostingClassifier,
            'params': {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7]
            }
        },
        'logistic_regression': {
            'model': LogisticRegression,
            'params': {
                'C': [0.1, 1.0, 10.0],
                'penalty': ['l1', 'l2'],
                'solver': ['liblinear', 'saga']
            }
        },
        'svm': {
            'model': SVC,
            'params': {
                'C': [0.1, 1.0, 10.0],
                'kernel': ['rbf', 'linear'],
                'probability': [True]
            }
        },
        'knn': {
            'model': KNeighborsClassifier,
            'params': {
                'n_neighbors': [3, 5, 7, 9],
                'weights': ['uniform', 'distance']
            }
        }
    }
    
    REGRESSION_MODELS = {
        'random_forest': {
            'model': RandomForestRegressor,
            'params': {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 20, None],
                'min_samples_split': [2, 5, 10]
            }
        },
        'gradient_boosting': {
            'model': GradientBoostingRegressor,
            'params': {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7]
            }
        },
        'ridge': {
            'model': Ridge,
            'params': {
                'alpha': [0.1, 1.0, 10.0, 100.0]
            }
        },
        'lasso': {
            'model': Lasso,
            'params': {
                'alpha': [0.1, 1.0, 10.0, 100.0]
            }
        },
        'elastic_net': {
            'model': ElasticNet,
            'params': {
                'alpha': [0.1, 1.0, 10.0],
                'l1_ratio': [0.2, 0.5, 0.8]
            }
        },
        'svr': {
            'model': SVR,
            'params': {
                'C': [0.1, 1.0, 10.0],
                'kernel': ['rbf', 'linear']
            }
        }
    }
    
    def __init__(self, cv_folds: int = 5, n_jobs: int = -1):
        self.cv_folds = cv_folds
        self.n_jobs = n_jobs
    
    def find_best_model(
        self,
        X: np.ndarray,
        y: np.ndarray,
        model_type: ModelType,
        algorithms: Optional[List[str]] = None,
        search_method: str = "random",  # "grid" or "random"
        n_iter: int = 20,
        scoring: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run AutoML to find the best model and hyperparameters.
        
        Returns:
            Dict with best model, params, and comparison results
        """
        if model_type == ModelType.CLASSIFICATION:
            models = self.CLASSIFICATION_MODELS
            scoring = scoring or 'accuracy'
        else:
            models = self.REGRESSION_MODELS
            scoring = scoring or 'r2'
        
        if algorithms:
            models = {k: v for k, v in models.items() if k in algorithms}
        
        results = []
        best_model = None
        best_score = -float('inf')
        best_params = {}
        best_algorithm = ""
        
        for name, config in models.items():
            logger.info(f"Training {name}...")
            
            try:
                if search_method == "grid":
                    search = GridSearchCV(
                        config['model'](),
                        config['params'],
                        cv=self.cv_folds,
                        scoring=scoring,
                        n_jobs=self.n_jobs,
                        error_score='raise'
                    )
                else:
                    search = RandomizedSearchCV(
                        config['model'](),
                        config['params'],
                        n_iter=min(n_iter, self._count_param_combinations(config['params'])),
                        cv=self.cv_folds,
                        scoring=scoring,
                        n_jobs=self.n_jobs,
                        random_state=42,
                        error_score='raise'
                    )
                
                search.fit(X, y)
                
                result = {
                    'algorithm': name,
                    'best_score': search.best_score_,
                    'best_params': search.best_params_,
                    'cv_results_mean': search.cv_results_['mean_test_score'].tolist(),
                    'cv_results_std': search.cv_results_['std_test_score'].tolist()
                }
                results.append(result)
                
                if search.best_score_ > best_score:
                    best_score = search.best_score_
                    best_model = search.best_estimator_
                    best_params = search.best_params_
                    best_algorithm = name
                
            except Exception as e:
                logger.warning(f"Failed to train {name}: {e}")
                results.append({
                    'algorithm': name,
                    'error': str(e)
                })
        
        return {
            'best_algorithm': best_algorithm,
            'best_model': best_model,
            'best_score': best_score,
            'best_params': best_params,
            'all_results': results,
            'scoring': scoring
        }
    
    def _count_param_combinations(self, params: Dict) -> int:
        """Count total parameter combinations"""
        count = 1
        for values in params.values():
            count *= len(values)
        return count


class FeatureEngineer:
    """Automated feature engineering"""
    
    def __init__(self):
        self.transformations = {}
        self.encoders = {}
        self.scalers = {}
    
    def auto_engineer(
        self,
        df,
        target_column: str,
        max_features: int = 50
    ) -> Tuple[np.ndarray, List[str], Dict[str, Any]]:
        """
        Automatically engineer features from a DataFrame.
        
        Returns:
            - X: Feature matrix
            - feature_names: List of feature names
            - transformations: Applied transformations
        """
        import pandas as pd
        
        df = df.copy()
        feature_columns = [c for c in df.columns if c != target_column]
        transformations = {}
        
        # Handle missing values
        for col in feature_columns:
            if df[col].isnull().any():
                if df[col].dtype in ['int64', 'float64']:
                    fill_value = df[col].median()
                    df[col] = df[col].fillna(fill_value)
                    transformations[f"{col}_fill"] = {'method': 'median', 'value': fill_value}
                else:
                    fill_value = df[col].mode()[0] if len(df[col].mode()) > 0 else "unknown"
                    df[col] = df[col].fillna(fill_value)
                    transformations[f"{col}_fill"] = {'method': 'mode', 'value': fill_value}
        
        # Encode categorical variables
        encoded_columns = []
        for col in feature_columns:
            if df[col].dtype == 'object' or str(df[col].dtype) == 'category':
                # Label encode if few unique values, otherwise one-hot
                n_unique = df[col].nunique()
                if n_unique <= 10:
                    le = LabelEncoder()
                    df[col] = le.fit_transform(df[col].astype(str))
                    self.encoders[col] = le
                    transformations[f"{col}_encode"] = {'method': 'label', 'classes': le.classes_.tolist()}
                    encoded_columns.append(col)
        
        # Create numeric feature matrix
        numeric_cols = df[feature_columns].select_dtypes(include=[np.number]).columns.tolist()
        
        # Scale numeric features
        scaler = StandardScaler()
        X = scaler.fit_transform(df[numeric_cols])
        self.scalers['main'] = scaler
        transformations['scaling'] = {'method': 'standard', 'columns': numeric_cols}
        
        # Feature selection if too many
        if X.shape[1] > max_features:
            from sklearn.feature_selection import SelectKBest, f_classif, f_regression
            selector = SelectKBest(k=max_features)
            X = selector.fit_transform(X, df[target_column])
            selected_indices = selector.get_support(indices=True)
            numeric_cols = [numeric_cols[i] for i in selected_indices]
            transformations['selection'] = {'method': 'kbest', 'k': max_features}
        
        return X, numeric_cols, transformations


class EnsembleBuilder:
    """Build ensemble models"""
    
    @staticmethod
    def create_voting_ensemble(
        models: List[Tuple[str, Any]],
        model_type: ModelType,
        voting: str = 'soft'
    ):
        """Create a voting ensemble from multiple models"""
        if model_type == ModelType.CLASSIFICATION:
            return VotingClassifier(
                estimators=models,
                voting=voting
            )
        else:
            return VotingRegressor(estimators=models)
    
    @staticmethod
    def create_stacking_ensemble(
        models: List[Tuple[str, Any]],
        model_type: ModelType,
        final_estimator=None
    ):
        """Create a stacking ensemble"""
        if model_type == ModelType.CLASSIFICATION:
            return StackingClassifier(
                estimators=models,
                final_estimator=final_estimator or LogisticRegression()
            )
        else:
            return StackingRegressor(
                estimators=models,
                final_estimator=final_estimator or Ridge()
            )


class ModelRegistry:
    """Model versioning and registry"""
    
    def __init__(self, models_dir: str = "./models"):
        self.models_dir = models_dir
        self.registry_file = os.path.join(models_dir, "registry.json")
        self.models: Dict[str, ModelInfo] = {}
        self.versions: Dict[str, ModelVersion] = {}
        self._load()
    
    def _load(self) -> None:
        """Load registry from disk"""
        try:
            if os.path.exists(self.registry_file):
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                    for model_data in data.get('models', []):
                        model_data['model_type'] = ModelType(model_data['model_type'])
                        self.models[model_data['model_id']] = ModelInfo(**model_data)
                    for version_data in data.get('versions', []):
                        version_data['status'] = ModelStatus(version_data['status'])
                        self.versions[version_data['version_id']] = ModelVersion(**version_data)
        except Exception as e:
            logger.warning(f"Failed to load model registry: {e}")
    
    def _save(self) -> None:
        """Save registry to disk"""
        try:
            os.makedirs(self.models_dir, exist_ok=True)
            with open(self.registry_file, 'w') as f:
                json.dump({
                    'models': [m.to_dict() for m in self.models.values()],
                    'versions': [v.to_dict() for v in self.versions.values()]
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save model registry: {e}")
    
    def register_model(
        self,
        name: str,
        model_type: ModelType,
        algorithm: str,
        target_column: str,
        feature_columns: List[str],
        created_by: Optional[str] = None,
        description: str = "",
        tags: List[str] = None
    ) -> ModelInfo:
        """Register a new model"""
        model_id = str(uuid.uuid4())
        
        model_info = ModelInfo(
            model_id=model_id,
            name=name,
            model_type=model_type,
            algorithm=algorithm,
            target_column=target_column,
            feature_columns=feature_columns,
            created_at=datetime.utcnow().isoformat(),
            created_by=created_by,
            current_version=0,
            versions=[],
            production_version=None,
            description=description,
            tags=tags or []
        )
        
        self.models[model_id] = model_info
        self._save()
        
        return model_info
    
    def add_version(
        self,
        model_id: str,
        model,
        metrics: Dict[str, float],
        hyperparameters: Dict[str, Any],
        feature_importance: Dict[str, float],
        created_by: Optional[str] = None,
        description: str = ""
    ) -> ModelVersion:
        """Add a new version to an existing model"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        
        model_info = self.models[model_id]
        version_number = model_info.current_version + 1
        version_id = f"{model_id}_v{version_number}"
        
        # Save model file
        model_dir = os.path.join(self.models_dir, model_id)
        os.makedirs(model_dir, exist_ok=True)
        file_path = os.path.join(model_dir, f"v{version_number}.pkl")
        joblib.dump(model, file_path)
        
        # Create version record
        version = ModelVersion(
            version_id=version_id,
            model_id=model_id,
            version_number=version_number,
            created_at=datetime.utcnow().isoformat(),
            created_by=created_by,
            metrics=metrics,
            hyperparameters=hyperparameters,
            feature_importance=feature_importance,
            file_path=file_path,
            status=ModelStatus.TRAINED,
            description=description
        )
        
        self.versions[version_id] = version
        model_info.versions.append(version_id)
        model_info.current_version = version_number
        
        self._save()
        return version
    
    def load_model(self, version_id: str):
        """Load a model by version ID"""
        if version_id not in self.versions:
            raise ValueError(f"Version {version_id} not found")
        
        version = self.versions[version_id]
        return joblib.load(version.file_path)
    
    def promote_to_production(self, version_id: str) -> bool:
        """Promote a model version to production"""
        if version_id not in self.versions:
            return False
        
        version = self.versions[version_id]
        model_info = self.models[version.model_id]
        
        # Demote current production
        if model_info.production_version:
            old_version = self.versions.get(model_info.production_version)
            if old_version:
                old_version.status = ModelStatus.ARCHIVED
        
        # Promote new version
        version.status = ModelStatus.DEPLOYED
        model_info.production_version = version_id
        
        self._save()
        return True
    
    def get_production_model(self, model_id: str):
        """Get the production version of a model"""
        if model_id not in self.models:
            return None
        
        model_info = self.models[model_id]
        if not model_info.production_version:
            return None
        
        return self.load_model(model_info.production_version)
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List all registered models"""
        return [m.to_dict() for m in self.models.values()]
    
    def get_model_versions(self, model_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a model"""
        if model_id not in self.models:
            return []
        
        model_info = self.models[model_id]
        return [self.versions[v].to_dict() for v in model_info.versions if v in self.versions]


class ABTestManager:
    """A/B testing for ML models"""
    
    def __init__(self):
        self.experiments: Dict[str, Dict] = {}
        self.results: Dict[str, List[Dict]] = {}
    
    def create_experiment(
        self,
        experiment_id: str,
        model_a_id: str,
        model_b_id: str,
        traffic_split: float = 0.5,
        metric: str = "accuracy",
        min_samples: int = 100
    ) -> Dict[str, Any]:
        """Create an A/B test experiment"""
        self.experiments[experiment_id] = {
            'experiment_id': experiment_id,
            'model_a_id': model_a_id,
            'model_b_id': model_b_id,
            'traffic_split': traffic_split,
            'metric': metric,
            'min_samples': min_samples,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'running'
        }
        self.results[experiment_id] = []
        return self.experiments[experiment_id]
    
    def record_prediction(
        self,
        experiment_id: str,
        model_used: str,  # 'A' or 'B'
        prediction: Any,
        actual: Optional[Any] = None,
        latency_ms: float = 0
    ) -> None:
        """Record a prediction in the experiment"""
        if experiment_id not in self.results:
            self.results[experiment_id] = []
        
        self.results[experiment_id].append({
            'model': model_used,
            'prediction': prediction,
            'actual': actual,
            'latency_ms': latency_ms,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """Get experiment results and statistics"""
        if experiment_id not in self.experiments:
            return {}
        
        experiment = self.experiments[experiment_id]
        results = self.results.get(experiment_id, [])
        
        # Calculate metrics for each model
        model_a_results = [r for r in results if r['model'] == 'A' and r['actual'] is not None]
        model_b_results = [r for r in results if r['model'] == 'B' and r['actual'] is not None]
        
        def calculate_accuracy(predictions):
            if not predictions:
                return 0
            correct = sum(1 for p in predictions if p['prediction'] == p['actual'])
            return correct / len(predictions)
        
        return {
            'experiment_id': experiment_id,
            'status': experiment['status'],
            'model_a': {
                'predictions': len(model_a_results),
                'accuracy': calculate_accuracy(model_a_results),
                'avg_latency_ms': np.mean([r['latency_ms'] for r in model_a_results]) if model_a_results else 0
            },
            'model_b': {
                'predictions': len(model_b_results),
                'accuracy': calculate_accuracy(model_b_results),
                'avg_latency_ms': np.mean([r['latency_ms'] for r in model_b_results]) if model_b_results else 0
            },
            'total_samples': len(results),
            'min_samples_reached': len(results) >= experiment['min_samples']
        }


# Global instances
automl_engine = AutoMLEngine()
feature_engineer = FeatureEngineer()
model_registry = ModelRegistry()
ab_test_manager = ABTestManager()


def get_automl_engine() -> AutoMLEngine:
    return automl_engine

def get_model_registry() -> ModelRegistry:
    return model_registry

def get_ab_test_manager() -> ABTestManager:
    return ab_test_manager
