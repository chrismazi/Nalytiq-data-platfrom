"""
Export, Reporting, and Data Transformation API Endpoints
"""
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
import pandas as pd
import os
import io
import logging
from datetime import datetime

from data_processor import UniversalDataProcessor
from report_generator import PDFReportGenerator, DataExporter, create_analysis_report
from data_transformation import DataTransformer, get_transformation_templates

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/export-transform", tags=["Export & Transformation"])

# Global storage
loaded_datasets = {}

# ============= Pydantic Models =============

# Export Models
class ExportDatasetRequest(BaseModel):
    dataset_id: int
    format: str = Field(..., pattern='^(csv|excel|json)$')
    filename: Optional[str] = None

class GenerateReportRequest(BaseModel):
    dataset_id: int
    title: str = "Data Analysis Report"
    include_data: bool = True
    include_statistics: bool = True
    max_rows: int = Field(default=100, ge=10, le=1000)

# Transformation Models
class FilterRowsRequest(BaseModel):
    dataset_id: int
    column: str
    operator: str = Field(..., pattern='^(equals|not_equals|greater_than|less_than|greater_equal|less_equal|contains|not_contains|in|not_in)$')
    value: Any

class SelectColumnsRequest(BaseModel):
    dataset_id: int
    columns: List[str]

class DropColumnsRequest(BaseModel):
    dataset_id: int
    columns: List[str]

class RenameColumnRequest(BaseModel):
    dataset_id: int
    old_name: str
    new_name: str

class CalculatedColumnRequest(BaseModel):
    dataset_id: int
    name: str
    expression: str

class ConvertTypeRequest(BaseModel):
    dataset_id: int
    column: str
    target_type: str = Field(..., pattern='^(int|float|string|datetime|bool)$')

class FillMissingRequest(BaseModel):
    dataset_id: int
    column: str
    method: str = Field(default='mean', pattern='^(mean|median|mode|forward|backward|value)$')
    value: Optional[Any] = None

class GroupByRequest(BaseModel):
    dataset_id: int
    group_columns: List[str]
    agg_dict: Dict[str, str]

class SortValuesRequest(BaseModel):
    dataset_id: int
    columns: List[str]
    ascending: bool = True

class TransformationPipelineRequest(BaseModel):
    dataset_id: int
    transformations: List[Dict[str, Any]]
    save_result: bool = False
    result_name: Optional[str] = None

# ============= Helper Functions =============

def get_dataset_df(dataset_id: int) -> pd.DataFrame:
    """Load dataset from database"""
    if dataset_id in loaded_datasets:
        return loaded_datasets[dataset_id].copy()
    
    from database_enhanced import get_db_connection
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM datasets WHERE id = ?", (dataset_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        file_path = row['file_path']
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Dataset file not found")
        
        processor = UniversalDataProcessor(file_path)
        df = processor.df.copy()
        
        loaded_datasets[dataset_id] = df.copy()
        
        return df

def get_dataset_info(dataset_id: int) -> Dict[str, Any]:
    """Get dataset metadata"""
    from database_enhanced import get_db_connection
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        return dict(row)

# ============= Export Endpoints =============

