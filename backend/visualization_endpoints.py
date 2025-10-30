"""
Visualization API Endpoints
Interactive chart generation with Plotly
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import pandas as pd
import os
import logging

from data_processor import UniversalDataProcessor
from visualization_engine import PlotlyVisualizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/viz", tags=["Visualizations"])

# Global storage for loaded datasets
loaded_datasets = {}

# Pydantic models

class BarChartRequest(BaseModel):
    dataset_id: int
    x_col: str
    y_col: str
    title: Optional[str] = None
    orientation: str = Field(default='v', pattern='^(v|h)$')
    color_col: Optional[str] = None

class LineChartRequest(BaseModel):
    dataset_id: int
    x_col: str
    y_cols: List[str]
    title: Optional[str] = None

class ScatterPlotRequest(BaseModel):
    dataset_id: int
    x_col: str
    y_col: str
    title: Optional[str] = None
    color_col: Optional[str] = None
    size_col: Optional[str] = None
    trendline: Optional[str] = None

class HistogramRequest(BaseModel):
    dataset_id: int
    col: str
    title: Optional[str] = None
    bins: int = Field(default=30, ge=10, le=100)

class BoxPlotRequest(BaseModel):
    dataset_id: int
    y_col: str
    x_col: Optional[str] = None
    title: Optional[str] = None

class PieChartRequest(BaseModel):
    dataset_id: int
    values_col: str
    names_col: str
    title: Optional[str] = None

class HeatmapRequest(BaseModel):
    dataset_id: int
    columns: Optional[List[str]] = None
    title: Optional[str] = None

class GroupedBarRequest(BaseModel):
    dataset_id: int
    x_col: str
    y_cols: List[str]
    title: Optional[str] = None

class AreaChartRequest(BaseModel):
    dataset_id: int
    x_col: str
    y_cols: List[str]
    title: Optional[str] = None
    stacked: bool = False

class ViolinPlotRequest(BaseModel):
    dataset_id: int
    y_col: str
    x_col: Optional[str] = None
    title: Optional[str] = None

class Scatter3DRequest(BaseModel):
    dataset_id: int
    x_col: str
    y_col: str
    z_col: str
    title: Optional[str] = None
    color_col: Optional[str] = None

# Helper function
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

# Endpoints

@router.post("/bar-chart")
async def create_bar_chart(request: BarChartRequest):
    """Create interactive bar chart"""
    try:
        df = get_dataset_df(request.dataset_id)
        viz = PlotlyVisualizer(df)
        
        result = viz.create_bar_chart(
            x_col=request.x_col,
            y_col=request.y_col,
            title=request.title,
            orientation=request.orientation,
            color_col=request.color_col
        )
        
        return {"status": "success", "chart": result}
        
    except Exception as e:
        logger.error(f"Bar chart creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/line-chart")
async def create_line_chart(request: LineChartRequest):
    """Create interactive line chart"""
    try:
        df = get_dataset_df(request.dataset_id)
        viz = PlotlyVisualizer(df)
        
        result = viz.create_line_chart(
            x_col=request.x_col,
            y_cols=request.y_cols,
            title=request.title
        )
        
        return {"status": "success", "chart": result}
        
    except Exception as e:
        logger.error(f"Line chart creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scatter-plot")
async def create_scatter_plot(request: ScatterPlotRequest):
    """Create interactive scatter plot"""
    try:
        df = get_dataset_df(request.dataset_id)
        viz = PlotlyVisualizer(df)
        
        result = viz.create_scatter_plot(
            x_col=request.x_col,
            y_col=request.y_col,
            title=request.title,
            color_col=request.color_col,
            size_col=request.size_col,
            trendline=request.trendline
        )
        
        return {"status": "success", "chart": result}
        
    except Exception as e:
        logger.error(f"Scatter plot creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/histogram")
async def create_histogram(request: HistogramRequest):
    """Create histogram"""
    try:
        df = get_dataset_df(request.dataset_id)
        viz = PlotlyVisualizer(df)
        
        result = viz.create_histogram(
            col=request.col,
            title=request.title,
            bins=request.bins
        )
        
        return {"status": "success", "chart": result}
        
    except Exception as e:
        logger.error(f"Histogram creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/box-plot")
async def create_box_plot(request: BoxPlotRequest):
    """Create box plot"""
    try:
        df = get_dataset_df(request.dataset_id)
        viz = PlotlyVisualizer(df)
        
        result = viz.create_box_plot(
            y_col=request.y_col,
            x_col=request.x_col,
            title=request.title
        )
        
        return {"status": "success", "chart": result}
        
    except Exception as e:
        logger.error(f"Box plot creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pie-chart")
async def create_pie_chart(request: PieChartRequest):
    """Create pie chart"""
    try:
        df = get_dataset_df(request.dataset_id)
        viz = PlotlyVisualizer(df)
        
        result = viz.create_pie_chart(
            values_col=request.values_col,
            names_col=request.names_col,
            title=request.title
        )
        
        return {"status": "success", "chart": result}
        
    except Exception as e:
        logger.error(f"Pie chart creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/heatmap")
async def create_heatmap(request: HeatmapRequest):
    """Create correlation heatmap"""
    try:
        df = get_dataset_df(request.dataset_id)
        viz = PlotlyVisualizer(df)
        
        result = viz.create_heatmap(
            columns=request.columns,
            title=request.title
        )
        
        return {"status": "success", "chart": result}
        
    except Exception as e:
        logger.error(f"Heatmap creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/grouped-bar")
async def create_grouped_bar(request: GroupedBarRequest):
    """Create grouped bar chart"""
    try:
        df = get_dataset_df(request.dataset_id)
        viz = PlotlyVisualizer(df)
        
        result = viz.create_grouped_bar(
            x_col=request.x_col,
            y_cols=request.y_cols,
            title=request.title
        )
        
        return {"status": "success", "chart": result}
        
    except Exception as e:
        logger.error(f"Grouped bar creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/area-chart")
async def create_area_chart(request: AreaChartRequest):
    """Create area chart"""
    try:
        df = get_dataset_df(request.dataset_id)
        viz = PlotlyVisualizer(df)
        
        result = viz.create_area_chart(
            x_col=request.x_col,
            y_cols=request.y_cols,
            title=request.title,
            stacked=request.stacked
        )
        
        return {"status": "success", "chart": result}
        
    except Exception as e:
        logger.error(f"Area chart creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/violin-plot")
async def create_violin_plot(request: ViolinPlotRequest):
    """Create violin plot"""
    try:
        df = get_dataset_df(request.dataset_id)
        viz = PlotlyVisualizer(df)
        
        result = viz.create_violin_plot(
            y_col=request.y_col,
            x_col=request.x_col,
            title=request.title
        )
        
        return {"status": "success", "chart": result}
        
    except Exception as e:
        logger.error(f"Violin plot creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/3d-scatter")
async def create_3d_scatter(request: Scatter3DRequest):
    """Create 3D scatter plot"""
    try:
        df = get_dataset_df(request.dataset_id)
        viz = PlotlyVisualizer(df)
        
        result = viz.create_3d_scatter(
            x_col=request.x_col,
            y_col=request.y_col,
            z_col=request.z_col,
            title=request.title,
            color_col=request.color_col
        )
        
        return {"status": "success", "chart": result}
        
    except Exception as e:
        logger.error(f"3D scatter creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chart-types")
async def get_chart_types():
    """Get list of available chart types"""
    return {
        "status": "success",
        "chart_types": PlotlyVisualizer.get_chart_types()
    }

@router.get("/dataset-columns/{dataset_id}")
async def get_dataset_columns(dataset_id: int):
    """Get columns of a dataset for chart configuration"""
    try:
        df = get_dataset_df(dataset_id)
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        
        return {
            "status": "success",
            "columns": {
                "all": df.columns.tolist(),
                "numeric": numeric_cols,
                "categorical": categorical_cols,
                "datetime": datetime_cols
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get columns: {e}")
        raise HTTPException(status_code=500, detail=str(e))
