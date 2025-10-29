"""
Enhanced API endpoints with universal dataset support
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Body
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import tempfile
import os
import pandas as pd
import io
import logging

from data_processor import UniversalDataProcessor
from eda_engine import EDAEngine
from ml_pipeline import MLPipeline
from advanced_analysis import AdvancedAnalyzer
from database import DatasetRepository, AnalysisRepository, QualityReportRepository
from validators import FileValidator, DataValidator
from exceptions import FileValidationError, DataProcessingError, create_error_response
from data_analysis import DataAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory cache for uploaded datasets (temporary solution)
DATASET_CACHE = {}

# Pydantic models for request validation
class GroupedStatsRequest(BaseModel):
    dataset_id: Optional[int] = None
    group_by: str
    value_col: str
    aggregation: str = "mean"

class CrosstabRequest(BaseModel):
    dataset_id: Optional[int] = None
    row_col: str
    col_col: str
    value_col: Optional[str] = None
    aggfunc: str = "count"
    normalize: bool = False

class MLModelRequest(BaseModel):
    dataset_id: Optional[int] = None
    target: str
    features: Optional[List[str]] = None
    test_size: float = 0.2
    n_estimators: int = 100
    max_depth: Optional[int] = None

class TopNRequest(BaseModel):
    dataset_id: Optional[int] = None
    group_col: str
    value_col: str
    n: int = 10
    ascending: bool = False

class ComparisonRequest(BaseModel):
    dataset_id: Optional[int] = None
    category_col: str
    value_col: str
    categories: Optional[List[str]] = None

@router.post("/upload-enhanced/", tags=["Data Processing"])
async def upload_enhanced(
    file: UploadFile = File(...),
    name: str = Form(None),
    description: str = Form(None),
    auto_clean: bool = Form(True)
):
    """
    Enhanced upload with automatic cleaning and profiling
    """
    logger.info(f"Enhanced upload request: {file.filename}")
    tmp_path = None
    
    try:
        # Validate file
        await FileValidator.validate_upload(file)
        file_info = FileValidator.get_file_info(file)
        logger.info(f"File validation passed: {file_info}")
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(file.filename or "data.csv")[-1]
        ) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Read file using DataAnalyzer
        analyzer = DataAnalyzer()
        result = analyzer.read_file(tmp_path)
        
        if "error" in result:
            raise DataProcessingError(result["error"])
        
        df = analyzer.df
        
        # Apply universal data processor
        processor = UniversalDataProcessor(df)
        
        if auto_clean:
            # Auto-detect types
            type_changes = processor.auto_detect_types()
            
            # Standardize column names
            name_mapping = processor.standardize_column_names()
            
            # Handle missing values
            missing_report = processor.handle_missing_values()
            
            # Remove duplicates
            duplicates_removed = processor.remove_duplicates()
            
            logger.info(f"Cleaning complete: {duplicates_removed} duplicates removed")
        
        # Generate comprehensive profile
        profile = processor.generate_profile()
        
        # Run EDA
        eda_engine = EDAEngine(processor.df)
        descriptive_stats = eda_engine.descriptive_statistics()
        correlations = eda_engine.correlation_analysis()
        distributions = eda_engine.distribution_analysis()
        quality_score = eda_engine.data_quality_score()
        insights = eda_engine.generate_insights()
        
        # Save to database
        dataset_id = DatasetRepository.create_dataset(
            name=name or file.filename,
            filename=file.filename,
            file_path=tmp_path,
            file_size=file_info['size_bytes'],
            file_type=file_info['extension'],
            num_rows=len(processor.df),
            num_columns=len(processor.df.columns),
            columns=processor.df.columns.tolist(),
            dtypes={col: str(dtype) for col, dtype in processor.df.dtypes.items()},
            description=description
        )
        
        # Cache the dataframe for later use
        DATASET_CACHE[dataset_id] = processor.df
        
        # Save quality report
        QualityReportRepository.save_report(
            dataset_id=dataset_id,
            missing_values=profile['basic_info']['total_missing'],
            duplicate_rows=profile['basic_info']['duplicates'],
            outliers_detected=len(profile.get('warnings', [])),
            warnings=profile.get('warnings', []),
            insights=insights
        )
        
        # Build response
        response = {
            'dataset_id': dataset_id,
            'file_info': file_info,
            'basic_info': profile['basic_info'],
            'columns': profile['columns'],
            'sample_data': processor.get_sample_data(10),
            'descriptive_stats': descriptive_stats,
            'correlations': correlations,
            'distributions': distributions,
            'quality_score': quality_score,
            'insights': insights,
            'warnings': profile.get('warnings', []),
            'cleaning_summary': processor.get_cleaning_summary() if auto_clean else None
        }
        
        logger.info(f"Upload successful: dataset_id={dataset_id}")
        return JSONResponse(content=response)
        
    except FileValidationError as e:
        logger.warning(f"File validation failed: {str(e)}")
        return create_error_response(str(e), "FILE_VALIDATION_ERROR", 400)
    
    except DataProcessingError as e:
        logger.error(f"Data processing failed: {str(e)}")
        return create_error_response(str(e), "DATA_PROCESSING_ERROR", 400)
    
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return create_error_response(
            "Failed to process file. Please check the file format and try again.",
            "PROCESSING_ERROR",
            500
        )
    
    finally:
        # Note: Don't delete temp file yet, we need it for analysis
        pass

@router.post("/analyze/grouped-stats/", tags=["Advanced Analysis"])
async def analyze_grouped_stats(request: GroupedStatsRequest):
    """
    Compute grouped statistics
    """
    try:
        dataset_id = request.dataset_id
        if not dataset_id or dataset_id not in DATASET_CACHE:
            raise HTTPException(status_code=404, detail="Dataset not found. Please upload first.")
        
        df = DATASET_CACHE[dataset_id]
        analyzer = AdvancedAnalyzer(df)
        
        result = analyzer.grouped_statistics(
            group_by=request.group_by,
            value_col=request.value_col,
            aggregation=request.aggregation
        )
        
        # Save analysis result
        AnalysisRepository.save_analysis(
            dataset_id=dataset_id,
            analysis_type='grouped_stats',
            results=result,
            parameters=request.dict()
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.exception(f"Grouped stats failed: {str(e)}")
        return create_error_response(str(e), "ANALYSIS_ERROR", 400)

@router.post("/analyze/crosstab/", tags=["Advanced Analysis"])
async def analyze_crosstab(request: CrosstabRequest):
    """
    Generate crosstabulation / pivot table
    """
    try:
        dataset_id = request.dataset_id
        if not dataset_id or dataset_id not in DATASET_CACHE:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        df = DATASET_CACHE[dataset_id]
        analyzer = AdvancedAnalyzer(df)
        
        result = analyzer.crosstab_analysis(
            row_col=request.row_col,
            col_col=request.col_col,
            value_col=request.value_col,
            aggfunc=request.aggfunc,
            normalize=request.normalize
        )
        
        AnalysisRepository.save_analysis(
            dataset_id=dataset_id,
            analysis_type='crosstab',
            results=result,
            parameters=request.dict()
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.exception(f"Crosstab failed: {str(e)}")
        return create_error_response(str(e), "ANALYSIS_ERROR", 400)

@router.post("/ml/train/", tags=["Machine Learning"])
async def train_ml_model(request: MLModelRequest):
    """
    Train machine learning model
    """
    try:
        dataset_id = request.dataset_id
        if not dataset_id or dataset_id not in DATASET_CACHE:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        df = DATASET_CACHE[dataset_id]
        pipeline = MLPipeline(df)
        
        results = pipeline.train_model(
            target=request.target,
            features=request.features,
            test_size=request.test_size,
            n_estimators=request.n_estimators,
            max_depth=request.max_depth
        )
        
        # Save model and results
        AnalysisRepository.save_analysis(
            dataset_id=dataset_id,
            analysis_type='ml_model',
            results=results,
            parameters=request.dict()
        )
        
        return JSONResponse(content=results)
        
    except Exception as e:
        logger.exception(f"ML training failed: {str(e)}")
        return create_error_response(str(e), "ML_ERROR", 400)

@router.post("/analyze/top-n/", tags=["Advanced Analysis"])
async def analyze_top_n(request: TopNRequest):
    """
    Get top N records
    """
    try:
        dataset_id = request.dataset_id
        if not dataset_id or dataset_id not in DATASET_CACHE:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        df = DATASET_CACHE[dataset_id]
        analyzer = AdvancedAnalyzer(df)
        
        result = analyzer.top_n_analysis(
            group_col=request.group_col,
            value_col=request.value_col,
            n=request.n,
            ascending=request.ascending
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.exception(f"Top N analysis failed: {str(e)}")
        return create_error_response(str(e), "ANALYSIS_ERROR", 400)

@router.post("/analyze/comparison/", tags=["Advanced Analysis"])
async def analyze_comparison(request: ComparisonRequest):
    """
    Compare values across categories
    """
    try:
        dataset_id = request.dataset_id
        if not dataset_id or dataset_id not in DATASET_CACHE:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        df = DATASET_CACHE[dataset_id]
        analyzer = AdvancedAnalyzer(df)
        
        result = analyzer.comparison_analysis(
            category_col=request.category_col,
            value_col=request.value_col,
            categories=request.categories
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.exception(f"Comparison analysis failed: {str(e)}")
        return create_error_response(str(e), "ANALYSIS_ERROR", 400)

@router.get("/datasets/", tags=["Data Management"])
async def list_datasets(limit: int = 100):
    """
    List all uploaded datasets
    """
    try:
        datasets = DatasetRepository.get_all_datasets(limit=limit)
        return JSONResponse(content={'datasets': datasets, 'count': len(datasets)})
    except Exception as e:
        logger.exception(f"Failed to list datasets: {str(e)}")
        return create_error_response(str(e), "DATABASE_ERROR", 500)

@router.get("/datasets/{dataset_id}/", tags=["Data Management"])
async def get_dataset(dataset_id: int):
    """
    Get dataset information
    """
    try:
        dataset = DatasetRepository.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        DatasetRepository.update_last_accessed(dataset_id)
        return JSONResponse(content=dataset)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get dataset: {str(e)}")
        return create_error_response(str(e), "DATABASE_ERROR", 500)

@router.get("/datasets/{dataset_id}/download/", tags=["Data Management"])
async def download_dataset(dataset_id: int, format: str = "csv"):
    """
    Download cleaned dataset
    """
    try:
        if dataset_id not in DATASET_CACHE:
            raise HTTPException(status_code=404, detail="Dataset not in cache")
        
        df = DATASET_CACHE[dataset_id]
        processor = UniversalDataProcessor(df)
        
        data = processor.export_cleaned_data(format=format)
        
        if format == "csv":
            media_type = "text/csv"
            filename = f"dataset_{dataset_id}.csv"
        elif format == "excel":
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"dataset_{dataset_id}.xlsx"
        elif format == "json":
            media_type = "application/json"
            filename = f"dataset_{dataset_id}.json"
        else:
            raise HTTPException(status_code=400, detail="Invalid format")
        
        return StreamingResponse(
            io.BytesIO(data),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.exception(f"Download failed: {str(e)}")
        return create_error_response(str(e), "DOWNLOAD_ERROR", 500)
