"""
Advanced Machine Learning API Endpoints
- XGBoost training
- Neural Network training
- Model comparison
- Hyperparameter tuning
- Feature engineering suggestions
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import pandas as pd
import os
import tempfile
import logging
from datetime import datetime

from data_processor import UniversalDataProcessor
from ml_advanced import AdvancedMLPipeline
from database_enhanced import get_db_connection, AnalysisHistoryRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml", tags=["Advanced ML"])

# Global storage for loaded datasets (in production, use Redis or database)
loaded_datasets = {}

# Pydantic models

class TrainXGBoostRequest(BaseModel):
    dataset_id: int
    target: str
    features: Optional[List[str]] = None
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)
    n_estimators: int = Field(default=100, ge=10, le=500)
    max_depth: int = Field(default=6, ge=1, le=20)
    learning_rate: float = Field(default=0.1, ge=0.01, le=1.0)
    tune_hyperparameters: bool = False
    save_model: bool = True

class TrainNeuralNetworkRequest(BaseModel):
    dataset_id: int
    target: str
    features: Optional[List[str]] = None
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)
    hidden_layers: List[int] = Field(default=[64, 32])
    dropout_rate: float = Field(default=0.2, ge=0.0, le=0.5)
    epochs: int = Field(default=50, ge=10, le=200)
    batch_size: int = Field(default=32, ge=8, le=256)
    save_model: bool = True

class CompareModelsRequest(BaseModel):
    dataset_id: int
    target: str
    features: Optional[List[str]] = None
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)
    algorithms: List[str] = Field(
        default=["xgboost", "neural_network"],
        description="Algorithms to compare: xgboost, neural_network"
    )
    xgboost_params: Optional[Dict[str, Any]] = None
    nn_params: Optional[Dict[str, Any]] = None

class FeatureEngineeringRequest(BaseModel):
    dataset_id: int
    target: str

# Helper function to load dataset
def get_dataset_df(dataset_id: int) -> pd.DataFrame:
    """Load dataset from database"""
    # Check cache first
    if dataset_id in loaded_datasets:
        return loaded_datasets[dataset_id].copy()
    
    # Load from database
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT file_path FROM datasets WHERE id = ?
        """, (dataset_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        file_path = row['file_path']
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Dataset file not found")
        
        # Read dataset
        processor = UniversalDataProcessor(file_path)
        df = processor.df.copy()
        
        # Cache it
        loaded_datasets[dataset_id] = df.copy()
        
        return df

# Endpoints

@router.post("/train-xgboost")
async def train_xgboost(request: TrainXGBoostRequest, background_tasks: BackgroundTasks):
    """Train XGBoost model (Classification or Regression)"""
    try:
        logger.info(f"Training XGBoost model for dataset {request.dataset_id}")
        start_time = datetime.now()
        
        # Load dataset
        df = get_dataset_df(request.dataset_id)
        
        # Initialize ML pipeline
        pipeline = AdvancedMLPipeline(df)
        
        # Prepare data
        X_train, X_test, y_train, y_test = pipeline.prepare_data(
            target=request.target,
            features=request.features,
            test_size=request.test_size,
            scale_features=True
        )
        
        # Train XGBoost
        result = pipeline.train_xgboost(
            X_train, X_test, y_train, y_test,
            n_estimators=request.n_estimators,
            max_depth=request.max_depth,
            learning_rate=request.learning_rate,
            tune_hyperparameters=request.tune_hyperparameters
        )
        
        # Save model if requested
        if request.save_model:
            model_dir = "models"
            os.makedirs(model_dir, exist_ok=True)
            model_name = f"xgboost_{request.dataset_id}_{int(datetime.now().timestamp())}"
            pipeline.save_model(model_name, "XGBoost", model_dir)
            result['model_path'] = f"{model_dir}/{model_name}"
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        result['execution_time_ms'] = int(execution_time)
        
        # Save to history in background
        background_tasks.add_task(
            save_ml_to_history,
            request.dataset_id,
            "xgboost",
            "XGBoost Model Training",
            request.dict(),
            result,
            execution_time
        )
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"XGBoost training failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train-neural-network")
async def train_neural_network(request: TrainNeuralNetworkRequest, background_tasks: BackgroundTasks):
    """Train Neural Network model (Classification or Regression)"""
    try:
        logger.info(f"Training Neural Network for dataset {request.dataset_id}")
        start_time = datetime.now()
        
        # Load dataset
        df = get_dataset_df(request.dataset_id)
        
        # Initialize ML pipeline
        pipeline = AdvancedMLPipeline(df)
        
        # Prepare data
        X_train, X_test, y_train, y_test = pipeline.prepare_data(
            target=request.target,
            features=request.features,
            test_size=request.test_size,
            scale_features=True
        )
        
        # Train Neural Network
        result = pipeline.train_neural_network(
            X_train, X_test, y_train, y_test,
            hidden_layers=request.hidden_layers,
            dropout_rate=request.dropout_rate,
            epochs=request.epochs,
            batch_size=request.batch_size
        )
        
        # Save model if requested
        if request.save_model:
            model_dir = "models"
            os.makedirs(model_dir, exist_ok=True)
            model_name = f"nn_{request.dataset_id}_{int(datetime.now().timestamp())}"
            pipeline.save_model(model_name, "Neural Network", model_dir)
            result['model_path'] = f"{model_dir}/{model_name}"
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        result['execution_time_ms'] = int(execution_time)
        
        # Save to history in background
        background_tasks.add_task(
            save_ml_to_history,
            request.dataset_id,
            "neural_network",
            "Neural Network Model Training",
            request.dict(),
            result,
            execution_time
        )
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Neural Network training failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare-models")
async def compare_models(request: CompareModelsRequest, background_tasks: BackgroundTasks):
    """Train and compare multiple ML algorithms"""
    try:
        logger.info(f"Comparing models for dataset {request.dataset_id}")
        start_time = datetime.now()
        
        # Load dataset
        df = get_dataset_df(request.dataset_id)
        
        # Initialize ML pipeline
        pipeline = AdvancedMLPipeline(df)
        
        # Prepare data
        X_train, X_test, y_train, y_test = pipeline.prepare_data(
            target=request.target,
            features=request.features,
            test_size=request.test_size,
            scale_features=True
        )
        
        results = []
        
        # Train XGBoost if requested
        if "xgboost" in request.algorithms:
            xgb_params = request.xgboost_params or {}
            xgb_result = pipeline.train_xgboost(
                X_train, X_test, y_train, y_test,
                n_estimators=xgb_params.get('n_estimators', 100),
                max_depth=xgb_params.get('max_depth', 6),
                learning_rate=xgb_params.get('learning_rate', 0.1),
                tune_hyperparameters=xgb_params.get('tune_hyperparameters', False)
            )
            results.append(xgb_result)
        
        # Train Neural Network if requested
        if "neural_network" in request.algorithms:
            nn_params = request.nn_params or {}
            nn_result = pipeline.train_neural_network(
                X_train, X_test, y_train, y_test,
                hidden_layers=nn_params.get('hidden_layers', [64, 32]),
                dropout_rate=nn_params.get('dropout_rate', 0.2),
                epochs=nn_params.get('epochs', 50),
                batch_size=nn_params.get('batch_size', 32)
            )
            results.append(nn_result)
        
        # Compare models
        comparison = pipeline.compare_models(results)
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        response = {
            "comparison": comparison,
            "models": results,
            "execution_time_ms": int(execution_time),
            "problem_type": pipeline.problem_type,
            "n_features": len(pipeline.feature_names),
            "feature_names": pipeline.feature_names
        }
        
        # Save to history in background
        background_tasks.add_task(
            save_ml_to_history,
            request.dataset_id,
            "model_comparison",
            f"Model Comparison: {' vs '.join(request.algorithms)}",
            request.dict(),
            response,
            execution_time
        )
        
        return {
            "status": "success",
            "result": response
        }
        
    except Exception as e:
        logger.error(f"Model comparison failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feature-suggestions")
