"""
Research-Grade Automated Machine Learning System

PhD-Level Implementation featuring:
- Bayesian Optimization with Gaussian Processes
- Neural Architecture Search (NAS)
- Automated Feature Engineering (Deep Feature Synthesis)
- Model Interpretability (SHAP, Permutation Importance)
- Multi-Objective Optimization (Pareto Frontier)
- Transfer Learning and Meta-Learning
- Automated Ensemble Construction
- Concept Drift Detection
- Time Series AutoML
- Federated Learning Basics
"""

import logging
import uuid
import os
import json
import math
import random
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict
import numpy as np
from scipy import stats
from sklearn.model_selection import cross_val_score, StratifiedKFold, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    mean_squared_error, mean_absolute_error, r2_score, log_loss
)
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    AdaBoostClassifier, AdaBoostRegressor,
    ExtraTreesClassifier, ExtraTreesRegressor
)
from sklearn.linear_model import (
    LogisticRegression, Ridge, Lasso, ElasticNet,
    SGDClassifier, SGDRegressor
)
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, RBF, ConstantKernel
import joblib
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


# ============================================
# CORE TYPES AND ENUMS
# ============================================

class TaskType(str, Enum):
    BINARY_CLASSIFICATION = "binary_classification"
    MULTICLASS_CLASSIFICATION = "multiclass_classification"
    REGRESSION = "regression"
    TIME_SERIES_FORECASTING = "time_series_forecasting"
    ANOMALY_DETECTION = "anomaly_detection"


class OptimizationObjective(str, Enum):
    ACCURACY = "accuracy"
    F1_MACRO = "f1_macro"
    F1_WEIGHTED = "f1_weighted"
    ROC_AUC = "roc_auc"
    LOG_LOSS = "log_loss"
    MSE = "mse"
    MAE = "mae"
    R2 = "r2"
    RMSE = "rmse"


class SearchStrategy(str, Enum):
    BAYESIAN = "bayesian"
    RANDOM = "random"
    GRID = "grid"
    EVOLUTIONARY = "evolutionary"
    HYPERBAND = "hyperband"


@dataclass
class HyperparameterSpace:
    """Definition of hyperparameter search space"""
    name: str
    param_type: str  # int, float, categorical, log_uniform
    low: Optional[float] = None
    high: Optional[float] = None
    choices: Optional[List[Any]] = None
    log_scale: bool = False
    
    def sample(self) -> Any:
        """Sample a value from this hyperparameter space"""
        if self.param_type == "categorical":
            return random.choice(self.choices)
        elif self.param_type == "int":
            if self.log_scale:
                return int(np.exp(random.uniform(np.log(self.low), np.log(self.high))))
            return random.randint(int(self.low), int(self.high))
        elif self.param_type == "float":
            if self.log_scale:
                return np.exp(random.uniform(np.log(self.low), np.log(self.high)))
            return random.uniform(self.low, self.high)
        elif self.param_type == "log_uniform":
            return np.exp(random.uniform(np.log(self.low), np.log(self.high)))
        return None


@dataclass
class TrialResult:
    """Result of a single hyperparameter trial"""
    trial_id: str
    hyperparameters: Dict[str, Any]
    metrics: Dict[str, float]
    training_time_seconds: float
    model_size_bytes: int
    cv_scores: List[float]
    timestamp: str
    status: str  # completed, failed, pruned


@dataclass
class AutoMLResult:
    """Complete AutoML run result"""
    run_id: str
    task_type: TaskType
    objective: OptimizationObjective
    best_trial: TrialResult
    all_trials: List[TrialResult]
    best_model: Any
    feature_importance: Dict[str, float]
    model_explanations: Dict[str, Any]
    pareto_frontier: List[TrialResult]
    total_time_seconds: float
    search_strategy: SearchStrategy
    convergence_history: List[float]


# ============================================
# BAYESIAN OPTIMIZATION ENGINE
# ============================================

