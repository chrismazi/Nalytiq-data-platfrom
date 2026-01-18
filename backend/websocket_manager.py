"""
WebSocket Manager for Real-Time Updates
Provides real-time progress updates for long-running operations
- ML model training progress
- Data processing status
- Analysis completion notifications
"""
import asyncio
import json
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import logging

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of WebSocket events"""
    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    
    # Progress events
    PROGRESS = "progress"
    STATUS_UPDATE = "status_update"
    
    # Job events
    JOB_STARTED = "job_started"
    JOB_PROGRESS = "job_progress"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    
    # ML events
    TRAINING_STARTED = "training_started"
    TRAINING_EPOCH = "training_epoch"
    TRAINING_COMPLETED = "training_completed"
    TRAINING_FAILED = "training_failed"
    
    # Data events
    UPLOAD_PROGRESS = "upload_progress"
    UPLOAD_COMPLETED = "upload_completed"
    ANALYSIS_COMPLETED = "analysis_completed"
    EXPORT_READY = "export_ready"
    
    # Notification events
    NOTIFICATION = "notification"
    ALERT = "alert"


@dataclass
class WebSocketMessage:
    """Structure for WebSocket messages"""
    event: str
    data: Dict[str, Any]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting
    Supports multiple rooms/channels for different update types
    """
    
    def __init__(self):
        # Active connections by user
        self._user_connections: Dict[int, Set[WebSocket]] = {}
        
        # Active connections by room/channel
        self._room_connections: Dict[str, Set[WebSocket]] = {}
        
        # All active connections
        self._all_connections: Set[WebSocket] = set()
        
        # Connection metadata
        self._connection_meta: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int = None, rooms: List[str] = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        self._all_connections.add(websocket)
        
        # Track by user
        if user_id:
            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(websocket)
        
        # Track by rooms
        if rooms:
            for room in rooms:
                if room not in self._room_connections:
                    self._room_connections[room] = set()
                self._room_connections[room].add(websocket)
        
        # Store metadata
        self._connection_meta[websocket] = {
            "user_id": user_id,
            "rooms": rooms or [],
            "connected_at": datetime.utcnow().isoformat()
        }
        
        # Send connection confirmation
        await self.send_personal(websocket, WebSocketMessage(
            event=EventType.CONNECTED.value,
            data={"message": "Connected to Nalytiq real-time updates"}
        ))
        
        logger.info(f"WebSocket connected: user={user_id}, rooms={rooms}")
    
    def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        self._all_connections.discard(websocket)
        
        # Remove from user connections
        meta = self._connection_meta.get(websocket, {})
        user_id = meta.get("user_id")
        if user_id and user_id in self._user_connections:
            self._user_connections[user_id].discard(websocket)
            if not self._user_connections[user_id]:
                del self._user_connections[user_id]
        
        # Remove from rooms
        for room in meta.get("rooms", []):
            if room in self._room_connections:
                self._room_connections[room].discard(websocket)
                if not self._room_connections[room]:
                    del self._room_connections[room]
        
        # Remove metadata
        self._connection_meta.pop(websocket, None)
        
        logger.info(f"WebSocket disconnected: user={user_id}")
    
    async def send_personal(self, websocket: WebSocket, message: WebSocketMessage):
        """Send message to a specific connection"""
        try:
            await websocket.send_text(message.to_json())
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def send_to_user(self, user_id: int, message: WebSocketMessage):
        """Send message to all connections of a specific user"""
        connections = self._user_connections.get(user_id, set())
        disconnected = []
        
        for websocket in connections:
            try:
                await websocket.send_text(message.to_json())
            except Exception as e:
                logger.error(f"Failed to send to user {user_id}: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected
        for ws in disconnected:
            self.disconnect(ws)
    
    async def send_to_room(self, room: str, message: WebSocketMessage):
        """Send message to all connections in a room"""
        connections = self._room_connections.get(room, set())
        disconnected = []
        
        for websocket in connections:
            try:
                await websocket.send_text(message.to_json())
            except Exception as e:
                logger.error(f"Failed to send to room {room}: {e}")
                disconnected.append(websocket)
        
        for ws in disconnected:
            self.disconnect(ws)
    
    async def broadcast(self, message: WebSocketMessage):
        """Broadcast message to all connections"""
        disconnected = []
        
        for websocket in self._all_connections:
            try:
                await websocket.send_text(message.to_json())
            except Exception as e:
                logger.error(f"Failed to broadcast: {e}")
                disconnected.append(websocket)
        
        for ws in disconnected:
            self.disconnect(ws)
    
    def join_room(self, websocket: WebSocket, room: str):
        """Add a connection to a room"""
        if room not in self._room_connections:
            self._room_connections[room] = set()
        self._room_connections[room].add(websocket)
        
        if websocket in self._connection_meta:
            self._connection_meta[websocket]["rooms"].append(room)
    
    def leave_room(self, websocket: WebSocket, room: str):
        """Remove a connection from a room"""
        if room in self._room_connections:
            self._room_connections[room].discard(websocket)
        
        if websocket in self._connection_meta:
            rooms = self._connection_meta[websocket].get("rooms", [])
            if room in rooms:
                rooms.remove(room)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self._all_connections)
    
    def get_room_count(self, room: str) -> int:
        """Get number of connections in a room"""
        return len(self._room_connections.get(room, set()))
    
    def get_stats(self) -> Dict:
        """Get connection statistics"""
        return {
            "total_connections": len(self._all_connections),
            "users_connected": len(self._user_connections),
            "rooms": {room: len(conns) for room, conns in self._room_connections.items()}
        }


