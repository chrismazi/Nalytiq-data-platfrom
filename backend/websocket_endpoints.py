"""
WebSocket Endpoints for Real-Time Updates
Integrates with FastAPI for WebSocket connections
"""
import json
from typing import Optional
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from websocket_manager import manager, WebSocketMessage, EventType, Rooms

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[int] = Query(None),
    rooms: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time updates
    
    Query Parameters:
    - user_id: User ID for personalized notifications
    - rooms: Comma-separated list of rooms to join
    """
    # Parse rooms
    room_list = rooms.split(',') if rooms else []
    
    # Add default rooms
    if user_id:
        room_list.append(Rooms.user(user_id))
    
    await manager.connect(websocket, user_id, room_list)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                action = message.get('action')
                
                if action == 'join_room':
                    room = message.get('room')
                    if room:
                        manager.join_room(websocket, room)
                        await manager.send_personal(websocket, WebSocketMessage(
                            event=EventType.STATUS_UPDATE.value,
                            data={"message": f"Joined room: {room}"}
                        ))
                
                elif action == 'leave_room':
                    room = message.get('room')
                    if room:
                        manager.leave_room(websocket, room)
                        await manager.send_personal(websocket, WebSocketMessage(
                            event=EventType.STATUS_UPDATE.value,
                            data={"message": f"Left room: {room}"}
                        ))
                
                elif action == 'ping':
                    await manager.send_personal(websocket, WebSocketMessage(
                        event=EventType.STATUS_UPDATE.value,
                        data={"message": "pong"}
                    ))
                
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from client: {data}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected: user={user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.get("/stats")
async def websocket_stats():
    """Get WebSocket connection statistics"""
    return manager.get_stats()


# Helper functions for sending notifications from other parts of the app

async def notify_user(user_id: int, event: str, data: dict):
    """Send notification to a specific user"""
    await manager.send_to_user(user_id, WebSocketMessage(
        event=event,
        data=data
    ))


async def notify_room(room: str, event: str, data: dict):
    """Send notification to a room"""
    await manager.send_to_room(room, WebSocketMessage(
        event=event,
        data=data
    ))


async def broadcast_all(event: str, data: dict):
    """Broadcast to all connected clients"""
    await manager.broadcast(WebSocketMessage(
        event=event,
        data=data
    ))


# Integration helpers for the job processor

async def notify_job_event(user_id: int, job_id: str, event: str, data: dict):
    """Notify user about job events"""
    await manager.send_to_user(user_id, WebSocketMessage(
        event=event,
        data={
            "job_id": job_id,
            **data
        }
    ))


async def notify_training_progress(
    user_id: int,
    job_id: str,
    epoch: int,
    total_epochs: int,
    loss: float = None,
    metrics: dict = None
):
    """Notify user about ML training progress"""
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


async def notify_analysis_complete(
    user_id: int,
    analysis_id: int,
    analysis_type: str,
    summary: str = None
):
    """Notify user that analysis is complete"""
    await manager.send_to_user(user_id, WebSocketMessage(
        event=EventType.ANALYSIS_COMPLETED.value,
        data={
            "analysis_id": analysis_id,
            "analysis_type": analysis_type,
            "summary": summary
        }
    ))


async def notify_export_ready(user_id: int, download_url: str, format: str, file_size: int = None):
    """Notify user that export is ready"""
    await manager.send_to_user(user_id, WebSocketMessage(
        event=EventType.EXPORT_READY.value,
        data={
            "download_url": download_url,
            "format": format,
            "file_size": file_size
        }
    ))