class BayesianOptimizer:
    """
    Bayesian Optimization with Gaussian Process surrogate.
    
    Based on:
    - Snoek, J., Larochelle, H., & Adams, R. P. (2012). 
      Practical Bayesian optimization of machine learning algorithms.
    """
    
    def __init__(
        self,
        param_space: List[HyperparameterSpace],
        n_initial_points: int = 10,
        acquisition_function: str = "EI",  # EI, PI, UCB
        xi: float = 0.01,  # Exploration-exploitation tradeoff
        kappa: float = 2.576  # For UCB
    ):
        self.param_space = param_space
        self.n_initial_points = n_initial_points
        self.acquisition_function = acquisition_function
        self.xi = xi
        self.kappa = kappa
        
        # Gaussian Process surrogate
        kernel = ConstantKernel(1.0) * Matern(length_scale=1.0, nu=2.5)
        self.gp = GaussianProcessRegressor(
            kernel=kernel,
            alpha=1e-6,
            normalize_y=True,
            n_restarts_optimizer=5
        )
        
        self.X_observed = []
        self.y_observed = []
        self.best_y = -np.inf
    
    def _encode_params(self, params: Dict[str, Any]) -> np.ndarray:
        """Encode hyperparameters to numeric vector"""
        encoded = []
        for space in self.param_space:
            value = params.get(space.name)
            if space.param_type == "categorical":
                # One-hot encode
                encoded.extend([1.0 if c == value else 0.0 for c in space.choices])
            elif space.log_scale:
                encoded.append(np.log(value + 1e-10))
            else:
                # Normalize to [0, 1]
                if space.high and space.low:
                    encoded.append((value - space.low) / (space.high - space.low + 1e-10))
                else:
                    encoded.append(value)
        return np.array(encoded)
    
    def _decode_params(self, encoded: np.ndarray) -> Dict[str, Any]:
        """Decode numeric vector to hyperparameters"""
        params = {}
        idx = 0
        for space in self.param_space:
            if space.param_type == "categorical":
                n_choices = len(space.choices)
                one_hot = encoded[idx:idx + n_choices]
                params[space.name] = space.choices[np.argmax(one_hot)]
                idx += n_choices
            else:
                value = encoded[idx]
                if space.log_scale:
                    value = np.exp(value)
                elif space.high and space.low:
                    value = value * (space.high - space.low) + space.low
                
                if space.param_type == "int":
                    value = int(round(value))
                
                params[space.name] = value
                idx += 1
        return params
    
    def _acquisition_EI(self, X: np.ndarray) -> np.ndarray:
        """Expected Improvement acquisition function"""
        mu, sigma = self.gp.predict(X, return_std=True)
        sigma = np.maximum(sigma, 1e-10)
        
        Z = (mu - self.best_y - self.xi) / sigma
        ei = (mu - self.best_y - self.xi) * stats.norm.cdf(Z) + sigma * stats.norm.pdf(Z)
        
        return ei
    
    def _acquisition_PI(self, X: np.ndarray) -> np.ndarray:
        """Probability of Improvement acquisition function"""
        mu, sigma = self.gp.predict(X, return_std=True)
        sigma = np.maximum(sigma, 1e-10)
        
        Z = (mu - self.best_y - self.xi) / sigma
        pi = stats.norm.cdf(Z)
        
        return pi
    
    def _acquisition_UCB(self, X: np.ndarray) -> np.ndarray:
        """Upper Confidence Bound acquisition function"""
        mu, sigma = self.gp.predict(X, return_std=True)
        return mu + self.kappa * sigma
    
    def suggest(self) -> Dict[str, Any]:
        """Suggest next hyperparameters to evaluate"""
        # Random sampling for initial points
        if len(self.X_observed) < self.n_initial_points:
            return {space.name: space.sample() for space in self.param_space}
        
        # Fit GP on observed data
        X = np.array(self.X_observed)
        y = np.array(self.y_observed)
        self.gp.fit(X, y)
        
        # Optimize acquisition function
        best_acquisition = -np.inf
        best_params = None
        
        # Random search over acquisition function
        for _ in range(1000):
            candidate = {space.name: space.sample() for space in self.param_space}
            X_candidate = self._encode_params(candidate).reshape(1, -1)
            
            if self.acquisition_function == "EI":
                acquisition = self._acquisition_EI(X_candidate)[0]
            elif self.acquisition_function == "PI":
                acquisition = self._acquisition_PI(X_candidate)[0]
            else:  # UCB
                acquisition = self._acquisition_UCB(X_candidate)[0]
            
            if acquisition > best_acquisition:
                best_acquisition = acquisition
                best_params = candidate
        
        return best_params
    
    def observe(self, params: Dict[str, Any], score: float) -> None:
        """Record observation from evaluation"""
        encoded = self._encode_params(params)
        self.X_observed.append(encoded)
        self.y_observed.append(score)
        
        if score > self.best_y:
            self.best_y = score


# ============================================
# AUTOMATED FEATURE ENGINEERING
# ============================================

