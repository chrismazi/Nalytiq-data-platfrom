"""
API Endpoints for Advanced Features

Endpoints for:
- Real-time notifications
- Advanced ML
- Custom reports
- Email notifications
- Scheduled jobs
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Advanced Features"])


# ============================================
# NOTIFICATIONS ENDPOINTS
# ============================================

class SendNotificationRequest(BaseModel):
    user_id: Optional[str] = None
    organization_code: Optional[str] = None
    title: str
    message: str
    type: str = "info"
    category: str = "system"
    link: Optional[str] = None


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: str = Query(...),
    organization_code: Optional[str] = Query(None)
):
    """WebSocket endpoint for real-time notifications"""
    from notifications import connection_manager
    
    await connection_manager.connect(websocket, user_id, organization_code)
    
    try:
        while True:
            # Keep connection alive, handle incoming messages
            data = await websocket.receive_text()
            # Can handle acknowledgments, mark as read, etc.
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)


@router.post("/notifications/send")
async def send_notification(request: SendNotificationRequest):
    """Send a notification to a user or organization"""
    from notifications import get_notification_service, NotificationType, NotificationCategory
    
    service = get_notification_service()
    
    if request.user_id:
        notification = await service.notify_user(
            user_id=request.user_id,
            title=request.title,
            message=request.message,
            type=NotificationType(request.type),
            category=NotificationCategory(request.category),
            link=request.link
        )
    elif request.organization_code:
        notification = await service.notify_organization(
            organization_code=request.organization_code,
            title=request.title,
            message=request.message,
            type=NotificationType(request.type),
            category=NotificationCategory(request.category)
        )
    else:
        notification = await service.broadcast_system(
            title=request.title,
            message=request.message,
            type=NotificationType(request.type)
        )
    
    return notification.to_dict()


@router.get("/notifications/{user_id}")
async def get_user_notifications(
    user_id: str,
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False)
):
    """Get notifications for a user"""
    from notifications import notification_store
    
    return notification_store.get_user_notifications(user_id, limit, unread_only)


@router.post("/notifications/{user_id}/read/{notification_id}")
async def mark_notification_read(user_id: str, notification_id: str):
    """Mark a notification as read"""
    from notifications import notification_store
    
    success = notification_store.mark_as_read(notification_id, user_id)
    return {"success": success}


@router.post("/notifications/{user_id}/read-all")
async def mark_all_notifications_read(user_id: str):
    """Mark all notifications as read"""
    from notifications import notification_store
    
    count = notification_store.mark_all_read(user_id)
    return {"marked_read": count}


@router.get("/notifications/{user_id}/unread-count")
async def get_unread_count(user_id: str):
    """Get unread notification count"""
    from notifications import notification_store
    
    return {"unread_count": notification_store.get_unread_count(user_id)}


@router.get("/notifications/stats")
async def get_notification_stats():
    """Get notification system stats"""
    from notifications import connection_manager
    
    return connection_manager.get_stats()


# ============================================
# ADVANCED ML ENDPOINTS
# ============================================

class AutoMLRequest(BaseModel):
    dataset_id: str
    target_column: str
    model_type: str = "classification"
    algorithms: Optional[List[str]] = None
    search_method: str = "random"
    n_iter: int = 20


class TrainModelRequest(BaseModel):
    name: str
    model_type: str
    algorithm: str
    target_column: str
    feature_columns: List[str]
    hyperparameters: Dict[str, Any] = {}
    description: str = ""
    tags: List[str] = []


class ABTestRequest(BaseModel):
    model_a_id: str
    model_b_id: str
    traffic_split: float = 0.5
    metric: str = "accuracy"
    min_samples: int = 100


@router.get("/ml/models")
async def list_ml_models():
    """List all registered ML models"""
    from advanced_ml import get_model_registry
    
    registry = get_model_registry()
    return registry.list_models()


@router.get("/ml/models/{model_id}")
async def get_ml_model(model_id: str):
    """Get ML model details"""
    from advanced_ml import get_model_registry
    
    registry = get_model_registry()
    if model_id not in registry.models:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return registry.models[model_id].to_dict()


@router.get("/ml/models/{model_id}/versions")
async def get_model_versions(model_id: str):
    """Get all versions of a model"""
    from advanced_ml import get_model_registry
    
    registry = get_model_registry()
    return registry.get_model_versions(model_id)


@router.post("/ml/models/{model_id}/promote/{version_id}")
async def promote_model_version(model_id: str, version_id: str):
    """Promote a model version to production"""
    from advanced_ml import get_model_registry
    
    registry = get_model_registry()
    success = registry.promote_to_production(version_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return {"success": True, "production_version": version_id}


@router.post("/ml/automl")
async def run_automl(request: AutoMLRequest, background_tasks: BackgroundTasks):
    """Run AutoML to find the best model"""
    from advanced_ml import get_automl_engine, ModelType
    
    # In production, this would load actual data
    # For now, return a mock response
    return {
        "status": "started",
        "message": "AutoML job started in background",
        "dataset_id": request.dataset_id,
        "target_column": request.target_column
    }


@router.post("/ml/ab-test")
async def create_ab_test(request: ABTestRequest):
    """Create an A/B test experiment"""
    from advanced_ml import get_ab_test_manager
    import uuid
    
    manager = get_ab_test_manager()
    experiment_id = str(uuid.uuid4())[:8]
    
    experiment = manager.create_experiment(
        experiment_id=experiment_id,
        model_a_id=request.model_a_id,
        model_b_id=request.model_b_id,
        traffic_split=request.traffic_split,
        metric=request.metric,
        min_samples=request.min_samples
    )
    
    return experiment


@router.get("/ml/ab-test/{experiment_id}")
async def get_ab_test_results(experiment_id: str):
    """Get A/B test results"""
    from advanced_ml import get_ab_test_manager
    
    manager = get_ab_test_manager()
    results = manager.get_experiment_results(experiment_id)
    
    if not results:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    return results


# ============================================
# REPORT BUILDER ENDPOINTS
# ============================================

class CreateReportRequest(BaseModel):
    name: str
    description: str = ""
    sections: List[Dict[str, Any]] = []
    parameters: Dict[str, Any] = {}
    tags: List[str] = []


class GenerateReportRequest(BaseModel):
    format: str = "pdf"
    parameters: Dict[str, Any] = {}


@router.get("/reports")
async def list_reports():
    """List all report definitions"""
    from report_builder import get_report_builder
    
    builder = get_report_builder()
    return builder.list_reports()


@router.post("/reports")
async def create_report(request: CreateReportRequest):
    """Create a new report definition"""
    from report_builder import get_report_builder
    
    builder = get_report_builder()
    report = builder.create_report(
        name=request.name,
        description=request.description,
        sections=request.sections,
        parameters=request.parameters,
        tags=request.tags
    )
    
    return report.to_dict()


@router.post("/reports/{report_id}/generate")
async def generate_report(report_id: str, request: GenerateReportRequest):
    """Generate a report in the specified format"""
    from report_builder import get_report_builder, ReportFormat
    
    builder = get_report_builder()
    
    try:
        format_enum = ReportFormat(request.format)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid format: {request.format}")
    
    try:
        generated = builder.generate_report(
            report_id=report_id,
            format=format_enum,
            parameters=request.parameters
        )
        return generated.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/reports/{report_id}/generated")
async def get_generated_reports(report_id: str):
    """Get generated instances of a report"""
    from report_builder import get_report_builder
    
    builder = get_report_builder()
    return builder.get_generated_reports(report_id)


# ============================================
# EMAIL ENDPOINTS
# ============================================

class SendEmailRequest(BaseModel):
    to: List[str]
    subject: str
    body_text: str
    body_html: Optional[str] = None
    cc: List[str] = []
    priority: str = "normal"


class SendTemplateEmailRequest(BaseModel):
    template_id: str
    to: List[str]
    data: Dict[str, Any]


@router.get("/email/templates")
async def list_email_templates():
    """List available email templates"""
    from email_service import EmailTemplate
    
    return {"templates": EmailTemplate.list_templates()}


@router.post("/email/send")
async def send_email(request: SendEmailRequest):
    """Send an email"""
    from email_service import get_email_service, EmailPriority
    
    service = get_email_service()
    
    message = service.send(
        to=request.to,
        subject=request.subject,
        body_text=request.body_text,
        body_html=request.body_html,
        cc=request.cc,
        priority=EmailPriority(request.priority)
    )
    
    return message.to_dict()


@router.post("/email/send-template")
async def send_template_email(request: SendTemplateEmailRequest):
    """Send an email using a template"""
    from email_service import get_email_service
    
    service = get_email_service()
    
    try:
        message = service.send_template(
            template_id=request.template_id,
            to=request.to,
            data=request.data
        )
        return message.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/email/log")
async def get_email_log(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """Get email sending log"""
    from email_service import get_email_service, EmailStatus
    
    service = get_email_service()
    
    status_filter = EmailStatus(status) if status else None
    return service.get_email_log(status=status_filter, limit=limit)


# ============================================
# SCHEDULED JOBS ENDPOINTS
# ============================================

class CreateJobRequest(BaseModel):
    name: str
    handler: str
    job_type: str = "one_time"
    schedule: Optional[str] = None
    interval_seconds: Optional[int] = None
    run_at: Optional[str] = None
    parameters: Dict[str, Any] = {}
    description: str = ""
    max_retries: int = 3
    timeout_seconds: int = 3600
    tags: List[str] = []


@router.get("/jobs")
async def list_jobs(include_disabled: bool = Query(False)):
    """List all scheduled jobs"""
    from scheduled_jobs import get_job_scheduler
    
    scheduler = get_job_scheduler()
    return scheduler.list_jobs(include_disabled)


@router.get("/jobs/handlers")
async def list_job_handlers():
    """List available job handlers"""
    from scheduled_jobs import JobRegistry
    
    return {"handlers": JobRegistry.list_handlers()}


@router.post("/jobs")
async def create_job(request: CreateJobRequest):
    """Create a new scheduled job"""
    from scheduled_jobs import get_job_scheduler, JobType
    from datetime import datetime
    
    scheduler = get_job_scheduler()
    
    run_at = None
    if request.run_at:
        run_at = datetime.fromisoformat(request.run_at)
    
    job = scheduler.create_job(
        name=request.name,
        handler=request.handler,
        job_type=JobType(request.job_type),
        schedule=request.schedule,
        interval_seconds=request.interval_seconds,
        run_at=run_at,
        parameters=request.parameters,
        description=request.description,
        max_retries=request.max_retries,
        timeout_seconds=request.timeout_seconds,
        tags=request.tags
    )
    
    return job.to_dict()


@router.post("/jobs/{job_id}/run")
async def run_job_now(job_id: str, force: bool = Query(False)):
    """Run a job immediately"""
    from scheduled_jobs import get_job_scheduler
    
    scheduler = get_job_scheduler()
    
    try:
        execution = await scheduler.run_job(job_id, force)
        return execution.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/jobs/{job_id}/executions")
async def get_job_executions(job_id: str, limit: int = Query(20, ge=1, le=100)):
    """Get execution history for a job"""
    from scheduled_jobs import get_job_scheduler
    
    scheduler = get_job_scheduler()
    return scheduler.get_job_executions(job_id, limit)


@router.post("/jobs/{job_id}/enable")
async def enable_job(job_id: str):
    """Enable a scheduled job"""
    from scheduled_jobs import get_job_scheduler
    
    scheduler = get_job_scheduler()
    success = scheduler.enable_job(job_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"success": True}


@router.post("/jobs/{job_id}/disable")
async def disable_job(job_id: str):
    """Disable a scheduled job"""
    from scheduled_jobs import get_job_scheduler
    
    scheduler = get_job_scheduler()
    success = scheduler.disable_job(job_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"success": True}


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a scheduled job"""
    from scheduled_jobs import get_job_scheduler
    
    scheduler = get_job_scheduler()
    success = scheduler.delete_job(job_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"success": True}


@router.get("/jobs/stats")
async def get_scheduler_stats():
    """Get scheduler statistics"""
    from scheduled_jobs import get_job_scheduler
    
    scheduler = get_job_scheduler()
    return scheduler.get_stats()


@router.post("/jobs/scheduler/start")
async def start_scheduler():
    """Start the job scheduler"""
    from scheduled_jobs import get_job_scheduler
    
    scheduler = get_job_scheduler()
    await scheduler.start()
    return {"status": "started"}


@router.post("/jobs/scheduler/stop")
async def stop_scheduler():
    """Stop the job scheduler"""
    from scheduled_jobs import get_job_scheduler
    
    scheduler = get_job_scheduler()
    await scheduler.stop()
    return {"status": "stopped"}
