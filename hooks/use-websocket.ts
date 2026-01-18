/**
 * WebSocket Hook for Real-Time Updates
 * Connects to backend WebSocket for live progress updates
 */
import { useState, useEffect, useCallback, useRef } from 'react'

// WebSocket event types (matching backend)
export type WebSocketEventType =
    | 'connected'
    | 'disconnected'
    | 'error'
    | 'progress'
    | 'status_update'
    | 'job_started'
    | 'job_progress'
    | 'job_completed'
    | 'job_failed'
    | 'training_started'
    | 'training_epoch'
    | 'training_completed'
    | 'training_failed'
    | 'upload_progress'
    | 'upload_completed'
    | 'analysis_completed'
    | 'export_ready'
    | 'notification'
    | 'alert'

export interface WebSocketMessage {
    event: WebSocketEventType
    data: Record<string, any>
    timestamp: string
}

export interface JobProgress {
    jobId: string
    jobType: string
    progress: number
    message?: string
    error?: string
}

export interface UseWebSocketOptions {
    userId?: number
    rooms?: string[]
    autoConnect?: boolean
    reconnectAttempts?: number
    reconnectInterval?: number
    onMessage?: (message: WebSocketMessage) => void
    onConnect?: () => void
    onDisconnect?: () => void
    onError?: (error: Event) => void
}

export interface UseWebSocketReturn {
    connected: boolean
    connecting: boolean
    error: Error | null
    lastMessage: WebSocketMessage | null
    jobProgress: Record<string, JobProgress>
    notifications: WebSocketMessage[]
    connect: () => void
    disconnect: () => void
    joinRoom: (room: string) => void
    leaveRoom: (room: string) => void
    clearNotifications: () => void
}

const BACKEND_WS_URL = process.env.NEXT_PUBLIC_BACKEND_URL?.replace('http', 'ws') || 'ws://localhost:8000'

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
    const {
        userId,
        rooms = [],
        autoConnect = true,
        reconnectAttempts = 5,
        reconnectInterval = 3000,
        onMessage,
        onConnect,
        onDisconnect,
        onError
    } = options

    const [connected, setConnected] = useState(false)
    const [connecting, setConnecting] = useState(false)
    const [error, setError] = useState<Error | null>(null)
    const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
    const [jobProgress, setJobProgress] = useState<Record<string, JobProgress>>({})
    const [notifications, setNotifications] = useState<WebSocketMessage[]>([])

    const wsRef = useRef<WebSocket | null>(null)
    const reconnectCountRef = useRef(0)
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined)

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            return
        }

        setConnecting(true)
        setError(null)

        try {
            // Build WebSocket URL with query params
            const params = new URLSearchParams()
            if (userId) params.append('user_id', String(userId))
            if (rooms.length) params.append('rooms', rooms.join(','))

            const wsUrl = `${BACKEND_WS_URL}/ws?${params.toString()}`
            wsRef.current = new WebSocket(wsUrl)

            wsRef.current.onopen = () => {
                setConnected(true)
                setConnecting(false)
                reconnectCountRef.current = 0
                onConnect?.()
            }

            wsRef.current.onclose = () => {
                setConnected(false)
                setConnecting(false)
                onDisconnect?.()

                // Attempt reconnection
                if (reconnectCountRef.current < reconnectAttempts) {
                    reconnectCountRef.current++
                    reconnectTimeoutRef.current = setTimeout(() => {
                        connect()
                    }, reconnectInterval * reconnectCountRef.current)
                }
            }

            wsRef.current.onerror = (event) => {
                setError(new Error('WebSocket connection error'))
                setConnecting(false)
                onError?.(event)
            }

            wsRef.current.onmessage = (event) => {
                try {
                    const message: WebSocketMessage = JSON.parse(event.data)
                    setLastMessage(message)
                    handleMessage(message)
                    onMessage?.(message)
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e)
                }
            }
        } catch (e) {
            setError(e as Error)
            setConnecting(false)
        }
    }, [userId, rooms, reconnectAttempts, reconnectInterval, onConnect, onDisconnect, onError, onMessage])

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current)
        }
        reconnectCountRef.current = reconnectAttempts // Prevent reconnection
        wsRef.current?.close()
        wsRef.current = null
        setConnected(false)
    }, [reconnectAttempts])

    const handleMessage = useCallback((message: WebSocketMessage) => {
        switch (message.event) {
            case 'job_started':
            case 'job_progress':
                setJobProgress(prev => ({
                    ...prev,
                    [message.data.job_id]: {
                        jobId: message.data.job_id,
                        jobType: message.data.job_type,
                        progress: message.data.progress || 0,
                        message: message.data.message
                    }
                }))
                break

            case 'job_completed':
                setJobProgress(prev => ({
                    ...prev,
                    [message.data.job_id]: {
                        ...prev[message.data.job_id],
                        progress: 100,
                        message: 'Completed'
                    }
                }))
                break

            case 'job_failed':
                setJobProgress(prev => ({
                    ...prev,
                    [message.data.job_id]: {
                        ...prev[message.data.job_id],
                        error: message.data.error
                    }
                }))
                break

            case 'training_epoch':
                setJobProgress(prev => ({
                    ...prev,
                    [message.data.job_id]: {
                        jobId: message.data.job_id,
                        jobType: 'ml_training',
                        progress: message.data.progress,
                        message: `Epoch ${message.data.epoch}/${message.data.total_epochs}`
                    }
                }))
                break

            case 'notification':
            case 'alert':
                setNotifications(prev => [message, ...prev].slice(0, 50))
                break
        }
    }, [])

    const joinRoom = useCallback((room: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                action: 'join_room',
                room
            }))
        }
    }, [])

    const leaveRoom = useCallback((room: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                action: 'leave_room',
                room
            }))
        }
    }, [])

    const clearNotifications = useCallback(() => {
        setNotifications([])
    }, [])

    // Auto-connect on mount
    useEffect(() => {
        if (autoConnect) {
            connect()
        }

        return () => {
            disconnect()
        }
    }, [autoConnect, connect, disconnect])

    return {
        connected,
        connecting,
        error,
        lastMessage,
        jobProgress,
        notifications,
        connect,
        disconnect,
        joinRoom,
        leaveRoom,
        clearNotifications
    }
}

/**
 * Hook for tracking specific job progress
 */
export function useJobProgress(jobId: string | null) {
    const { jobProgress, connected } = useWebSocket({ autoConnect: !!jobId })

    return {
        progress: jobId ? jobProgress[jobId] : null,
        connected
    }
}

/**
 * Hook for receiving real-time notifications
 */
export function useNotifications(options?: { maxNotifications?: number }) {
    const { maxNotifications = 20 } = options || {}
    const { notifications, clearNotifications, connected } = useWebSocket()

    return {
        notifications: notifications.slice(0, maxNotifications),
        unreadCount: notifications.filter(n => !n.data.read).length,
        clearNotifications,
        connected
    }
}
