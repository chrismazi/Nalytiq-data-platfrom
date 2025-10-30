"""
Analysis History & Persistence API Endpoints
- Save analysis results
- View analysis history
- Re-run saved configurations
- Compare results over time
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
import logging

from database_enhanced import (
    AnalysisHistoryRepository, 
    SavedConfigRepository,
    get_db_connection
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/history", tags=["Analysis History"])

# Pydantic models

class SaveAnalysisRequest(BaseModel):
    dataset_id: int
    user_id: int = 1  # Default user for now
    analysis_type: str
    title: str
    description: Optional[str] = None
    parameters: Dict[str, Any]
    results: Dict[str, Any]
    visualization_data: Optional[Dict[str, Any]] = None
    is_saved: bool = True
    execution_time_ms: Optional[int] = None

class SaveConfigRequest(BaseModel):
    user_id: int = 1
    name: str
    description: Optional[str] = None
    analysis_type: str
    parameters: Dict[str, Any]

class ComparisonRequest(BaseModel):
    analysis_ids: List[int]
    comparison_name: Optional[str] = None

# Endpoints

@router.post("/save")
async def save_analysis(request: SaveAnalysisRequest):
    """Save an analysis result to history"""
    try:
        analysis_id = AnalysisHistoryRepository.save_analysis(
            dataset_id=request.dataset_id,
            user_id=request.user_id,
            analysis_type=request.analysis_type,
            title=request.title,
            parameters=request.parameters,
            results=request.results,
            visualization_data=request.visualization_data,
            is_saved=request.is_saved,
            execution_time_ms=request.execution_time_ms
        )
        
        logger.info(f"Analysis saved: {analysis_id}")
        
        return {
            "status": "success",
            "analysis_id": analysis_id,
            "message": "Analysis saved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to save analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def get_analysis_history(
    dataset_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    analysis_type: Optional[str] = Query(None),
    is_saved: Optional[bool] = Query(None),
    limit: int = Query(50, le=200)
):
    """Get analysis history with optional filters"""
    try:
        # Get analyses from repository
        analyses = AnalysisHistoryRepository.get_analysis_history(
            dataset_id=dataset_id,
            user_id=user_id,
            limit=limit
        )
        
        # Apply additional filters
        if analysis_type:
            analyses = [a for a in analyses if a['analysis_type'] == analysis_type]
        
        if is_saved is not None:
            analyses = [a for a in analyses if a['is_saved'] == is_saved]
        
        # Parse JSON fields
        for analysis in analyses:
            if analysis.get('parameters'):
                analysis['parameters'] = json.loads(analysis['parameters'])
            if analysis.get('results'):
                analysis['results'] = json.loads(analysis['results'])
            if analysis.get('visualization_data'):
                analysis['visualization_data'] = json.loads(analysis['visualization_data'])
        
        return {
            "status": "success",
            "count": len(analyses),
            "analyses": analyses
        }
        
    except Exception as e:
        logger.error(f"Failed to get analysis history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{analysis_id}")
async def get_analysis_detail(analysis_id: int):
    """Get specific analysis by ID"""
    try:
        analysis = AnalysisHistoryRepository.get_analysis(analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Parse JSON fields
        if analysis.get('parameters'):
            analysis['parameters'] = json.loads(analysis['parameters'])
        if analysis.get('results'):
            analysis['results'] = json.loads(analysis['results'])
        if analysis.get('visualization_data'):
            analysis['visualization_data'] = json.loads(analysis['visualization_data'])
        
        return {
            "status": "success",
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{analysis_id}/favorite")
async def toggle_favorite(analysis_id: int, user_id: int = Query(1)):
    """Toggle favorite status of an analysis"""
    try:
        success = AnalysisHistoryRepository.toggle_favorite(analysis_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            "status": "success",
            "message": "Favorite status toggled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle favorite: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{analysis_id}")
async def delete_analysis(analysis_id: int, user_id: int = Query(1)):
    """Delete an analysis"""
    try:
        success = AnalysisHistoryRepository.delete_analysis(analysis_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            "status": "success",
            "message": "Analysis deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare")
async def compare_analyses(request: ComparisonRequest):
    """Compare multiple analyses"""
    try:
        if len(request.analysis_ids) < 2:
            raise HTTPException(
                status_code=400, 
                detail="At least 2 analyses required for comparison"
            )
        
        # Get all analyses
        analyses = []
        for aid in request.analysis_ids:
            analysis = AnalysisHistoryRepository.get_analysis(aid)
            if not analysis:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Analysis {aid} not found"
                )
            
            # Parse JSON fields
            if analysis.get('parameters'):
                analysis['parameters'] = json.loads(analysis['parameters'])
            if analysis.get('results'):
                analysis['results'] = json.loads(analysis['results'])
            
            analyses.append(analysis)
        
        # Build comparison data
        comparison = {
            "comparison_name": request.comparison_name or f"Comparison {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "created_at": datetime.now().isoformat(),
            "n_analyses": len(analyses),
            "analyses": []
        }
        
        # Extract key metrics for comparison
        for analysis in analyses:
            comparison_item = {
                "id": analysis['id'],
                "title": analysis['title'],
                "analysis_type": analysis['analysis_type'],
                "created_at": analysis['created_at'],
                "execution_time_ms": analysis.get('execution_time_ms'),
                "parameters": analysis.get('parameters', {}),
                "key_metrics": {}
            }
            
            # Extract key metrics from results
            results = analysis.get('results', {})
            if isinstance(results, dict):
                # Look for common metric patterns
                for key in ['accuracy', 'r2', 'r2_score', 'rmse', 'mae', 'f1_score', 
                           'precision', 'recall', 'test_accuracy', 'test_r2']:
                    if key in results:
                        comparison_item['key_metrics'][key] = results[key]
                
                # Look nested in 'metrics' key
                if 'metrics' in results:
                    comparison_item['key_metrics'].update(results['metrics'])
            
            comparison['analyses'].append(comparison_item)
        
        # Add comparison insights
        comparison['insights'] = _generate_comparison_insights(comparison['analyses'])
        
        return {
            "status": "success",
            "comparison": comparison
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare analyses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config/save")
async def save_analysis_config(request: SaveConfigRequest):
    """Save analysis configuration as template"""
    try:
        config_id = SavedConfigRepository.save_config(
            user_id=request.user_id,
            name=request.name,
            analysis_type=request.analysis_type,
            parameters=request.parameters,
            description=request.description
        )
        
        return {
            "status": "success",
            "config_id": config_id,
            "message": "Configuration saved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/list")
async def get_saved_configs(
    user_id: int = Query(1),
    analysis_type: Optional[str] = Query(None)
):
    """Get saved analysis configurations"""
    try:
        configs = SavedConfigRepository.get_configs(user_id, analysis_type)
        
        # Parse parameters JSON
        for config in configs:
            if config.get('parameters'):
                config['parameters'] = json.loads(config['parameters'])
        
        return {
            "status": "success",
            "count": len(configs),
            "configs": configs
        }
        
    except Exception as e:
        logger.error(f"Failed to get configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_history_stats(user_id: int = Query(1)):
    """Get analysis history statistics"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Total analyses
            cursor.execute("""
                SELECT COUNT(*) as total FROM analysis_results WHERE user_id = ?
            """, (user_id,))
            total = cursor.fetchone()['total']
            
            # By type
            cursor.execute("""
                SELECT analysis_type, COUNT(*) as count 
                FROM analysis_results 
                WHERE user_id = ?
                GROUP BY analysis_type
            """, (user_id,))
            by_type = [dict(row) for row in cursor.fetchall()]
            
            # Saved analyses
            cursor.execute("""
                SELECT COUNT(*) as saved FROM analysis_results 
                WHERE user_id = ? AND is_saved = 1
            """, (user_id,))
            saved = cursor.fetchone()['saved']
            
            # Favorites
            cursor.execute("""
                SELECT COUNT(*) as favorites FROM analysis_results 
                WHERE user_id = ? AND is_favorite = 1
            """, (user_id,))
            favorites = cursor.fetchone()['favorites']
            
            # Recent activity (last 7 days)
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM analysis_results
                WHERE user_id = ? AND created_at >= date('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """, (user_id,))
            recent_activity = [dict(row) for row in cursor.fetchall()]
        
        return {
            "status": "success",
            "stats": {
                "total_analyses": total,
                "saved_analyses": saved,
                "favorite_analyses": favorites,
                "by_type": by_type,
                "recent_activity": recent_activity
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions

def _generate_comparison_insights(analyses: List[Dict]) -> List[str]:
    """Generate insights from analysis comparison"""
    insights = []
    
    if len(analyses) < 2:
        return insights
    
    # Compare by analysis type
    types = set(a['analysis_type'] for a in analyses)
    if len(types) == 1:
        insights.append(f"All analyses use the same type: {list(types)[0]}")
    else:
        insights.append(f"Comparing {len(types)} different analysis types")
    
    # Compare execution times
    exec_times = [a.get('execution_time_ms') for a in analyses if a.get('execution_time_ms')]
    if exec_times:
        fastest = min(exec_times)
        slowest = max(exec_times)
        if slowest > fastest * 2:
            insights.append(f"Execution time varies significantly: {fastest}ms to {slowest}ms")
    
    # Compare key metrics
    all_metrics = {}
    for analysis in analyses:
        for metric, value in analysis.get('key_metrics', {}).items():
            if metric not in all_metrics:
                all_metrics[metric] = []
            all_metrics[metric].append(value)
    
    for metric, values in all_metrics.items():
        if len(values) >= 2 and all(isinstance(v, (int, float)) for v in values):
            best_val = max(values)
            worst_val = min(values)
            best_idx = values.index(best_val)
            
            if best_val > worst_val * 1.1:  # At least 10% difference
                insights.append(
                    f"{metric.replace('_', ' ').title()}: Analysis {best_idx + 1} "
                    f"performs best ({best_val:.4f} vs {worst_val:.4f})"
                )
    
    return insights