@router.post("/export-dataset")
async def export_dataset(request: ExportDatasetRequest):
    """Export dataset in specified format"""
    try:
        df = get_dataset_df(request.dataset_id)
        dataset_info = get_dataset_info(request.dataset_id)
        
        filename = request.filename or f"dataset_{request.dataset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if request.format == 'csv':
            content = DataExporter.to_csv(df)
            media_type = 'text/csv'
            filename = f"{filename}.csv"
            
        elif request.format == 'excel':
            content = DataExporter.to_excel(df, sheet_name=dataset_info['name'][:31])
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f"{filename}.xlsx"
            
        elif request.format == 'json':
            content = DataExporter.to_json(df).encode('utf-8')
            media_type = 'application/json'
            filename = f"{filename}.json"
        
        else:
            raise HTTPException(status_code=400, detail="Invalid format")
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-report")
async def generate_report(request: GenerateReportRequest):
    """Generate PDF analysis report"""
    try:
        df = get_dataset_df(request.dataset_id)
        dataset_info = get_dataset_info(request.dataset_id)
        
        # Prepare analysis results
        analysis_results = {
            'dataset_info': {
                'num_rows': len(df),
                'num_columns': len(df.columns),
                'file_size': f"{dataset_info['file_size'] / 1024 / 1024:.2f} MB",
                'upload_date': dataset_info['upload_date']
            }
        }
        
        # Add data preview
        if request.include_data:
            analysis_results['data'] = df.head(request.max_rows).to_dict('records')
        
        # Add statistics
        if request.include_statistics:
            stats_df = df.describe(include='all').transpose()
            analysis_results['statistics'] = stats_df.reset_index().to_dict('records')
        
        # Add insights
        numeric_cols = df.select_dtypes(include=['number']).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        
        insights = [
            f"Dataset contains {len(df):,} rows and {len(df.columns)} columns",
            f"{len(numeric_cols)} numeric columns and {len(categorical_cols)} categorical columns",
            f"Missing values: {df.isnull().sum().sum():,} total ({(df.isnull().sum().sum() / df.size * 100):.2f}%)"
        ]
        
        if len(numeric_cols) > 0:
            insights.append(f"Numeric columns range from {df[numeric_cols].min().min():.2f} to {df[numeric_cols].max().max():.2f}")
        
        analysis_results['insights'] = insights
        
        # Generate PDF
        pdf_bytes = create_analysis_report(
            title=request.title,
            dataset_name=dataset_info['name'],
            analysis_results=analysis_results,
            include_data=request.include_data
        )
        
        filename = f"report_{dataset_info['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= Transformation Endpoints =============

@router.post("/filter-rows")
async def filter_rows(request: FilterRowsRequest):
    """Filter rows based on condition"""
    try:
        df = get_dataset_df(request.dataset_id)
        transformer = DataTransformer(df)
        
        transformer.filter_rows(request.column, request.operator, request.value)
        result = transformer.preview()
        
        return {
            "status": "success",
            "result": result,
            "history": transformer.get_history()
        }
        
    except Exception as e:
        logger.error(f"Filter rows failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/select-columns")
async def select_columns(request: SelectColumnsRequest):
    """Select specific columns"""
    try:
        df = get_dataset_df(request.dataset_id)
        transformer = DataTransformer(df)
        
        transformer.select_columns(request.columns)
        result = transformer.preview()
        
        return {
            "status": "success",
            "result": result,
            "history": transformer.get_history()
        }
        
    except Exception as e:
        logger.error(f"Select columns failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/drop-columns")
async def drop_columns(request: DropColumnsRequest):
    """Drop columns"""
    try:
        df = get_dataset_df(request.dataset_id)
        transformer = DataTransformer(df)
        
        transformer.drop_columns(request.columns)
        result = transformer.preview()
        
        return {
            "status": "success",
            "result": result,
            "history": transformer.get_history()
        }
        
    except Exception as e:
        logger.error(f"Drop columns failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rename-column")
async def rename_column(request: RenameColumnRequest):
    """Rename a column"""
    try:
        df = get_dataset_df(request.dataset_id)
        transformer = DataTransformer(df)
        
        transformer.rename_column(request.old_name, request.new_name)
        result = transformer.preview()
        
        return {
            "status": "success",
            "result": result,
            "history": transformer.get_history()
        }
        
    except Exception as e:
        logger.error(f"Rename column failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-calculated-column")
async def add_calculated_column(request: CalculatedColumnRequest):
    """Add calculated column"""
    try:
        df = get_dataset_df(request.dataset_id)
        transformer = DataTransformer(df)
        
        transformer.add_calculated_column(request.name, request.expression)
        result = transformer.preview()
        
        return {
            "status": "success",
            "result": result,
            "history": transformer.get_history()
        }
        
    except Exception as e:
        logger.error(f"Add calculated column failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/convert-type")
async def convert_type(request: ConvertTypeRequest):
    """Convert column data type"""
    try:
        df = get_dataset_df(request.dataset_id)
        transformer = DataTransformer(df)
        
        transformer.convert_type(request.column, request.target_type)
        result = transformer.preview()
        
        return {
            "status": "success",
            "result": result,
            "history": transformer.get_history()
        }
        
    except Exception as e:
        logger.error(f"Convert type failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fill-missing")
