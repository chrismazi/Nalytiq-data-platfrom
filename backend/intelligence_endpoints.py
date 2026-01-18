"""Intelligence Engine API Endpoints.

The brain of the platform - endpoints for:
- SDG monitoring and dashboards
- Automated insights generation
- Publication-ready reports
- Anomaly detection
- Workflow automation
- System health monitoring
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/intelligence", tags=["Intelligence Engine"])


# ============================================
# REQUEST MODELS
# ============================================

class AnalyzeDatasetRequest(BaseModel):
    """Request for automated dataset analysis."""
    data: List[Dict[str, Any]] = Field(..., min_items=1)
    dataset_name: str = Field("dataset", max_length=100)


class GenerateReportRequest(BaseModel):
    """Request for automated report generation."""
    data: List[Dict[str, Any]] = Field(..., min_items=1)
    title: str = Field(..., max_length=200)
    description: str = ""


class DetectAnomaliesRequest(BaseModel):
    """Request for anomaly detection."""
    values: List[float] = Field(..., min_items=5)
    threshold_sigma: float = Field(3.0, ge=2.0, le=5.0)


class CreateAlertRequest(BaseModel):
    """Request to create an alert."""
    title: str = Field(..., max_length=200)
    message: str
    severity: str = Field("info", pattern="^(info|warning|critical)$")
    source: str = "api"
    metadata: Dict[str, Any] = {}


class RunWorkflowRequest(BaseModel):
    """Request to run an automated workflow."""
    workflow_id: str
    context: Dict[str, Any] = {}


# ============================================
# SDG MONITORING ENDPOINTS
# ============================================

@router.get("/sdg/dashboard")
async def get_sdg_dashboard():
    """Get comprehensive SDG progress dashboard.
    
    Returns:
    - Overall progress summary
    - Leading and lagging indicators
    - Progress by SDG category
    - Alerts for off-track indicators
    
    This is the executive view of Rwanda's SDG progress.
    """
    from intelligence_engine import get_intelligence_engine
    
    engine = get_intelligence_engine()
    return engine.get_sdg_dashboard()


@router.get("/sdg/indicators")
async def get_sdg_indicators():
    """Get all SDG indicators with current values.
    
    Returns detailed information for each tracked indicator
    including progress percentage and trend.
    """
    from intelligence_engine import get_intelligence_engine
    
    engine = get_intelligence_engine()
    indicators = engine.get_sdg_indicators()
    
    return {
        "indicators": indicators,
        "count": len(indicators),
        "last_updated": datetime.now().isoformat()
    }


@router.get("/sdg/indicator/{indicator_code}")
async def get_sdg_indicator(indicator_code: str):
    """Get details for a specific SDG indicator."""
    from intelligence_engine import get_intelligence_engine
    
    engine = get_intelligence_engine()
    indicators = engine.get_sdg_indicators()
    
    for ind in indicators:
        if ind["indicator_code"] == indicator_code:
            return ind
    
    raise HTTPException(status_code=404, detail=f"Indicator not found: {indicator_code}")


@router.get("/sdg/progress-summary")
async def get_sdg_progress_summary():
    """Get SDG progress summary for quick overview."""
    from intelligence_engine import get_intelligence_engine
    
    engine = get_intelligence_engine()
    dashboard = engine.get_sdg_dashboard()
    
    return {
        "summary": dashboard["summary"],
        "highlight": {
            "best_performing": dashboard["leaders"][0] if dashboard["leaders"] else None,
            "needs_attention": dashboard["needs_attention"][0] if dashboard["needs_attention"] else None
        },
        "message": f"Rwanda is on track for {dashboard['summary']['on_track']} out of {dashboard['summary']['total_indicators']} SDG indicators"
    }


# ============================================
# AUTOMATED ANALYSIS ENDPOINTS
# ============================================

@router.post("/analyze")
async def analyze_dataset(request: AnalyzeDatasetRequest):
    """One-click automated dataset analysis.
    
    Automatically generates:
    - Key insights and findings
    - Statistical summaries
    - Trend detection
    - Anomaly identification
    - Data quality assessment
    - Recommendations
    
    This is the genius feature - comprehensive analysis with one API call.
    """
    from intelligence_engine import get_intelligence_engine
    
    engine = get_intelligence_engine()
    
    analysis = engine.analyze_dataset(
        data=request.data,
        dataset_name=request.dataset_name
    )
    
    return {
        "analysis": analysis,
        "generated_at": datetime.now().isoformat(),
        "tip": "Use /intelligence/report to generate a publication-ready report from this analysis"
    }


@router.post("/report")
async def generate_report(request: GenerateReportRequest):
    """Generate publication-ready statistical report.
    
    Creates a comprehensive report suitable for:
    - Government publications
    - World Bank/IMF submissions
    - Academic papers
    - Press releases
    
    Includes executive summary, methodology, findings, and recommendations.
    """
    from intelligence_engine import get_intelligence_engine
    
    engine = get_intelligence_engine()
    
    report = engine.generate_report(
        data=request.data,
        title=request.title,
        description=request.description
    )
    
    return report


@router.post("/anomalies")
async def detect_anomalies(request: DetectAnomaliesRequest):
    """Detect anomalies in numeric data.
    
    Identifies:
    - Statistical outliers (Z-score method)
    - Trend breaks (sudden changes)
    
    Use this for data quality monitoring and early warning.
    """
    from intelligence_engine import get_intelligence_engine
    
    engine = get_intelligence_engine()
    
    result = engine.detect_anomalies(
        values=request.values,
        threshold=request.threshold_sigma
    )
    
    return {
        "result": result,
        "data_points": len(request.values),
        "threshold_sigma": request.threshold_sigma
    }


# ============================================
# ALERTS ENDPOINTS
# ============================================

@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = None,
    unacknowledged_only: bool = False
):
    """Get system alerts.
    
    Filters:
    - severity: info, warning, critical
    - unacknowledged_only: only pending alerts
    """
    from intelligence_engine import get_intelligence_engine, AlertSeverity
    
    engine = get_intelligence_engine()
    
    sev = AlertSeverity(severity) if severity else None
    
    return {
        "alerts": engine.get_alerts(severity=sev, unacknowledged_only=unacknowledged_only),
        "filter": {
            "severity": severity,
            "unacknowledged_only": unacknowledged_only
        }
    }


@router.post("/alerts")
async def create_alert(request: CreateAlertRequest):
    """Create a new alert."""
    from intelligence_engine import get_intelligence_engine, AlertSeverity
    
    engine = get_intelligence_engine()
    
    alert = engine.create_alert(
        title=request.title,
        message=request.message,
        severity=AlertSeverity(request.severity),
        source=request.source,
        metadata=request.metadata
    )
    
    return {
        "alert": alert.to_dict(),
        "message": "Alert created successfully"
    }


# ============================================
# WORKFLOW ENDPOINTS
# ============================================

@router.get("/workflows")
async def list_workflows():
    """List available automated workflows.
    
    Workflows are predefined sequences of operations like:
    - Daily data quality checks
    - Weekly SDG reports
    - Monthly statistical releases
    """
    from intelligence_engine import get_intelligence_engine
    
    engine = get_intelligence_engine()
    
    return {
        "workflows": engine.get_workflows(),
        "tip": "Use POST /intelligence/workflows/run to execute a workflow"
    }


@router.post("/workflows/run")
async def run_workflow(
    request: RunWorkflowRequest,
    background_tasks: BackgroundTasks
):
    """Execute an automated workflow.
    
    Available workflows:
    - daily_quality_check: Data quality monitoring
    - weekly_sdg_report: SDG progress report
    - monthly_statistical_release: Publication workflow
    """
    from intelligence_engine import get_intelligence_engine
    
    engine = get_intelligence_engine()
    
    result = await engine.run_workflow(
        workflow_id=request.workflow_id,
        context=request.context
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


# ============================================
# SYSTEM HEALTH ENDPOINTS
# ============================================

@router.get("/health")
async def get_system_health():
    """Get overall system health status.
    
    Returns:
    - Overall status (healthy, warning, critical)
    - Key metrics
    - Active alerts
    - SDG items needing attention
    """
    from intelligence_engine import get_intelligence_engine
    
    engine = get_intelligence_engine()
    return engine.get_system_health()


@router.get("/quick-stats")
async def get_quick_stats():
    """Get quick platform statistics for dashboard.
    
    Returns key metrics at a glance for executive dashboards.
    """
    from intelligence_engine import get_intelligence_engine
    
    engine = get_intelligence_engine()
    return engine.get_quick_stats()


@router.get("/status")
async def get_intelligence_status():
    """Get intelligence engine status and capabilities."""
    from intelligence_engine import get_intelligence_engine
    
    engine = get_intelligence_engine()
    
    return {
        "status": "operational",
        "capabilities": [
            {
                "name": "SDG Monitoring",
                "description": "Track Rwanda's progress on Sustainable Development Goals",
                "endpoint": "/sdg/dashboard"
            },
            {
                "name": "Automated Analysis",
                "description": "One-click comprehensive dataset analysis",
                "endpoint": "/analyze"
            },
            {
                "name": "Report Generation",
                "description": "Generate publication-ready statistical reports",
                "endpoint": "/report"
            },
            {
                "name": "Anomaly Detection",
                "description": "Detect outliers and trend breaks in data",
                "endpoint": "/anomalies"
            },
            {
                "name": "Workflow Automation",
                "description": "Execute predefined data workflows",
                "endpoint": "/workflows"
            },
            {
                "name": "Alert System",
                "description": "Create and manage system alerts",
                "endpoint": "/alerts"
            }
        ],
        "sdg_indicators_tracked": len(engine.get_sdg_indicators()),
        "workflows_available": len(engine.get_workflows()),
        "timestamp": datetime.now().isoformat()
    }


# ============================================
# INSIGHTS ENDPOINTS
# ============================================

@router.post("/insights/quick")
async def quick_insights(data: List[Dict[str, Any]]):
    """Get quick insights from data without full analysis.
    
    Returns top 3 most important insights for rapid decision making.
    """
    from intelligence_engine import InsightGenerator
    
    analysis = InsightGenerator.analyze_dataset(data)
    
    return {
        "quick_insights": analysis.get("key_findings", [])[:3],
        "data_quality": analysis.get("data_quality", {}).get("completeness", 100),
        "recommendation": "Use /intelligence/analyze for comprehensive analysis"
    }


@router.get("/insights/sdg-recommendations")
async def get_sdg_recommendations():
    """Get actionable recommendations for SDG improvement.
    
    Returns prioritized recommendations based on current SDG progress.
    """
    from intelligence_engine import get_intelligence_engine
    
    engine = get_intelligence_engine()
    dashboard = engine.get_sdg_dashboard()
    
    recommendations = []
    
    for item in dashboard.get("needs_attention", []):
        recommendations.append({
            "priority": "high",
            "sdg": item.get("sdg_name"),
            "indicator": item.get("indicator_name"),
            "current_progress": item.get("progress_percent"),
            "recommendation": f"Focus resources on improving {item.get('indicator_name')} to reach {item.get('target_value')} by 2030",
            "gap": item.get("target_value", 0) - item.get("current_value", 0)
        })
    
    return {
        "recommendations": recommendations,
        "overall_message": f"Rwanda needs to accelerate progress on {len(recommendations)} SDG indicators to meet 2030 targets"
    }
