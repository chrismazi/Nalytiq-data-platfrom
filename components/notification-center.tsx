/**
 * Real-Time Notifications Component
 * Shows notifications from WebSocket updates
 */
"use client"

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Bell,
    BellOff,
    X,
    CheckCircle2,
    AlertCircle,
    Info,
    AlertTriangle,
    Trash2
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover'
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from '@/components/ui/sheet'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { useWebSocket, WebSocketMessage } from '@/hooks/use-websocket'

interface NotificationItem {
    id: string
    event: string
    title: string
    message: string
    type: 'success' | 'error' | 'warning' | 'info'
    timestamp: Date
    read: boolean
}

const NOTIFICATION_ICONS = {
    success: CheckCircle2,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info
}

const NOTIFICATION_COLORS = {
    success: 'text-green-500 bg-green-500/10',
    error: 'text-red-500 bg-red-500/10',
    warning: 'text-yellow-500 bg-yellow-500/10',
    info: 'text-blue-500 bg-blue-500/10'
}

function parseNotification(message: WebSocketMessage): NotificationItem {
    const data = message.data

    let type: NotificationItem['type'] = 'info'
    let title = 'Notification'
    let msg = ''

    switch (message.event) {
        case 'job_completed':
            type = 'success'
            title = 'Job Completed'
            msg = data.message || 'Your job has finished successfully'
            break
        case 'job_failed':
            type = 'error'
            title = 'Job Failed'
            msg = data.error || 'An error occurred'
            break
        case 'training_completed':
            type = 'success'
            title = 'Training Complete'
            msg = 'Your ML model has been trained successfully'
            break
        case 'analysis_completed':
            type = 'success'
            title = 'Analysis Complete'
            msg = data.summary || 'Your analysis is ready'
            break
        case 'export_ready':
            type = 'success'
            title = 'Export Ready'
            msg = 'Your file is ready for download'
            break
        case 'notification':
            type = data.type || 'info'
            title = data.title || 'Notification'
            msg = data.message || ''
            break
        case 'alert':
            type = data.type === 'error' ? 'error' : 'warning'
            title = 'System Alert'
            msg = data.message || ''
            break
        default:
            msg = JSON.stringify(data)
    }

    return {
        id: `${message.event}-${message.timestamp}`,
        event: message.event,
        title,
        message: msg,
        type,
        timestamp: new Date(message.timestamp),
        read: false
    }
}

function NotificationEntry({
    notification,
    onDismiss,
    onMarkRead
}: {
    notification: NotificationItem
    onDismiss: () => void
    onMarkRead: () => void
}) {
    const Icon = NOTIFICATION_ICONS[notification.type]
    const colorClass = NOTIFICATION_COLORS[notification.type]

    useEffect(() => {
        if (!notification.read) {
            // Mark as read after 2 seconds of viewing
            const timer = setTimeout(onMarkRead, 2000)
            return () => clearTimeout(timer)
        }
    }, [notification.read, onMarkRead])

    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className={`
        p-3 rounded-lg border transition-colors
        ${notification.read ? 'bg-background' : 'bg-muted/50'}
      `}
        >
            <div className="flex gap-3">
                <div className={`p-2 rounded-full ${colorClass}`}>
                    <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                        <div>
                            <p className="font-medium text-sm">{notification.title}</p>
                            <p className="text-xs text-muted-foreground mt-0.5">
                                {notification.timestamp.toLocaleTimeString()}
                            </p>
                        </div>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6"
                            onClick={onDismiss}
                        >
                            <X className="h-3 w-3" />
                        </Button>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                        {notification.message}
                    </p>
                </div>
            </div>
        </motion.div>
    )
}

interface NotificationCenterProps {
    userId?: number
    variant?: 'popover' | 'sheet'
}

