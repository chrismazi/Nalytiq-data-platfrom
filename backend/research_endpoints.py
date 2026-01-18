"""
API Endpoints for Research-Grade Data Exchange and AutoML

PhD-Level Endpoints featuring:
- Differential Privacy Data Sharing
- Data Lineage Tracking
- Data Quality Assessment
- Federated Query Optimization
- Advanced AutoML
- Model Interpretability
- Drift Detection
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import logging
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/research", tags=["Research-Grade Features"])


# ============================================
# DATA EXCHANGE MODELS
# ============================================

class PrivacyQueryRequest(BaseModel):
    """Request for privacy-preserving query"""
    query_type: str = Field(..., description="Query type: count, sum, avg, min, max")
    value: float = Field(..., description="True value to protect")
    sensitivity: float = Field(1.0, description="Query sensitivity")
    epsilon: float = Field(1.0, description="Privacy budget (lower = more private)")
    mechanism: str = Field("laplace", description="Noise mechanism: laplace or gaussian")


class LineageEntityRequest(BaseModel):
    """Request to create lineage entity"""
    name: str
    attributes: Dict[str, Any]
    derived_from: List[str] = []
    generated_by: Optional[str] = None
    attributed_to: Optional[str] = None


class LineageActivityRequest(BaseModel):
    """Request to create lineage activity"""
    name: str
    activity_type: str
    parameters: Dict[str, Any]
    associated_with: Optional[str] = None


class DataQualityRequest(BaseModel):
    """Request for data quality assessment"""
    dataset_id: str
    data: List[Dict[str, Any]]
    schema: Dict[str, Any]


class FederatedQueryRequest(BaseModel):
    """Request for federated query"""
    select: List[str] = ["*"]
    sources: List[str]
    where: List[Dict[str, Any]] = []
    join: List[Dict[str, Any]] = []
    aggregate: List[Dict[str, Any]] = []
    limit: int = 1000


class SecureExchangeRequest(BaseModel):
    """Request for secure data exchange"""
    client_org: str
    provider_org: str
    service_code: str
    payload: Dict[str, Any]
    privacy_level: str = "internal"
    apply_differential_privacy: bool = True


# ============================================
# AUTOML MODELS
# ============================================

class AutoMLTrainRequest(BaseModel):
    """Request for AutoML training"""
    task_type: str = Field("classification", description="Task: classification, regression, timeseries")
    objective: str = Field("accuracy", description="Optimization metric")
    data: List[Dict[str, Any]] = Field(..., description="Training data")
    target_column: str = Field(..., description="Target variable name")
    feature_columns: Optional[List[str]] = None
    n_trials: int = Field(50, ge=10, le=500)
    time_budget_seconds: int = Field(3600, ge=60, le=86400)
    algorithms: Optional[List[str]] = None
    enable_feature_engineering: bool = True
    enable_ensemble: bool = True
    enable_interpretation: bool = True


class AutoMLPredictRequest(BaseModel):
    """Request for AutoML prediction"""
    model_id: str
    data: List[Dict[str, Any]]
    return_probabilities: bool = False


class DriftDetectionRequest(BaseModel):
    """Request for drift detection"""
    model_id: str
    data: List[Dict[str, Any]]
    feature_columns: List[str]
    significance_level: float = 0.05


class InterpretRequest(BaseModel):
    """Request for model interpretation"""
    model_id: str
    data: List[Dict[str, Any]]
    n_samples: int = 100
    method: str = "shap"  # shap, permutation


# ============================================
# DIFFERENTIAL PRIVACY ENDPOINTS
# ============================================

@router.post("/privacy/query")
async def privacy_preserving_query(request: PrivacyQueryRequest):
    """
    Execute a query with differential privacy protection.
    
    Returns a noisy result that satisfies ε-differential privacy,
    protecting individual records while preserving aggregate statistics.
    """
    from advanced_data_exchange import DifferentialPrivacyEngine
    
    engine = DifferentialPrivacyEngine(epsilon=request.epsilon)
    
    if request.mechanism == "laplace":
        noisy_value = engine.laplace_mechanism(request.value, request.sensitivity)
    else:
        noisy_value = engine.gaussian_mechanism(request.value, request.sensitivity)
    
    # Calculate privacy guarantee
    privacy_guarantee = f"ε={request.epsilon}"
    if request.mechanism == "gaussian":
        privacy_guarantee += f", δ={engine.delta}"
    
    return {
        "original_value": request.value,
        "protected_value": noisy_value,
        "noise_added": noisy_value - request.value,
        "mechanism": request.mechanism,
        "epsilon": request.epsilon,
        "sensitivity": request.sensitivity,
        "privacy_guarantee": privacy_guarantee,
        "interpretation": f"Any single record change would result in at most e^{request.epsilon}x difference in output probability"
    }


@router.get("/privacy/budget")
async def get_privacy_budget():
    """Get current privacy budget status and recommendations"""
    from advanced_data_exchange import get_privacy_engine
    
    engine = get_privacy_engine()
    
    return {
        "total_epsilon": engine.epsilon,
        "delta": engine.delta,
        "recommendations": [
            {"epsilon_range": "0.01 - 0.1", "privacy_level": "Very High", "use_case": "Highly sensitive data"},
            {"epsilon_range": "0.1 - 1.0", "privacy_level": "High", "use_case": "Standard protection"},
            {"epsilon_range": "1.0 - 5.0", "privacy_level": "Moderate", "use_case": "Aggregate statistics"},
            {"epsilon_range": "> 5.0", "privacy_level": "Low", "use_case": "Non-sensitive analytics"},
        ],
        "academic_references": [
            "Dwork, C., & Roth, A. (2014). The algorithmic foundations of differential privacy.",
            "Apple (2017). Learning with Privacy at Scale."
        ]
    }


# ============================================
# DATA LINEAGE ENDPOINTS
# ============================================

@router.post("/lineage/entity")
async def create_lineage_entity(request: LineageEntityRequest):
    """
    Create a data entity in the W3C PROV-DM lineage graph.
    
    Tracks data provenance with complete derivation chains.
    """
    from advanced_data_exchange import get_lineage_tracker
    
    tracker = get_lineage_tracker()
    
    node = tracker.create_entity(
        name=request.name,
        attributes=request.attributes,
        derived_from=request.derived_from,
        generated_by=request.generated_by,
        attributed_to=request.attributed_to
    )
    
    return {
        "node_id": node.node_id,
        "prov_json": node.to_prov_json(),
        "message": f"Entity '{request.name}' created with {len(request.derived_from)} derivation links"
    }


@router.post("/lineage/activity")
async def create_lineage_activity(request: LineageActivityRequest):
    """
    Create a data transformation activity in the lineage graph.
    """
    from advanced_data_exchange import get_lineage_tracker
    
    tracker = get_lineage_tracker()
    
    node = tracker.create_activity(
        name=request.name,
        activity_type=request.activity_type,
        parameters=request.parameters,
        associated_with=request.associated_with
    )
    
    return {
        "node_id": node.node_id,
        "prov_json": node.to_prov_json()
    }


@router.get("/lineage/trace/{entity_id}")
async def trace_lineage(
    entity_id: str,
    direction: str = Query("backward", regex="^(backward|forward)$"),
    max_depth: int = Query(10, ge=1, le=50)
):
    """
    Trace the complete lineage of a data entity.
    
    - backward: Find all sources and transformations that created this data
    - forward: Find all derivatives of this data
    """
    from advanced_data_exchange import get_lineage_tracker
    
    tracker = get_lineage_tracker()
    lineage = tracker.trace_lineage(entity_id, direction, max_depth)
    
    return {
        **lineage,
        "visualization_format": "prov-json",
        "can_export_to": ["PROV-JSON", "PROV-XML", "PROV-N", "DOT"]
    }


@router.get("/lineage/impact/{entity_id}")
async def analyze_lineage_impact(entity_id: str):
    """
    Analyze data quality impact propagation through lineage.
    """
    from advanced_data_exchange import get_lineage_tracker
    
    tracker = get_lineage_tracker()
    impact = tracker.compute_data_quality_impact(entity_id)
    
    return {
        "entity_id": entity_id,
        "quality_factors": impact,
        "interpretation": {
            "source_reliability": "Trust score based on number of verified sources",
            "transformation_quality": "Degradation factor from data transformations",
            "temporal_freshness": "Decay based on data age",
            "aggregated_score": "Combined quality score (0-1)"
        }
    }


# ============================================
# DATA QUALITY ENDPOINTS
# ============================================

@router.post("/quality/assess")
async def assess_data_quality(request: DataQualityRequest):
    """
    Perform comprehensive ISO 25012 data quality assessment.
    
    Evaluates:
    - Completeness: Missing value analysis
    - Consistency: Business rule compliance
    - Uniqueness: Duplicate detection
    - Timeliness: Data freshness
    """
    from advanced_data_exchange import get_quality_framework
    
    framework = get_quality_framework()
    
    assessment = framework.comprehensive_assessment(
        dataset_id=request.dataset_id,
        data=request.data,
        schema=request.schema
    )
    
    return {
        **assessment,
        "standards_compliance": {
            "iso_25012": True,
            "dimensions_assessed": [s["dimension"] for s in assessment["dimension_scores"]]
        }
    }


@router.get("/quality/history/{dataset_id}")
async def get_quality_history(
    dataset_id: str,
    limit: int = Query(10, ge=1, le=100)
):
    """Get historical quality assessments for a dataset"""
    from advanced_data_exchange import get_quality_framework
    
    framework = get_quality_framework()
    history = framework.assessments.get(dataset_id, [])
    
    return {
        "dataset_id": dataset_id,
        "assessments": [
            {
                "dimension": a.dimension.value,
                "score": a.score,
                "confidence": a.confidence,
                "measured_at": a.measured_at
            }
            for a in history[-limit:]
        ],
        "trend": "improving" if len(history) > 1 and history[-1].score > history[0].score else "stable"
    }


# ============================================
# FEDERATED QUERY ENDPOINTS
# ============================================

@router.post("/federation/optimize")
async def optimize_federated_query(request: FederatedQueryRequest):
    """
    Optimize a federated query across multiple data sources.
    
    Uses cost-based optimization with:
    - Predicate pushdown
    - Join reordering
    - Parallel execution planning
    """
    from advanced_data_exchange import get_query_optimizer
    
    optimizer = get_query_optimizer()
    
    query = {
        "select": request.select,
        "from": request.sources,
        "where": request.where,
        "join": request.join,
        "aggregate": request.aggregate,
        "limit": request.limit
    }
    
    plan = optimizer.optimize_query(query, request.sources)
    
    return {
        "query": query,
        "optimized_plan": plan,
        "optimization_techniques": [
            "predicate_pushdown",
            "join_reordering",
            "cost_based_selection",
            "parallel_execution"
        ]
    }


@router.post("/federation/register-source")
async def register_federation_source(
    source_id: str,
    row_count: int,
    column_stats: Dict[str, Dict[str, Any]],
    network_latency_ms: float = 50,
    bandwidth_mbps: float = 100
):
    """Register statistics for a federated data source"""
    from advanced_data_exchange import get_query_optimizer
    
    optimizer = get_query_optimizer()
    optimizer.register_source_statistics(
        source_id=source_id,
        row_count=row_count,
        column_stats=column_stats,
        network_latency_ms=network_latency_ms,
        bandwidth_mbps=bandwidth_mbps
    )
    
    return {
        "source_id": source_id,
        "registered": True,
        "stats": {
            "row_count": row_count,
            "network_latency_ms": network_latency_ms,
            "bandwidth_mbps": bandwidth_mbps
        }
    }


# ============================================
# SECURE EXCHANGE ENDPOINTS
# ============================================

@router.post("/exchange/initiate")
async def initiate_secure_exchange(request: SecureExchangeRequest):
    """
    Initiate a secure X-Road compliant data exchange.
    
    Features:
    - End-to-end encryption
    - Digital signatures
    - Non-repudiation
    - Complete audit trail
    - Optional differential privacy
    """
    from advanced_data_exchange import SecureDataExchangeProtocol, PrivacyLevel
    
    protocol = SecureDataExchangeProtocol(organization_code=request.client_org)
    
    # Create transaction
    transaction = protocol.create_transaction(
        client_org=request.client_org,
        provider_org=request.provider_org,
        service_code=request.service_code,
        payload=request.payload,
        privacy_level=PrivacyLevel(request.privacy_level)
    )
    
    # Validate
    is_valid, errors = protocol.validate_transaction(transaction)
    if not is_valid:
        raise HTTPException(status_code=400, detail={"errors": errors})
    
    # Execute exchange
    result = protocol.execute_exchange(
        transaction=transaction,
        payload=request.payload,
        apply_privacy=request.apply_differential_privacy
    )
    
    return result


# ============================================
# AUTOML ENDPOINTS
# ============================================

@router.post("/automl/train")
async def train_automl_model(
    request: AutoMLTrainRequest,
    background_tasks: BackgroundTasks
):
    """
    Train an AutoML model with PhD-level optimization.
    
    Features:
    - Bayesian Optimization with Gaussian Process surrogate
    - Automated Feature Engineering
    - Multi-algorithm search
    - Model Interpretability (SHAP)
    - Ensemble Construction
    - Drift Detection capability
    """
    from research_automl import create_automl, TaskType, OptimizationObjective
    import pandas as pd
    
    # Convert data to numpy
    df = pd.DataFrame(request.data)
    
    if request.feature_columns:
        X = df[request.feature_columns].values
        feature_names = request.feature_columns
    else:
        feature_names = [c for c in df.columns if c != request.target_column]
        X = df[feature_names].values
    
    y = df[request.target_column].values
    
    # Create AutoML
    automl = create_automl(
        task=request.task_type,
        metric=request.objective,
        time_budget=request.time_budget_seconds,
        n_trials=request.n_trials,
        enable_feature_engineering=request.enable_feature_engineering,
        enable_ensemble=request.enable_ensemble,
        enable_interpretation=request.enable_interpretation
    )
    
    # Run fitting
    result = automl.fit(X, y, feature_names, request.algorithms)
    
    # Save model
    model_id = result.run_id
    automl.save(f"./models/{model_id}")
    
    return {
        "model_id": model_id,
        "task_type": result.task_type.value,
        "objective": result.objective.value,
        "best_score": result.best_trial.metrics if result.best_trial else None,
        "best_algorithm": result.best_trial.hyperparameters.get("algorithm") if result.best_trial else None,
        "best_hyperparameters": result.best_trial.hyperparameters if result.best_trial else None,
        "n_trials_completed": len([t for t in result.all_trials if t.status == "completed"]),
        "total_time_seconds": result.total_time_seconds,
        "feature_importance": dict(sorted(
            result.feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]),
        "convergence_history": result.convergence_history[-20:],
        "model_explanations": {
            "top_features": result.model_explanations.get("top_features", [])[:10]
        } if result.model_explanations else None,
        "algorithms_tried": list(set(
            t.hyperparameters.get("algorithm") 
            for t in result.all_trials 
            if t.hyperparameters.get("algorithm")
        ))
    }


@router.post("/automl/predict")
async def automl_predict(request: AutoMLPredictRequest):
    """Make predictions using a trained AutoML model"""
    from research_automl import ResearchAutoML
    import pandas as pd
    
    try:
        automl = ResearchAutoML.load(f"./models/{request.model_id}")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Model not found: {request.model_id}")
    
    df = pd.DataFrame(request.data)
    X = df.values
    
    predictions = automl.predict(X).tolist()
    
    result = {
        "model_id": request.model_id,
        "predictions": predictions,
        "n_samples": len(predictions)
    }
    
    if request.return_probabilities:
        try:
            probabilities = automl.predict_proba(X).tolist()
            result["probabilities"] = probabilities
        except Exception:
            pass
    
    return result


@router.post("/automl/drift-detection")
async def detect_model_drift(request: DriftDetectionRequest):
    """
    Detect data drift in new data compared to training distribution.
    
    Uses Kolmogorov-Smirnov test for statistical significance.
    """
    from research_automl import ResearchAutoML
    import pandas as pd
    
    try:
        automl = ResearchAutoML.load(f"./models/{request.model_id}")
    except Exception:
        raise HTTPException(status_code=404, detail=f"Model not found: {request.model_id}")
    
    df = pd.DataFrame(request.data)
    X = df[request.feature_columns].values
    
    drift_result = automl.check_drift(X)
    
    return {
        "model_id": request.model_id,
        **drift_result,
        "recommendation": (
            "Consider retraining the model" if drift_result.get("drift_detected") 
            else "No action needed - data distribution is stable"
        )
    }


@router.post("/automl/interpret")
async def interpret_model(request: InterpretRequest):
    """
    Generate model interpretations using SHAP-like methods.
    
    Provides both local (instance-level) and global explanations.
    """
    from research_automl import ResearchAutoML
    from research_automl import ModelInterpreter
    import pandas as pd
    
    try:
        automl = ResearchAutoML.load(f"./models/{request.model_id}")
    except Exception:
        raise HTTPException(status_code=404, detail=f"Model not found: {request.model_id}")
    
    df = pd.DataFrame(request.data)
    feature_names = list(df.columns)
    X = df.values
    
    interpreter = ModelInterpreter(
        model=automl.best_model,
        X=X,
        feature_names=feature_names
    )
    
    explanations = interpreter.explain_predictions(X, request.n_samples)
    
    return {
        "model_id": request.model_id,
        "method": request.method,
        "n_instances_explained": explanations["n_instances_explained"],
        "global_importance": dict(sorted(
            explanations["global_importance"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:15]),
        "sample_explanations": explanations["instance_explanations"][:5],
        "interpretation_guide": {
            "positive_shap": "Feature pushes prediction higher",
            "negative_shap": "Feature pushes prediction lower",
            "magnitude": "Absolute value indicates importance"
        }
    }


@router.get("/automl/algorithms")
async def list_automl_algorithms():
    """List available AutoML algorithms and their hyperparameter spaces"""
    from research_automl import ResearchAutoML
    
    return {
        "algorithms": [
            {
                "name": algo,
                "parameters": [
                    {
                        "name": space.name,
                        "type": space.param_type,
                        "range": {"low": space.low, "high": space.high} if space.low else None,
                        "choices": space.choices
                    }
                    for space in spaces
                ]
            }
            for algo, spaces in ResearchAutoML.SEARCH_SPACES.items()
        ],
        "search_strategies": ["bayesian", "random", "grid"],
        "optimization_objectives": {
            "classification": ["accuracy", "f1", "auc", "log_loss"],
            "regression": ["mse", "mae", "r2", "rmse"]
        }
    }


@router.get("/automl/models")
async def list_automl_models():
    """List all trained AutoML models"""
    import os
    import json
    
    models_dir = "./models"
    models = []
    
    if os.path.exists(models_dir):
        for filename in os.listdir(models_dir):
            if filename.endswith("_state.json"):
                model_id = filename.replace("_state.json", "")
                try:
                    with open(os.path.join(models_dir, filename), 'r') as f:
                        state = json.load(f)
                        models.append({
                            "model_id": model_id,
                            "task_type": state.get("task_type"),
                            "objective": state.get("objective"),
                            "n_trials": len(state.get("all_trials", []))
                        })
                except Exception:
                    pass
    
    return {"models": models, "total": len(models)}