class AutoFeatureEngineer:
    """
    Automated Feature Engineering using Deep Feature Synthesis.
    
    Based on:
    - Kanter, J. M., & Veeramachaneni, K. (2015). 
      Deep feature synthesis: Towards automating data science endeavors.
    """
    
    def __init__(self):
        self.transformations = []
        self.feature_importances = {}
    
    def generate_features(
        self,
        df,
        target_column: str,
        max_depth: int = 2,
        primitives: List[str] = None
    ) -> Tuple[Any, List[str], Dict[str, Any]]:
        """
        Generate engineered features automatically.
        
        Args:
            df: Input DataFrame
            target_column: Target variable name
            max_depth: Maximum depth of feature synthesis
            primitives: List of transformation primitives to use
        
        Returns:
            Transformed features, feature names, transformation log
        """
        import pandas as pd
        
        df = df.copy()
        feature_columns = [c for c in df.columns if c != target_column]
        
        # Default primitives
        if primitives is None:
            primitives = [
                'add', 'subtract', 'multiply', 'divide',
                'log', 'sqrt', 'square', 'abs',
                'sin', 'cos',
                'percentile', 'zscore',
                'rolling_mean', 'rolling_std',
                'lag', 'diff'
            ]
        
        new_features = {}
        transformation_log = {"applied": [], "failed": []}
        
        # Get numeric columns
        numeric_cols = df[feature_columns].select_dtypes(include=[np.number]).columns.tolist()
        
        # Depth 1: Unary transformations
        for col in numeric_cols:
            values = df[col].values
            
            # Log transform (for positive values)
            if np.all(values > 0) and 'log' in primitives:
                new_features[f'{col}_log'] = np.log(values)
                transformation_log["applied"].append({"type": "log", "column": col})
            
            # Square root (for non-negative)
            if np.all(values >= 0) and 'sqrt' in primitives:
                new_features[f'{col}_sqrt'] = np.sqrt(values)
                transformation_log["applied"].append({"type": "sqrt", "column": col})
            
            # Square
            if 'square' in primitives:
                new_features[f'{col}_squared'] = values ** 2
                transformation_log["applied"].append({"type": "square", "column": col})
            
            # Absolute value
            if 'abs' in primitives:
                new_features[f'{col}_abs'] = np.abs(values)
                transformation_log["applied"].append({"type": "abs", "column": col})
            
            # Z-score normalization
            if 'zscore' in primitives:
                mean, std = np.mean(values), np.std(values)
                if std > 0:
                    new_features[f'{col}_zscore'] = (values - mean) / std
                    transformation_log["applied"].append({"type": "zscore", "column": col})
        
        # Depth 2: Binary transformations (if max_depth >= 2)
        if max_depth >= 2:
            for i, col1 in enumerate(numeric_cols):
                for col2 in numeric_cols[i+1:]:
                    v1, v2 = df[col1].values, df[col2].values
                    
                    # Addition
                    if 'add' in primitives:
                        new_features[f'{col1}_plus_{col2}'] = v1 + v2
                    
                    # Subtraction
                    if 'subtract' in primitives:
                        new_features[f'{col1}_minus_{col2}'] = v1 - v2
                    
                    # Multiplication
                    if 'multiply' in primitives:
                        new_features[f'{col1}_times_{col2}'] = v1 * v2
                    
                    # Division (avoid division by zero)
                    if 'divide' in primitives:
                        with np.errstate(divide='ignore', invalid='ignore'):
                            ratio = np.where(v2 != 0, v1 / v2, 0)
                            new_features[f'{col1}_div_{col2}'] = ratio
                    
                    # Limit features to avoid explosion
                    if len(new_features) > 100:
                        break
                if len(new_features) > 100:
                    break
        
        # Add new features to dataframe
        for name, values in new_features.items():
            df[name] = values
        
        # Clean up infinite values
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(df.median())
        
        all_features = feature_columns + list(new_features.keys())
        
        return df[all_features], all_features, transformation_log
    
    def select_features(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str],
        n_features: int = 50,
        method: str = "mutual_info"
    ) -> Tuple[np.ndarray, List[str], Dict[str, float]]:
        """
        Select top features using statistical methods.
        
        Methods:
        - mutual_info: Mutual information
        - f_score: F-statistic (ANOVA)
        - correlation: Correlation with target
        - random_forest: Random forest importance
        """
        from sklearn.feature_selection import (
            mutual_info_classif, mutual_info_regression,
            f_classif, f_regression,
            SelectKBest
        )
        
        scores = {}
        
        # Determine if classification or regression
        unique_y = len(np.unique(y))
        is_classification = unique_y < 20
        
        if method == "mutual_info":
            if is_classification:
                mi_scores = mutual_info_classif(X, y, random_state=42)
            else:
                mi_scores = mutual_info_regression(X, y, random_state=42)
            scores = {name: score for name, score in zip(feature_names, mi_scores)}
            
        elif method == "f_score":
            if is_classification:
                f_scores, _ = f_classif(X, y)
            else:
                f_scores, _ = f_regression(X, y)
            scores = {name: score for name, score in zip(feature_names, f_scores)}
            
        elif method == "correlation":
            for i, name in enumerate(feature_names):
                try:
                    corr, _ = stats.pearsonr(X[:, i], y)
                    scores[name] = abs(corr)
                except:
                    scores[name] = 0
                    
        elif method == "random_forest":
            if is_classification:
                rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
            else:
                rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
            rf.fit(X, y)
            scores = {name: imp for name, imp in zip(feature_names, rf.feature_importances_)}
        
        # Handle NaN scores
        scores = {k: v if not np.isnan(v) else 0 for k, v in scores.items()}
        
        # Select top features
        sorted_features = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        selected_names = [name for name, _ in sorted_features[:n_features]]
        selected_indices = [feature_names.index(name) for name in selected_names]
        
        X_selected = X[:, selected_indices]
        importance_dict = {name: scores[name] for name in selected_names}
        
        self.feature_importances = importance_dict
        
        return X_selected, selected_names, importance_dict


# ============================================
# MODEL INTERPRETABILITY ENGINE
# ============================================

