"""
Background Job Processor
Handles long-running tasks asynchronously with progress tracking
Uses asyncio by default, with optional Celery integration for production
"""
import asyncio
import uuid
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import traceback
import logging

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status states"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(Enum):
    """Types of background jobs"""
    ML_TRAINING = "ml_training"
    DATA_UPLOAD = "data_upload"
    DATA_PROCESSING = "data_processing"
    ANALYSIS = "analysis"
    EXPORT = "export"
    REPORT_GENERATION = "report_generation"
    EMAIL_SEND = "email_send"


@dataclass
class Job:
    """Represents a background job"""
    id: str
    job_type: JobType
    user_id: int
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    message: str = ""
    result: Any = None
    error: str = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime = None
    completed_at: datetime = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "job_type": self.job_type.value,
            "user_id": self.user_id,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata
        }


class JobStore:
    """In-memory job storage with optional persistence"""
    
    def __init__(self, max_jobs: int = 1000):
        self._jobs: Dict[str, Job] = {}
        self._user_jobs: Dict[int, List[str]] = {}
        self.max_jobs = max_jobs
    
    def add(self, job: Job) -> str:
        """Add a job to the store"""
        self._jobs[job.id] = job
        
        if job.user_id not in self._user_jobs:
            self._user_jobs[job.user_id] = []
        self._user_jobs[job.user_id].append(job.id)
        
        # Cleanup old jobs if needed
        self._cleanup_if_needed()
        
        return job.id
    
    def get(self, job_id: str) -> Optional[Job]:
        """Get a job by ID"""
        return self._jobs.get(job_id)
    
    def update(self, job_id: str, **kwargs):
        """Update job fields"""
        job = self._jobs.get(job_id)
        if job:
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
    
    def get_user_jobs(self, user_id: int, status: JobStatus = None) -> List[Job]:
        """Get all jobs for a user, optionally filtered by status"""
        job_ids = self._user_jobs.get(user_id, [])
        jobs = [self._jobs[jid] for jid in job_ids if jid in self._jobs]
        
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)
    
    def delete(self, job_id: str):
        """Delete a job"""
        job = self._jobs.pop(job_id, None)
        if job and job.user_id in self._user_jobs:
            if job_id in self._user_jobs[job.user_id]:
                self._user_jobs[job.user_id].remove(job_id)
    
    def _cleanup_if_needed(self):
        """Remove old completed jobs if over limit"""
        if len(self._jobs) <= self.max_jobs:
            return
        
        # Sort jobs by completion time, remove oldest completed
        completed = [j for j in self._jobs.values() 
                     if j.status in [JobStatus.COMPLETED, JobStatus.FAILED]]
        completed.sort(key=lambda j: j.completed_at or j.created_at)
        
        to_remove = len(self._jobs) - self.max_jobs
        for job in completed[:to_remove]:
            self.delete(job.id)


