"""
Real-time Notifications System

WebSocket-based real-time notifications with:
- User-specific channels
- Organization broadcasts
- System-wide announcements
- Notification persistence and history
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Set, Optional, List, Any
from enum import Enum
from dataclasses import dataclass, asdict
from fastapi import WebSocket, WebSocketDisconnect
import uuid
import os

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Notification types"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    ALERT = "alert"


class NotificationCategory(str, Enum):
    """Notification categories"""
    SYSTEM = "system"
    SECURITY = "security"
    DATA = "data"
    ML = "ml"
    COMPLIANCE = "compliance"
    XROAD = "xroad"


@dataclass
class Notification:
    """Notification data structure"""
    id: str
    type: NotificationType
    category: NotificationCategory
    title: str
    message: str
    timestamp: str
    user_id: Optional[str] = None
    organization_code: Optional[str] = None
    link: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    read: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConnectionManager:
    """WebSocket connection manager for real-time notifications"""
    
    def __init__(self):
        # User connections: user_id -> set of websockets
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # Organization connections: org_code -> set of websockets
        self.org_connections: Dict[str, Set[WebSocket]] = {}
        # All active connections
        self.active_connections: Set[WebSocket] = set()
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, str]] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        organization_code: Optional[str] = None
    ) -> None:
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        
        # Register to user channel
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)
        
        # Register to organization channel
        if organization_code:
            if organization_code not in self.org_connections:
                self.org_connections[organization_code] = set()
            self.org_connections[organization_code].add(websocket)
        
        # Track connection
        self.active_connections.add(websocket)
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "organization_code": organization_code or "",
            "connected_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"WebSocket connected: user={user_id}, org={organization_code}")
        
        # Send welcome message
        await self._send_to_websocket(websocket, Notification(
            id=str(uuid.uuid4()),
            type=NotificationType.INFO,
            category=NotificationCategory.SYSTEM,
            title="Connected",
            message="Real-time notifications enabled",
            timestamp=datetime.utcnow().isoformat()
        ))
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection"""
        metadata = self.connection_metadata.get(websocket, {})
        user_id = metadata.get("user_id")
        org_code = metadata.get("organization_code")
        
        # Remove from user connections
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove from org connections
        if org_code and org_code in self.org_connections:
            self.org_connections[org_code].discard(websocket)
            if not self.org_connections[org_code]:
                del self.org_connections[org_code]
        
        # Remove from active connections
        self.active_connections.discard(websocket)
        self.connection_metadata.pop(websocket, None)
        
        logger.info(f"WebSocket disconnected: user={user_id}")
    
    async def _send_to_websocket(self, websocket: WebSocket, notification: Notification) -> bool:
        """Send notification to a single websocket"""
        try:
            await websocket.send_json(notification.to_dict())
            return True
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")
            return False
    
    async def send_to_user(self, user_id: str, notification: Notification) -> int:
        """Send notification to a specific user"""
        notification.user_id = user_id
        sent = 0
        
        if user_id in self.user_connections:
            for websocket in list(self.user_connections[user_id]):
                if await self._send_to_websocket(websocket, notification):
                    sent += 1
        
        # Store notification for persistence
        await notification_store.save(notification)
        return sent
    
    async def send_to_organization(
        self,
        organization_code: str,
        notification: Notification
    ) -> int:
        """Send notification to all users in an organization"""
        notification.organization_code = organization_code
        sent = 0
        
        if organization_code in self.org_connections:
            for websocket in list(self.org_connections[organization_code]):
                if await self._send_to_websocket(websocket, notification):
                    sent += 1
        
        await notification_store.save(notification)
        return sent
    
    async def broadcast(self, notification: Notification) -> int:
        """Broadcast notification to all connected users"""
        sent = 0
        
        for websocket in list(self.active_connections):
            if await self._send_to_websocket(websocket, notification):
                sent += 1
        
        await notification_store.save(notification)
        return sent
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "users_connected": len(self.user_connections),
            "organizations_connected": len(self.org_connections),
        }