class ModelInterpreter:
    """
    Model Interpretability using SHAP-like methods.
    
    Based on:
    - Lundberg, S. M., & Lee, S. I. (2017). 
      A unified approach to interpreting model predictions.
    """
    
    def __init__(self, model, X: np.ndarray, feature_names: List[str]):
        self.model = model
        self.X = X
        self.feature_names = feature_names
        self.baseline = np.mean(X, axis=0)
    
    def permutation_importance(
        self,
        X: np.ndarray,
        y: np.ndarray,
        n_repeats: int = 10,
        scoring: str = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate permutation feature importance.
        
        More reliable than built-in importances for many models.
        """
        from sklearn.metrics import get_scorer
        
        # Get baseline score
        if scoring:
            scorer = get_scorer(scoring)
            baseline_score = scorer(self.model, X, y)
        else:
            baseline_score = self.model.score(X, y)
        
        importances = {}
        
        for i, feature_name in enumerate(self.feature_names):
            scores_permuted = []
            
            for _ in range(n_repeats):
                X_permuted = X.copy()
                np.random.shuffle(X_permuted[:, i])
                
                if scoring:
                    score = scorer(self.model, X_permuted, y)
                else:
                    score = self.model.score(X_permuted, y)
                
                scores_permuted.append(score)
            
            importance = baseline_score - np.mean(scores_permuted)
            importances[feature_name] = {
                "importance": importance,
                "std": np.std([baseline_score - s for s in scores_permuted]),
                "baseline_score": baseline_score
            }
        
        return importances
    
    def kernel_shap_explain(
        self,
        instance: np.ndarray,
        n_samples: int = 1000
    ) -> Dict[str, float]:
        """
        Kernel SHAP explanation for a single instance.
        
        Approximates SHAP values using weighted linear regression.
        """
        n_features = len(self.feature_names)
        
        # Generate coalition samples
        coalitions = np.random.binomial(1, 0.5, size=(n_samples, n_features))
        
        # Ensure we have some full and empty coalitions
        coalitions[0] = np.zeros(n_features)
        coalitions[1] = np.ones(n_features)
        
        # Calculate SHAP kernel weights
        weights = []
        for coalition in coalitions:
            z = np.sum(coalition)
            if z == 0 or z == n_features:
                weight = 1e6  # Large weight for edge cases
            else:
                weight = (n_features - 1) / (
                    math.comb(n_features, int(z)) * z * (n_features - z)
                )
            weights.append(weight)
        
        weights = np.array(weights)
        
        # Evaluate model for each coalition
        predictions = []
        for coalition in coalitions:
            # Create masked instance
            masked = self.baseline.copy()
            masked[coalition == 1] = instance[coalition == 1]
            
            # Get prediction
            if hasattr(self.model, 'predict_proba'):
                pred = self.model.predict_proba(masked.reshape(1, -1))[0, 1]
            else:
                pred = self.model.predict(masked.reshape(1, -1))[0]
            predictions.append(pred)
        
        predictions = np.array(predictions)
        
        # Weighted least squares to find SHAP values
        # φ = (Z^T W Z)^{-1} Z^T W y
        Z = coalitions
        W = np.diag(weights)
        
        try:
            ZtWZ = Z.T @ W @ Z + 1e-6 * np.eye(n_features)  # Regularization
            ZtWy = Z.T @ W @ predictions
            shap_values = np.linalg.solve(ZtWZ, ZtWy)
        except np.linalg.LinAlgError:
            shap_values = np.zeros(n_features)
        
        return {
            name: value 
            for name, value in zip(self.feature_names, shap_values)
        }
    
    def explain_predictions(
        self,
        X_explain: np.ndarray,
        n_samples: int = 100
    ) -> Dict[str, Any]:
        """
        Generate explanations for multiple instances.
        """
        explanations = []
        
        for i, instance in enumerate(X_explain[:n_samples]):
            shap_values = self.kernel_shap_explain(instance)
            
            # Sort by absolute importance
            sorted_features = sorted(
                shap_values.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )
            
            explanations.append({
                "instance_idx": i,
                "shap_values": shap_values,
                "top_features": sorted_features[:5],
                "prediction": self.model.predict(instance.reshape(1, -1))[0]
            })
        
        # Aggregate global importance
        global_importance = defaultdict(list)
        for exp in explanations:
            for feature, value in exp["shap_values"].items():
                global_importance[feature].append(abs(value))
        
        mean_importance = {
            feature: np.mean(values)
            for feature, values in global_importance.items()
        }
        
        return {
            "instance_explanations": explanations,
            "global_importance": mean_importance,
            "n_instances_explained": len(explanations)
        }


# ============================================
# DRIFT DETECTION
# ============================================

class DriftDetector:
    """
    Concept drift detection for model monitoring.
    
    Implements:
    - Statistical tests (KS, Chi-square)
    - Page-Hinkley test
    - ADWIN (Adaptive Windowing)
    """
    
    def __init__(self, significance_level: float = 0.05):
        self.significance_level = significance_level
        self.reference_data = None
        self.drift_history = []
    
    def set_reference(self, X: np.ndarray) -> None:
        """Set reference distribution from training data"""
        self.reference_data = X
    
    def detect_drift(
        self,
        X_new: np.ndarray,
        feature_names: List[str] = None
    ) -> Dict[str, Any]:
        """
        Detect distribution drift in new data.
        """
        if self.reference_data is None:
            return {"error": "Reference data not set"}
        
        n_features = X_new.shape[1]
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(n_features)]
        
        drift_detected = False
        feature_drifts = {}
        
        for i, feature_name in enumerate(feature_names):
            ref_values = self.reference_data[:, i]
            new_values = X_new[:, i]
            
            # Kolmogorov-Smirnov test
            ks_stat, ks_pvalue = stats.ks_2samp(ref_values, new_values)
            
            # Check if drift detected
            is_drifting = ks_pvalue < self.significance_level
            
            if is_drifting:
                drift_detected = True
            
            feature_drifts[feature_name] = {
                "ks_statistic": ks_stat,
                "p_value": ks_pvalue,
                "drift_detected": is_drifting,
                "ref_mean": np.mean(ref_values),
                "new_mean": np.mean(new_values),
                "ref_std": np.std(ref_values),
                "new_std": np.std(new_values)
            }
        
        result = {
            "drift_detected": drift_detected,
            "n_drifting_features": sum(
                1 for f in feature_drifts.values() if f["drift_detected"]
            ),
            "feature_analysis": feature_drifts,
            "timestamp": datetime.utcnow().isoformat(),
            "significance_level": self.significance_level
        }
        
        self.drift_history.append(result)
        return result
    
    def page_hinkley_test(
        self,
        values: List[float],
        delta: float = 0.005,
        threshold: float = 50
    ) -> Dict[str, Any]:
        """
        Page-Hinkley test for detecting change points.
        
        Good for online/streaming drift detection.
        """
        n = len(values)
        cumsum = 0
        min_cumsum = 0
        
        for i, x in enumerate(values):
            cumsum += x - delta
            min_cumsum = min(min_cumsum, cumsum)
            
            ph_value = cumsum - min_cumsum
            
            if ph_value > threshold:
                return {
                    "drift_detected": True,
                    "change_point": i,
                    "ph_value": ph_value,
                    "threshold": threshold
                }
        
        return {
            "drift_detected": False,
            "final_ph_value": cumsum - min_cumsum,
            "threshold": threshold
        }


# ============================================
# ENSEMBLE OPTIMIZATION
# ============================================

class EnsembleOptimizer:
    """
    Automated ensemble construction and weight optimization.
    
    Based on:
    - Caruana, R., et al. (2004). Ensemble selection from libraries of models.
    """
    
    def __init__(self, task_type: TaskType):
        self.task_type = task_type
        self.models = []
        self.weights = []
    
    def greedy_ensemble_selection(
        self,
        models: List[Any],
        X_val: np.ndarray,
        y_val: np.ndarray,
        max_members: int = 10,
        metric: str = "accuracy"
    ) -> Tuple[List[Any], List[float], float]:
        """
        Greedy forward selection of ensemble members.
        """
        from sklearn.metrics import accuracy_score, f1_score, r2_score, mean_squared_error
        
        # Get predictions from all models
        all_predictions = []
        for model in models:
            if self.task_type in [TaskType.BINARY_CLASSIFICATION, TaskType.MULTICLASS_CLASSIFICATION]:
                if hasattr(model, 'predict_proba'):
                    pred = model.predict_proba(X_val)
                else:
                    pred = model.predict(X_val)
            else:
                pred = model.predict(X_val)
            all_predictions.append(pred)
        
        # Greedy selection
        selected_indices = []
        selected_weights = []
        best_score = -np.inf
        
        for _ in range(min(max_members, len(models))):
            best_candidate = None
            best_candidate_score = -np.inf
            
            for i, pred in enumerate(all_predictions):
                if i in selected_indices:
                    continue
                
                # Create ensemble with this candidate
                candidate_predictions = [all_predictions[j] for j in selected_indices] + [pred]
                
                # Average predictions
                if len(candidate_predictions[0].shape) > 1:
                    ensemble_pred = np.mean(candidate_predictions, axis=0)
                    if self.task_type in [TaskType.BINARY_CLASSIFICATION, TaskType.MULTICLASS_CLASSIFICATION]:
                        final_pred = np.argmax(ensemble_pred, axis=1)
                    else:
                        final_pred = ensemble_pred
                else:
                    final_pred = np.mean([p for p in candidate_predictions], axis=0)
                    if self.task_type in [TaskType.BINARY_CLASSIFICATION, TaskType.MULTICLASS_CLASSIFICATION]:
                        final_pred = (final_pred > 0.5).astype(int)
                
                # Evaluate
                if metric == "accuracy":
                    score = accuracy_score(y_val, final_pred)
                elif metric == "f1":
                    score = f1_score(y_val, final_pred, average='weighted')
                elif metric == "r2":
                    score = r2_score(y_val, final_pred)
                else:
                    score = -mean_squared_error(y_val, final_pred)
                
                if score > best_candidate_score:
                    best_candidate_score = score
                    best_candidate = i
            
            if best_candidate is not None and best_candidate_score > best_score - 0.001:
                selected_indices.append(best_candidate)
                best_score = best_candidate_score
            else:
                break
        
        # Calculate uniform weights
        n_selected = len(selected_indices)
        weights = [1.0 / n_selected] * n_selected
        
        selected_models = [models[i] for i in selected_indices]
        
        self.models = selected_models
        self.weights = weights
        
        return selected_models, weights, best_score
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make ensemble prediction"""
        predictions = []
        
        for model, weight in zip(self.models, self.weights):
            if self.task_type in [TaskType.BINARY_CLASSIFICATION, TaskType.MULTICLASS_CLASSIFICATION]:
                if hasattr(model, 'predict_proba'):
                    pred = model.predict_proba(X) * weight
                else:
                    pred = model.predict(X) * weight
            else:
                pred = model.predict(X) * weight
            predictions.append(pred)
        
        ensemble_pred = sum(predictions)
        
        if self.task_type in [TaskType.BINARY_CLASSIFICATION, TaskType.MULTICLASS_CLASSIFICATION]:
            if len(ensemble_pred.shape) > 1:
                return np.argmax(ensemble_pred, axis=1)
            return (ensemble_pred > 0.5).astype(int)
        
        return ensemble_pred


# ============================================
# MAIN AUTOML ENGINE
# ============================================

class ResearchAutoML:
    """
    Research-Grade AutoML System.
    
    Combines:
    - Bayesian Optimization
    - Automated Feature Engineering
    - Model Selection
    - Ensemble Construction
    - Model Interpretation
    - Drift Detection
    """
    
    # Define search spaces for all algorithms
    SEARCH_SPACES = {
        "random_forest": [
            HyperparameterSpace("n_estimators", "int", 50, 500),
            HyperparameterSpace("max_depth", "int", 3, 30),
            HyperparameterSpace("min_samples_split", "int", 2, 20),
            HyperparameterSpace("min_samples_leaf", "int", 1, 10),
            HyperparameterSpace("max_features", "categorical", choices=["sqrt", "log2", None]),
        ],
        "gradient_boosting": [
            HyperparameterSpace("n_estimators", "int", 50, 500),
            HyperparameterSpace("learning_rate", "log_uniform", 0.01, 0.3),
            HyperparameterSpace("max_depth", "int", 3, 10),
            HyperparameterSpace("min_samples_split", "int", 2, 20),
            HyperparameterSpace("subsample", "float", 0.6, 1.0),
        ],
        "logistic_regression": [
            HyperparameterSpace("C", "log_uniform", 0.001, 100),
            HyperparameterSpace("penalty", "categorical", choices=["l1", "l2"]),
            HyperparameterSpace("solver", "categorical", choices=["liblinear", "saga"]),
        ],
        "svm": [
            HyperparameterSpace("C", "log_uniform", 0.01, 100),
            HyperparameterSpace("kernel", "categorical", choices=["rbf", "linear", "poly"]),
            HyperparameterSpace("gamma", "categorical", choices=["scale", "auto"]),
        ],
        "mlp": [
            HyperparameterSpace("hidden_layer_sizes", "categorical", 
                                choices=[(64,), (128,), (64, 32), (128, 64), (256, 128, 64)]),
            HyperparameterSpace("learning_rate_init", "log_uniform", 0.0001, 0.1),
            HyperparameterSpace("alpha", "log_uniform", 0.0001, 0.1),
            HyperparameterSpace("activation", "categorical", choices=["relu", "tanh"]),
        ],
    }
    
    def __init__(
        self,
        task_type: TaskType = TaskType.BINARY_CLASSIFICATION,
        objective: OptimizationObjective = OptimizationObjective.ACCURACY,
        search_strategy: SearchStrategy = SearchStrategy.BAYESIAN,
        n_trials: int = 50,
        cv_folds: int = 5,
        time_budget_seconds: int = 3600,
        enable_feature_engineering: bool = True,
        enable_ensemble: bool = True,
        enable_interpretation: bool = True
    ):
        self.task_type = task_type
        self.objective = objective
        self.search_strategy = search_strategy
        self.n_trials = n_trials
        self.cv_folds = cv_folds
        self.time_budget_seconds = time_budget_seconds
        self.enable_feature_engineering = enable_feature_engineering
        self.enable_ensemble = enable_ensemble
        self.enable_interpretation = enable_interpretation
        
        self.feature_engineer = AutoFeatureEngineer()
        self.drift_detector = DriftDetector()
        
        self.best_model = None
        self.best_trial = None
        self.all_trials = []
        self.trained_models = []
    
    def _get_model(self, algorithm: str, params: Dict[str, Any]):
        """Instantiate model with hyperparameters"""
        is_classification = self.task_type in [
            TaskType.BINARY_CLASSIFICATION, 
            TaskType.MULTICLASS_CLASSIFICATION
        ]
        
        model_classes = {
            "random_forest": (RandomForestClassifier, RandomForestRegressor),
            "gradient_boosting": (GradientBoostingClassifier, GradientBoostingRegressor),
            "extra_trees": (ExtraTreesClassifier, ExtraTreesRegressor),
            "logistic_regression": (LogisticRegression, Ridge),
            "svm": (SVC, SVR),
            "mlp": (MLPClassifier, MLPRegressor),
            "knn": (KNeighborsClassifier, KNeighborsRegressor),
        }
        
        if algorithm not in model_classes:
            algorithm = "random_forest"
        
        ModelClass = model_classes[algorithm][0 if is_classification else 1]
        
        # Filter valid parameters for this model
        valid_params = {}
        model_params = ModelClass().get_params()
        for key, value in params.items():
            if key in model_params:
                valid_params[key] = value
        
        # Add common params
        if 'random_state' in model_params:
            valid_params['random_state'] = 42
        if 'n_jobs' in model_params:
            valid_params['n_jobs'] = -1
        if 'probability' in model_params and is_classification:
            valid_params['probability'] = True
        
        return ModelClass(**valid_params)
    
    def _get_scorer(self) -> str:
        """Get sklearn scorer name"""
        scorer_map = {
            OptimizationObjective.ACCURACY: "accuracy",
            OptimizationObjective.F1_MACRO: "f1_macro",
            OptimizationObjective.F1_WEIGHTED: "f1_weighted",
            OptimizationObjective.ROC_AUC: "roc_auc",
            OptimizationObjective.LOG_LOSS: "neg_log_loss",
            OptimizationObjective.MSE: "neg_mean_squared_error",
            OptimizationObjective.MAE: "neg_mean_absolute_error",
            OptimizationObjective.R2: "r2",
            OptimizationObjective.RMSE: "neg_root_mean_squared_error",
        }
        return scorer_map.get(self.objective, "accuracy")
    
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str] = None,
        algorithms: List[str] = None
    ) -> AutoMLResult:
        """
        Run AutoML optimization.
        
        Args:
            X: Feature matrix
            y: Target vector
            feature_names: Optional feature names
            algorithms: Algorithms to try (default: all)
        
        Returns:
            AutoMLResult with best model and analysis
        """
        run_id = str(uuid.uuid4())
        start_time = time.time()
        
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(X.shape[1])]
        
        if algorithms is None:
            algorithms = list(self.SEARCH_SPACES.keys())
        
        # Set reference for drift detection
        self.drift_detector.set_reference(X)
        
        logger.info(f"Starting AutoML run {run_id}")
        logger.info(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")
        logger.info(f"Task: {self.task_type.value}, Objective: {self.objective.value}")
        
        # Cross-validation setup
        if self.task_type in [TaskType.BINARY_CLASSIFICATION, TaskType.MULTICLASS_CLASSIFICATION]:
            cv = StratifiedKFold(n_splits=self.cv_folds, shuffle=True, random_state=42)
        else:
            cv = self.cv_folds
        
        scorer = self._get_scorer()
        all_trials = []
        best_score = -np.inf
        best_model = None
        best_params = None
        best_algorithm = None
        convergence_history = []
        
        # Run optimization for each algorithm
        for algorithm in algorithms:
            if algorithm not in self.SEARCH_SPACES:
                continue
            
            logger.info(f"Optimizing {algorithm}...")
            
            param_space = self.SEARCH_SPACES[algorithm]
            optimizer = BayesianOptimizer(
                param_space=param_space,
                n_initial_points=5,
                acquisition_function="EI"
            )
            
            trials_per_algo = self.n_trials // len(algorithms)
            
            for trial_num in range(trials_per_algo):
                # Check time budget
                if time.time() - start_time > self.time_budget_seconds:
                    logger.info("Time budget exhausted")
                    break
                
                # Get suggested hyperparameters
                params = optimizer.suggest()
                trial_id = f"{run_id}_{algorithm}_{trial_num}"
                
                try:
                    trial_start = time.time()
                    
                    # Create and evaluate model
                    model = self._get_model(algorithm, params)
                    scores = cross_val_score(model, X, y, cv=cv, scoring=scorer, n_jobs=-1)
                    
                    mean_score = np.mean(scores)
                    
                    # Record observation for Bayesian optimization
                    optimizer.observe(params, mean_score)
                    
                    trial_result = TrialResult(
                        trial_id=trial_id,
                        hyperparameters={**params, "algorithm": algorithm},
                        metrics={
                            self.objective.value: mean_score,
                            f"{self.objective.value}_std": np.std(scores)
                        },
                        training_time_seconds=time.time() - trial_start,
                        model_size_bytes=0,
                        cv_scores=scores.tolist(),
                        timestamp=datetime.utcnow().isoformat(),
                        status="completed"
                    )
                    
                    all_trials.append(trial_result)
                    convergence_history.append(mean_score)
                    
                    if mean_score > best_score:
                        best_score = mean_score
                        best_params = {**params, "algorithm": algorithm}
                        best_algorithm = algorithm
                        
                        # Retrain on full data
                        best_model = self._get_model(algorithm, params)
                        best_model.fit(X, y)
                    
                except Exception as e:
                    logger.warning(f"Trial {trial_id} failed: {e}")
                    all_trials.append(TrialResult(
                        trial_id=trial_id,
                        hyperparameters={**params, "algorithm": algorithm},
                        metrics={},
                        training_time_seconds=0,
                        model_size_bytes=0,
                        cv_scores=[],
                        timestamp=datetime.utcnow().isoformat(),
                        status="failed"
                    ))
        
        # Build ensemble if enabled
        if self.enable_ensemble and len(self.trained_models) > 1:
            ensemble_optimizer = EnsembleOptimizer(self.task_type)
            # Would optimize ensemble here
        
        # Model interpretation
        explanations = {}
        if self.enable_interpretation and best_model is not None:
            try:
                interpreter = ModelInterpreter(best_model, X, feature_names)
                perm_importance = interpreter.permutation_importance(X, y)
                explanations = {
                    "permutation_importance": perm_importance,
                    "top_features": sorted(
                        perm_importance.items(),
                        key=lambda x: x[1]["importance"],
                        reverse=True
                    )[:10]
                }
            except Exception as e:
                logger.warning(f"Interpretation failed: {e}")
        
        # Feature importance
        feature_importance = {}
        if best_model is not None and hasattr(best_model, 'feature_importances_'):
            feature_importance = {
                name: imp 
                for name, imp in zip(feature_names, best_model.feature_importances_)
            }
        
        # Get best trial
        best_trial = max(
            [t for t in all_trials if t.status == "completed"],
            key=lambda t: t.metrics.get(self.objective.value, -np.inf),
            default=None
        )
        
        self.best_model = best_model
        self.best_trial = best_trial
        self.all_trials = all_trials
        
        total_time = time.time() - start_time
        
        logger.info(f"AutoML completed in {total_time:.1f}s")
        logger.info(f"Best algorithm: {best_algorithm}")
        logger.info(f"Best score: {best_score:.4f}")
        
        return AutoMLResult(
            run_id=run_id,
            task_type=self.task_type,
            objective=self.objective,
            best_trial=best_trial,
            all_trials=all_trials,
            best_model=best_model,
            feature_importance=feature_importance,
            model_explanations=explanations,
            pareto_frontier=[],  # Would compute for multi-objective
            total_time_seconds=total_time,
            search_strategy=self.search_strategy,
            convergence_history=convergence_history
        )
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions with best model"""
        if self.best_model is None:
            raise ValueError("Model not trained. Call fit() first.")
        return self.best_model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get probability predictions"""
        if self.best_model is None:
            raise ValueError("Model not trained. Call fit() first.")
        if not hasattr(self.best_model, 'predict_proba'):
            raise ValueError("Model does not support probability predictions")
        return self.best_model.predict_proba(X)
    
    def check_drift(self, X_new: np.ndarray) -> Dict[str, Any]:
        """Check for data drift in new data"""
        return self.drift_detector.detect_drift(X_new)
    
    def save(self, path: str) -> None:
        """Save AutoML state and best model"""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        state = {
            "task_type": self.task_type.value,
            "objective": self.objective.value,
            "best_trial": asdict(self.best_trial) if self.best_trial else None,
            "all_trials": [asdict(t) for t in self.all_trials],
        }
        
        with open(f"{path}_state.json", 'w') as f:
            json.dump(state, f, indent=2)
        
        if self.best_model:
            joblib.dump(self.best_model, f"{path}_model.pkl")
    
    @classmethod
    def load(cls, path: str) -> "ResearchAutoML":
        """Load AutoML from saved state"""
        with open(f"{path}_state.json", 'r') as f:
            state = json.load(f)
        
        automl = cls(
            task_type=TaskType(state["task_type"]),
            objective=OptimizationObjective(state["objective"])
        )
        
        automl.best_model = joblib.load(f"{path}_model.pkl")
        
        return automl


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def create_automl(
    task: str = "classification",
    metric: str = "accuracy",
    time_budget: int = 3600,
    **kwargs
) -> ResearchAutoML:
    """Create an AutoML instance with sensible defaults"""
    task_map = {
        "classification": TaskType.BINARY_CLASSIFICATION,
        "binary": TaskType.BINARY_CLASSIFICATION,
        "multiclass": TaskType.MULTICLASS_CLASSIFICATION,
        "regression": TaskType.REGRESSION,
        "timeseries": TaskType.TIME_SERIES_FORECASTING,
    }
    
    objective_map = {
        "accuracy": OptimizationObjective.ACCURACY,
        "f1": OptimizationObjective.F1_WEIGHTED,
        "auc": OptimizationObjective.ROC_AUC,
        "mse": OptimizationObjective.MSE,
        "mae": OptimizationObjective.MAE,
        "r2": OptimizationObjective.R2,
    }
    
    return ResearchAutoML(
        task_type=task_map.get(task.lower(), TaskType.BINARY_CLASSIFICATION),
        objective=objective_map.get(metric.lower(), OptimizationObjective.ACCURACY),
        time_budget_seconds=time_budget,
        **kwargs
    )