export function NotificationCenter({
    userId,
    variant = 'popover'
}: NotificationCenterProps) {
    const [notifications, setNotifications] = useState<NotificationItem[]>([])
    const [open, setOpen] = useState(false)

    const { notifications: wsNotifications, connected, clearNotifications } = useWebSocket({
        userId,
        onMessage: (msg) => {
            if (['notification', 'alert', 'job_completed', 'job_failed',
                'training_completed', 'analysis_completed', 'export_ready'].includes(msg.event)) {
                setNotifications(prev => [parseNotification(msg), ...prev].slice(0, 50))
            }
        }
    })

    const unreadCount = notifications.filter(n => !n.read).length

    const dismissNotification = (id: string) => {
        setNotifications(prev => prev.filter(n => n.id !== id))
    }

    const markAsRead = (id: string) => {
        setNotifications(prev => prev.map(n =>
            n.id === id ? { ...n, read: true } : n
        ))
    }

    const clearAll = () => {
        setNotifications([])
        clearNotifications()
    }

    const markAllRead = () => {
        setNotifications(prev => prev.map(n => ({ ...n, read: true })))
    }

    const NotificationList = () => (
        <div className="space-y-2">
            <div className="flex items-center justify-between px-1">
                <span className="text-sm font-medium">
                    Notifications
                    {unreadCount > 0 && (
                        <span className="ml-2 text-muted-foreground">({unreadCount} new)</span>
                    )}
                </span>
                <div className="flex gap-1">
                    {unreadCount > 0 && (
                        <Button variant="ghost" size="sm" onClick={markAllRead}>
                            Mark read
                        </Button>
                    )}
                    {notifications.length > 0 && (
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={clearAll}
                        >
                            <Trash2 className="h-4 w-4" />
                        </Button>
                    )}
                </div>
            </div>
            <Separator />
            <ScrollArea className="h-[300px]">
                <AnimatePresence mode="popLayout">
                    {notifications.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                            <BellOff className="h-8 w-8 mb-2 opacity-50" />
                            <p className="text-sm">No notifications</p>
                        </div>
                    ) : (
                        <div className="space-y-2 pr-2">
                            {notifications.map(notification => (
                                <NotificationEntry
                                    key={notification.id}
                                    notification={notification}
                                    onDismiss={() => dismissNotification(notification.id)}
                                    onMarkRead={() => markAsRead(notification.id)}
                                />
                            ))}
                        </div>
                    )}
                </AnimatePresence>
            </ScrollArea>
        </div>
    )

    const TriggerButton = (
        <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-5 w-5" />
            {unreadCount > 0 && (
                <Badge
                    className="absolute -top-1 -right-1 h-5 w-5 p-0 flex items-center justify-center text-xs"
                    variant="destructive"
                >
                    {unreadCount > 9 ? '9+' : unreadCount}
                </Badge>
            )}
            {!connected && (
                <span className="absolute bottom-0 right-0 h-2 w-2 rounded-full bg-yellow-500" />
            )}
        </Button>
    )

    if (variant === 'sheet') {
        return (
            <Sheet open={open} onOpenChange={setOpen}>
                <SheetTrigger asChild>
                    {TriggerButton}
                </SheetTrigger>
                <SheetContent>
                    <SheetHeader>
                        <SheetTitle>Notifications</SheetTitle>
                    </SheetHeader>
                    <div className="mt-4">
                        <NotificationList />
                    </div>
                </SheetContent>
            </Sheet>
        )
    }

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                {TriggerButton}
            </PopoverTrigger>
            <PopoverContent className="w-80 p-3" align="end">
                <NotificationList />
            </PopoverContent>
        </Popover>
    )
}

/**
 * Toast-style notification that appears temporarily
 */
export function NotificationToast() {
    const [visible, setVisible] = useState(false)
    const [notification, setNotification] = useState<NotificationItem | null>(null)

    useWebSocket({
        onMessage: (msg) => {
            if (['job_completed', 'job_failed', 'notification', 'alert'].includes(msg.event)) {
                setNotification(parseNotification(msg))
                setVisible(true)

                // Auto-hide after 5 seconds
                setTimeout(() => setVisible(false), 5000)
            }
        }
    })

    if (!notification) return null

    const Icon = NOTIFICATION_ICONS[notification.type]
    const colorClass = NOTIFICATION_COLORS[notification.type]

    return (
        <AnimatePresence>
            {visible && (
                <motion.div
                    initial={{ opacity: 0, y: -50, x: '-50%' }}
                    animate={{ opacity: 1, y: 0, x: '-50%' }}
                    exit={{ opacity: 0, y: -50, x: '-50%' }}
                    className="fixed top-4 left-1/2 z-[100]"
                >
                    <div className="bg-background border rounded-lg shadow-lg p-4 flex items-start gap-3 min-w-[300px] max-w-md">
                        <div className={`p-2 rounded-full ${colorClass}`}>
                            <Icon className="h-4 w-4" />
                        </div>
                        <div className="flex-1">
                            <p className="font-medium text-sm">{notification.title}</p>
                            <p className="text-sm text-muted-foreground mt-0.5">
                                {notification.message}
                            </p>
                        </div>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6"
                            onClick={() => setVisible(false)}
                        >
                            <X className="h-3 w-3" />
                        </Button>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    )
}

export default NotificationCenter