class NotificationStore:
    """Persistent notification storage"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self.notifications_file = os.path.join(data_dir, "notifications.json")
        self._notifications: List[Notification] = []
        self._load()
    
    def _load(self) -> None:
        """Load notifications from file"""
        try:
            if os.path.exists(self.notifications_file):
                with open(self.notifications_file, 'r') as f:
                    data = json.load(f)
                    self._notifications = [
                        Notification(**n) for n in data
                    ]
        except Exception as e:
            logger.warning(f"Failed to load notifications: {e}")
            self._notifications = []
    
    def _save(self) -> None:
        """Save notifications to file"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.notifications_file, 'w') as f:
                json.dump([n.to_dict() for n in self._notifications], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save notifications: {e}")
    
    async def save(self, notification: Notification) -> None:
        """Save a notification"""
        self._notifications.append(notification)
        # Keep only last 1000 notifications
        if len(self._notifications) > 1000:
            self._notifications = self._notifications[-1000:]
        self._save()
    
    def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        user_notifications = [
            n for n in self._notifications
            if n.user_id == user_id or n.user_id is None
        ]
        
        if unread_only:
            user_notifications = [n for n in user_notifications if not n.read]
        
        # Sort by timestamp descending
        user_notifications.sort(key=lambda n: n.timestamp, reverse=True)
        
        return [n.to_dict() for n in user_notifications[:limit]]
    
    def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        for n in self._notifications:
            if n.id == notification_id:
                n.read = True
                self._save()
                return True
        return False
    
    def mark_all_read(self, user_id: str) -> int:
        """Mark all user notifications as read"""
        count = 0
        for n in self._notifications:
            if (n.user_id == user_id or n.user_id is None) and not n.read:
                n.read = True
                count += 1
        if count > 0:
            self._save()
        return count
    
    def get_unread_count(self, user_id: str) -> int:
        """Get unread notification count for user"""
        return len([
            n for n in self._notifications
            if (n.user_id == user_id or n.user_id is None) and not n.read
        ])


# Global instances
connection_manager = ConnectionManager()
notification_store = NotificationStore()


class NotificationService:
    """High-level notification service"""
    
    def __init__(self):
        self.manager = connection_manager
        self.store = notification_store
    
    async def notify_user(
        self,
        user_id: str,
        title: str,
        message: str,
        type: NotificationType = NotificationType.INFO,
        category: NotificationCategory = NotificationCategory.SYSTEM,
        link: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Notification:
        """Send notification to a specific user"""
        notification = Notification(
            id=str(uuid.uuid4()),
            type=type,
            category=category,
            title=title,
            message=message,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            link=link,
            metadata=metadata
        )
        
        await self.manager.send_to_user(user_id, notification)
        return notification
    
    async def notify_organization(
        self,
        organization_code: str,
        title: str,
        message: str,
        type: NotificationType = NotificationType.INFO,
        category: NotificationCategory = NotificationCategory.SYSTEM
    ) -> Notification:
        """Send notification to an organization"""
        notification = Notification(
            id=str(uuid.uuid4()),
            type=type,
            category=category,
            title=title,
            message=message,
            timestamp=datetime.utcnow().isoformat(),
            organization_code=organization_code
        )
        
        await self.manager.send_to_organization(organization_code, notification)
        return notification
    
    async def broadcast_system(
        self,
        title: str,
        message: str,
        type: NotificationType = NotificationType.INFO
    ) -> Notification:
        """Broadcast system-wide notification"""
        notification = Notification(
            id=str(uuid.uuid4()),
            type=type,
            category=NotificationCategory.SYSTEM,
            title=title,
            message=message,
            timestamp=datetime.utcnow().isoformat()
        )
        
        await self.manager.broadcast(notification)
        return notification
    
    # Convenience methods for common notifications
    async def notify_ml_training_complete(
        self,
        user_id: str,
        model_id: str,
        model_name: str,
        accuracy: float
    ) -> Notification:
        """Notify user that ML training is complete"""
        return await self.notify_user(
            user_id=user_id,
            title="Training Complete",
            message=f"Model '{model_name}' finished training with {accuracy:.2%} accuracy",
            type=NotificationType.SUCCESS,
            category=NotificationCategory.ML,
            link=f"/models/{model_id}",
            metadata={"model_id": model_id, "accuracy": accuracy}
        )
    
    async def notify_dataset_access_approved(
        self,
        user_id: str,
        dataset_name: str,
        dataset_id: str
    ) -> Notification:
        """Notify user that dataset access was approved"""
        return await self.notify_user(
            user_id=user_id,
            title="Access Approved",
            message=f"Your access to '{dataset_name}' has been approved",
            type=NotificationType.SUCCESS,
            category=NotificationCategory.DATA,
            link=f"/federation?dataset={dataset_id}"
        )
    
    async def notify_security_alert(
        self,
        user_id: str,
        alert_message: str
    ) -> Notification:
        """Notify user of security alert"""
        return await self.notify_user(
            user_id=user_id,
            title="Security Alert",
            message=alert_message,
            type=NotificationType.ALERT,
            category=NotificationCategory.SECURITY
        )
    
    async def notify_compliance_action_required(
        self,
        organization_code: str,
        action: str
    ) -> Notification:
        """Notify organization of required compliance action"""
        return await self.notify_organization(
            organization_code=organization_code,
            title="Compliance Action Required",
            message=action,
            type=NotificationType.WARNING,
            category=NotificationCategory.COMPLIANCE
        )


# Global notification service
notification_service = NotificationService()


def get_notification_service() -> NotificationService:
    """Get the notification service instance"""
    return notification_service