async def fill_missing(request: FillMissingRequest):
    """Fill missing values"""
    try:
        df = get_dataset_df(request.dataset_id)
        transformer = DataTransformer(df)
        
        transformer.fill_missing(request.column, request.method, request.value)
        result = transformer.preview()
        
        return {
            "status": "success",
            "result": result,
            "history": transformer.get_history()
        }
        
    except Exception as e:
        logger.error(f"Fill missing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/drop-duplicates")
async def drop_duplicates(dataset_id: int, columns: Optional[List[str]] = None):
    """Remove duplicate rows"""
    try:
        df = get_dataset_df(dataset_id)
        transformer = DataTransformer(df)
        
        transformer.drop_duplicates(columns)
        result = transformer.preview()
        
        return {
            "status": "success",
            "result": result,
            "history": transformer.get_history()
        }
        
    except Exception as e:
        logger.error(f"Drop duplicates failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/group-by")
async def group_by(request: GroupByRequest):
    """Group by and aggregate"""
    try:
        df = get_dataset_df(request.dataset_id)
        transformer = DataTransformer(df)
        
        transformer.group_by(request.group_columns, request.agg_dict)
        result = transformer.preview()
        
        return {
            "status": "success",
            "result": result,
            "history": transformer.get_history()
        }
        
    except Exception as e:
        logger.error(f"Group by failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sort-values")
async def sort_values(request: SortValuesRequest):
    """Sort by columns"""
    try:
        df = get_dataset_df(request.dataset_id)
        transformer = DataTransformer(df)
        
        transformer.sort_values(request.columns, request.ascending)
        result = transformer.preview()
        
        return {
            "status": "success",
            "result": result,
            "history": transformer.get_history()
        }
        
    except Exception as e:
        logger.error(f"Sort values failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transformation-pipeline")
async def transformation_pipeline(request: TransformationPipelineRequest):
    """Apply multiple transformations in sequence"""
    try:
        df = get_dataset_df(request.dataset_id)
        transformer = DataTransformer(df)
        
        # Apply each transformation
        for step in request.transformations:
            operation = step['operation']
            params = step.get('params', {})
            
            if operation == 'filter_rows':
                transformer.filter_rows(**params)
            elif operation == 'select_columns':
                transformer.select_columns(**params)
            elif operation == 'drop_columns':
                transformer.drop_columns(**params)
            elif operation == 'rename_column':
                transformer.rename_column(**params)
            elif operation == 'convert_type':
                transformer.convert_type(**params)
            elif operation == 'fill_missing':
                transformer.fill_missing(**params)
            elif operation == 'drop_duplicates':
                transformer.drop_duplicates(**params)
            elif operation == 'group_by':
                transformer.group_by(**params)
            elif operation == 'sort_values':
                transformer.sort_values(**params)
            else:
                raise ValueError(f"Unknown operation: {operation}")
        
        result = transformer.preview()
        
        # Save result if requested
        if request.save_result:
            # TODO: Save transformed dataset to database
            pass
        
        return {
            "status": "success",
            "result": result,
            "history": transformer.get_history(),
            "transformations_applied": len(request.transformations)
        }
        
    except Exception as e:
        logger.error(f"Transformation pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transformation-templates")
async def get_templates():
    """Get predefined transformation templates"""
    return {
        "status": "success",
        "templates": get_transformation_templates()
    }

@router.get("/transformation-operations")
async def get_operations():
    """Get available transformation operations"""
    return {
        "status": "success",
        "operations": [
            {"id": "filter_rows", "name": "Filter Rows", "category": "filtering"},
            {"id": "select_columns", "name": "Select Columns", "category": "columns"},
            {"id": "drop_columns", "name": "Drop Columns", "category": "columns"},
            {"id": "rename_column", "name": "Rename Column", "category": "columns"},
            {"id": "add_calculated_column", "name": "Add Calculated Column", "category": "columns"},
            {"id": "convert_type", "name": "Convert Type", "category": "data_types"},
            {"id": "fill_missing", "name": "Fill Missing Values", "category": "missing_data"},
            {"id": "drop_duplicates", "name": "Drop Duplicates", "category": "cleaning"},
            {"id": "group_by", "name": "Group By", "category": "aggregation"},
            {"id": "sort_values", "name": "Sort Values", "category": "sorting"}
        ]
    }