async def get_feature_suggestions(request: FeatureEngineeringRequest):
    """Get feature engineering suggestions"""
    try:
        logger.info(f"Getting feature suggestions for dataset {request.dataset_id}")
        
        # Load dataset
        df = get_dataset_df(request.dataset_id)
        
        # Initialize ML pipeline
        pipeline = AdvancedMLPipeline(df)
        
        # Get features (exclude target)
        features = [col for col in df.columns if col != request.target]
        X = df[features]
        
        # Get suggestions
        suggestions = pipeline.suggest_features(X)
        
        return {
            "status": "success",
            "suggestions": suggestions,
            "target": request.target,
            "n_features": len(features)
        }
        
    except Exception as e:
        logger.error(f"Feature suggestions failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/list")
async def list_saved_models(dataset_id: Optional[int] = Query(None)):
    """List saved ML models"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if dataset_id:
                cursor.execute("""
                    SELECT * FROM ml_models 
                    WHERE dataset_id = ?
                    ORDER BY created_at DESC
                """, (dataset_id,))
            else:
                cursor.execute("""
                    SELECT * FROM ml_models 
                    ORDER BY created_at DESC
                    LIMIT 50
                """)
            
            models = [dict(row) for row in cursor.fetchall()]
        
        return {
            "status": "success",
            "count": len(models),
            "models": models
        }
        
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/models/{model_id}")
async def delete_model(model_id: int):
    """Delete a saved model"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get model info
            cursor.execute("SELECT * FROM ml_models WHERE id = ?", (model_id,))
            model = cursor.fetchone()
            
            if not model:
                raise HTTPException(status_code=404, detail="Model not found")
            
            # Delete model files
            if model['model_path'] and os.path.exists(model['model_path']):
                os.remove(model['model_path'])
            
            # Delete from database
            cursor.execute("DELETE FROM ml_models WHERE id = ?", (model_id,))
        
        return {
            "status": "success",
            "message": "Model deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/algorithms")