class JobProcessor:
    """
    Background job processor
    Manages job execution with progress tracking and WebSocket notifications
    """
    
    def __init__(self, max_workers: int = 4):
        self.store = JobStore()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._handlers: Dict[JobType, Callable] = {}
        self._websocket_manager = None
    
    def set_websocket_manager(self, manager):
        """Set WebSocket manager for notifications"""
        self._websocket_manager = manager
    
    def register_handler(self, job_type: JobType, handler: Callable):
        """Register a handler for a job type"""
        self._handlers[job_type] = handler
    
    def create_job(self, job_type: JobType, user_id: int, 
                   metadata: Dict = None) -> Job:
        """Create a new job"""
        job = Job(
            id=str(uuid.uuid4()),
            job_type=job_type,
            user_id=user_id,
            metadata=metadata or {}
        )
        self.store.add(job)
        return job
    
    async def submit(self, job: Job, handler: Callable = None, *args, **kwargs) -> str:
        """Submit a job for execution"""
        # Use registered handler if not provided
        if handler is None:
            handler = self._handlers.get(job.job_type)
        
        if handler is None:
            job.status = JobStatus.FAILED
            job.error = f"No handler registered for job type: {job.job_type.value}"
            return job.id
        
        # Start async execution
        task = asyncio.create_task(
            self._execute_job(job, handler, *args, **kwargs)
        )
        self._running_tasks[job.id] = task
        
        return job.id
    
    async def _execute_job(self, job: Job, handler: Callable, *args, **kwargs):
        """Execute a job with progress tracking"""
        try:
            # Update status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            
            # Notify start
            await self._notify_progress(job, 0, "Starting...")
            
            # Create progress callback
            async def progress_callback(progress: int, message: str = None):
                job.progress = progress
                job.message = message or ""
                await self._notify_progress(job, progress, message)
            
            # Execute handler
            if asyncio.iscoroutinefunction(handler):
                result = await handler(job, progress_callback, *args, **kwargs)
            else:
                # Run sync handler in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.executor,
                    lambda: handler(job, lambda p, m: None, *args, **kwargs)
                )
            
            # Update completion
            job.status = JobStatus.COMPLETED
            job.progress = 100
            job.result = result
            job.completed_at = datetime.utcnow()
            
            # Notify completion
            await self._notify_complete(job)
            
        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            await self._notify_cancelled(job)
            
        except Exception as e:
            logger.error(f"Job {job.id} failed: {e}\n{traceback.format_exc()}")
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.utcnow()
            await self._notify_failed(job)
        
        finally:
            self._running_tasks.pop(job.id, None)
    
    async def cancel(self, job_id: str) -> bool:
        """Cancel a running job"""
        task = self._running_tasks.get(job_id)
        if task and not task.done():
            task.cancel()
            return True
        return False
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        return self.store.get(job_id)
    
    def get_user_jobs(self, user_id: int, status: JobStatus = None) -> List[Job]:
        """Get jobs for a user"""
        return self.store.get_user_jobs(user_id, status)
    
    async def _notify_progress(self, job: Job, progress: int, message: str = None):
        """Send progress notification via WebSocket"""
        if self._websocket_manager:
            from websocket_manager import WebSocketMessage, EventType
            await self._websocket_manager.send_to_user(
                job.user_id,
                WebSocketMessage(
                    event=EventType.JOB_PROGRESS.value,
                    data={
                        "job_id": job.id,
                        "job_type": job.job_type.value,
                        "progress": progress,
                        "message": message
                    }
                )
            )
    
    async def _notify_complete(self, job: Job):
        """Send completion notification"""
        if self._websocket_manager:
            from websocket_manager import WebSocketMessage, EventType
            await self._websocket_manager.send_to_user(
                job.user_id,
                WebSocketMessage(
                    event=EventType.JOB_COMPLETED.value,
                    data={
                        "job_id": job.id,
                        "job_type": job.job_type.value,
                        "message": "Job completed successfully"
                    }
                )
            )
    
    async def _notify_failed(self, job: Job):
        """Send failure notification"""
        if self._websocket_manager:
            from websocket_manager import WebSocketMessage, EventType
            await self._websocket_manager.send_to_user(
                job.user_id,
                WebSocketMessage(
                    event=EventType.JOB_FAILED.value,
                    data={
                        "job_id": job.id,
                        "job_type": job.job_type.value,
                        "error": job.error
                    }
                )
            )
    
    async def _notify_cancelled(self, job: Job):
        """Send cancellation notification"""
        if self._websocket_manager:
            from websocket_manager import WebSocketMessage, EventType
            await self._websocket_manager.send_to_user(
                job.user_id,
                WebSocketMessage(
                    event=EventType.JOB_PROGRESS.value,
                    data={
                        "job_id": job.id,
                        "job_type": job.job_type.value,
                        "message": "Job cancelled"
                    }
                )
            )


# Global processor instance
_processor = None


def get_job_processor() -> JobProcessor:
    """Get the global job processor instance"""
    global _processor
    if _processor is None:
        _processor = JobProcessor()
        _register_default_handlers(_processor)
    return _processor


def _register_default_handlers(processor: JobProcessor):
    """Register default job handlers"""
    
    # ML Training handler
    async def ml_training_handler(job: Job, progress_callback, dataset_id: int, 
                                   target: str, algorithm: str, **params):
        """Handle ML training job"""
        await progress_callback(10, f"Loading dataset {dataset_id}...")
        
        # Simulate loading
        await asyncio.sleep(1)
        
        await progress_callback(20, "Preparing data...")
        await asyncio.sleep(1)
        
        await progress_callback(30, f"Training {algorithm} model...")
        
        # Simulate training epochs
        total_epochs = params.get('epochs', 10)
        for epoch in range(1, total_epochs + 1):
            progress = 30 + int((epoch / total_epochs) * 60)
            await progress_callback(progress, f"Epoch {epoch}/{total_epochs}")
            await asyncio.sleep(0.5)
        
        await progress_callback(95, "Evaluating model...")
        await asyncio.sleep(1)
        
        return {
            "model_id": str(uuid.uuid4()),
            "accuracy": 0.85,
            "message": "Training completed successfully"
        }
    
    processor.register_handler(JobType.ML_TRAINING, ml_training_handler)
    
    # Export handler
    async def export_handler(job: Job, progress_callback, dataset_id: int, 
                              format: str, **options):
        """Handle export job"""
        await progress_callback(20, f"Loading dataset {dataset_id}...")
        await asyncio.sleep(1)
        
        await progress_callback(50, f"Generating {format} file...")
        await asyncio.sleep(2)
        
        await progress_callback(80, "Preparing download...")
        await asyncio.sleep(1)
        
        return {
            "download_url": f"/downloads/{job.id}.{format}",
            "file_size": 1024 * 100  # 100KB
        }
    
    processor.register_handler(JobType.EXPORT, export_handler)
    
    # Report generation handler
    async def report_handler(job: Job, progress_callback, dataset_id: int, 
                              report_type: str, **options):
        """Handle report generation job"""
        await progress_callback(10, "Analyzing data...")
        await asyncio.sleep(2)
        
        await progress_callback(40, "Generating charts...")
        await asyncio.sleep(2)
        
        await progress_callback(70, "Building report...")
        await asyncio.sleep(2)
        
        await progress_callback(90, "Finalizing PDF...")
        await asyncio.sleep(1)
        
        return {
            "report_url": f"/reports/{job.id}.pdf",
            "pages": 10
        }
    
    processor.register_handler(JobType.REPORT_GENERATION, report_handler)