# Global connection manager instance
manager = ConnectionManager()


# Helper functions for common operations
async def notify_job_started(user_id: int, job_id: str, job_type: str, description: str = None):
    """Notify user that a job has started"""
    await manager.send_to_user(user_id, WebSocketMessage(
        event=EventType.JOB_STARTED.value,
        data={
            "job_id": job_id,
            "job_type": job_type,
            "description": description or f"Started {job_type}",
            "progress": 0
        }
    ))


async def notify_job_progress(user_id: int, job_id: str, progress: int, message: str = None):
    """Notify user of job progress"""
    await manager.send_to_user(user_id, WebSocketMessage(
        event=EventType.JOB_PROGRESS.value,
        data={
            "job_id": job_id,
            "progress": min(100, max(0, progress)),
            "message": message
        }
    ))


async def notify_job_completed(user_id: int, job_id: str, result: Any = None):
    """Notify user that a job has completed"""
    await manager.send_to_user(user_id, WebSocketMessage(
        event=EventType.JOB_COMPLETED.value,
        data={
            "job_id": job_id,
            "progress": 100,
            "result": result
        }
    ))


async def notify_job_failed(user_id: int, job_id: str, error: str):
    """Notify user that a job has failed"""
    await manager.send_to_user(user_id, WebSocketMessage(
        event=EventType.JOB_FAILED.value,
        data={
            "job_id": job_id,
            "error": error
        }
    ))


async def notify_training_progress(user_id: int, job_id: str, epoch: int, total_epochs: int, 
                                    loss: float = None, metrics: Dict = None):
    """Notify user of ML training progress"""
    await manager.send_to_user(user_id, WebSocketMessage(
        event=EventType.TRAINING_EPOCH.value,
        data={
            "job_id": job_id,
            "epoch": epoch,
            "total_epochs": total_epochs,
            "progress": int((epoch / total_epochs) * 100),
            "loss": loss,
            "metrics": metrics
        }
    ))


async def notify_analysis_complete(user_id: int, analysis_id: int, analysis_type: str, 
                                    summary: str = None):
    """Notify user that analysis is complete"""
    await manager.send_to_user(user_id, WebSocketMessage(
        event=EventType.ANALYSIS_COMPLETED.value,
        data={
            "analysis_id": analysis_id,
            "analysis_type": analysis_type,
            "summary": summary
        }
    ))


async def send_notification(user_id: int, title: str, message: str, 
                            notification_type: str = "info"):
    """Send a general notification to user"""
    await manager.send_to_user(user_id, WebSocketMessage(
        event=EventType.NOTIFICATION.value,
        data={
            "title": title,
            "message": message,
            "type": notification_type  # info, success, warning, error
        }
    ))


async def broadcast_system_alert(message: str, alert_type: str = "info"):
    """Broadcast a system alert to all users"""
    await manager.broadcast(WebSocketMessage(
        event=EventType.ALERT.value,
        data={
            "message": message,
            "type": alert_type
        }
    ))


# Room names for different update types
class Rooms:
    """Predefined room names"""
    ML_TRAINING = "ml_training"
    DATA_PROCESSING = "data_processing"
    ANALYSIS = "analysis"
    EXPORTS = "exports"
    SYSTEM = "system"
    
    @staticmethod
    def dataset(dataset_id: int) -> str:
        return f"dataset_{dataset_id}"
    
    @staticmethod
    def user(user_id: int) -> str:
        return f"user_{user_id}"
    
    @staticmethod
    def job(job_id: str) -> str:
        return f"job_{job_id}"