async def get_supported_algorithms():
    """Get list of supported ML algorithms"""
    return {
        "status": "success",
        "algorithms": [
            {
                "id": "xgboost",
                "name": "XGBoost",
                "type": "Gradient Boosting",
                "supports": ["classification", "regression"],
                "parameters": {
                    "n_estimators": {"type": "int", "default": 100, "min": 10, "max": 500},
                    "max_depth": {"type": "int", "default": 6, "min": 1, "max": 20},
                    "learning_rate": {"type": "float", "default": 0.1, "min": 0.01, "max": 1.0}
                }
            },
            {
                "id": "neural_network",
                "name": "Neural Network",
                "type": "Deep Learning",
                "supports": ["classification", "regression"],
                "parameters": {
                    "hidden_layers": {"type": "list[int]", "default": [64, 32]},
                    "dropout_rate": {"type": "float", "default": 0.2, "min": 0.0, "max": 0.5},
                    "epochs": {"type": "int", "default": 50, "min": 10, "max": 200},
                    "batch_size": {"type": "int", "default": 32, "min": 8, "max": 256}
                }
            }
        ]
    }

# Helper function
def save_ml_to_history(dataset_id: int, analysis_type: str, title: str, 
                       parameters: dict, results: dict, execution_time: float):
    """Save ML training to analysis history"""
    try:
        AnalysisHistoryRepository.save_analysis(
            dataset_id=dataset_id,
            user_id=1,  # Default user
            analysis_type=analysis_type,
            title=title,
            parameters=parameters,
            results=results,
            is_saved=True,
            execution_time_ms=int(execution_time)
        )
        logger.info(f"Saved {analysis_type} to history")
    except Exception as e:
        logger.error(f"Failed to save to history: {e}")
