/**
 * Real-Time Job Progress Component
 * Shows progress bars for running background jobs
 */
"use client"

import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Loader2,
    CheckCircle2,
    XCircle,
    Clock,
    Cpu,
    FileSpreadsheet,
    BarChart3,
    Download
} from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useWebSocket, JobProgress } from '@/hooks/use-websocket'

interface JobProgressTrackerProps {
    userId?: number
    onJobComplete?: (jobId: string, result: any) => void
    showCompleted?: boolean
    maxJobs?: number
}

const JOB_TYPE_CONFIG: Record<string, {
    icon: React.ElementType
    label: string
    color: string
}> = {
    ml_training: { icon: Cpu, label: 'ML Training', color: 'text-purple-500' },
    data_upload: { icon: FileSpreadsheet, label: 'Data Upload', color: 'text-blue-500' },
    data_processing: { icon: Loader2, label: 'Processing', color: 'text-orange-500' },
    analysis: { icon: BarChart3, label: 'Analysis', color: 'text-green-500' },
    export: { icon: Download, label: 'Export', color: 'text-cyan-500' },
    report_generation: { icon: FileSpreadsheet, label: 'Report', color: 'text-pink-500' }
}

function getJobConfig(jobType: string) {
    return JOB_TYPE_CONFIG[jobType] || {
        icon: Clock,
        label: jobType,
        color: 'text-gray-500'
    }
}

function JobProgressItem({ job, onCancel }: { job: JobProgress; onCancel?: () => void }) {
    const config = getJobConfig(job.jobType)
    const Icon = config.icon
    const isComplete = job.progress >= 100
    const hasFailed = !!job.error

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, x: -100 }}
            className="relative"
        >
            <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50 border">
                {/* Icon */}
                <div className={`mt-0.5 ${config.color}`}>
                    {isComplete ? (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                    ) : hasFailed ? (
                        <XCircle className="h-5 w-5 text-red-500" />
                    ) : (
                        <Icon className="h-5 w-5 animate-pulse" />
                    )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                        <span className="font-medium text-sm truncate">
                            {config.label}
                        </span>
                        <Badge
                            variant={isComplete ? "default" : hasFailed ? "destructive" : "secondary"}
                            className="text-xs"
                        >
                            {isComplete ? 'Complete' : hasFailed ? 'Failed' : `${job.progress}%`}
                        </Badge>
                    </div>

                    {/* Progress bar */}
                    {!isComplete && !hasFailed && (
                        <div className="mt-2">
                            <Progress value={job.progress} className="h-1.5" />
                        </div>
                    )}

                    {/* Message */}
                    {job.message && (
                        <p className="text-xs text-muted-foreground mt-1 truncate">
                            {job.message}
                        </p>
                    )}

                    {/* Error */}
                    {job.error && (
                        <p className="text-xs text-red-500 mt-1 truncate">
                            {job.error}
                        </p>
                    )}
                </div>

                {/* Cancel button */}
                {!isComplete && !hasFailed && onCancel && (
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2 text-xs"
                        onClick={onCancel}
                    >
                        Cancel
                    </Button>
                )}
            </div>
        </motion.div>
    )
}

export function JobProgressTracker({
    userId,
    onJobComplete,
    showCompleted = true,
    maxJobs = 5
}: JobProgressTrackerProps) {
    const { jobProgress, connected } = useWebSocket({ userId })

    const jobs = Object.values(jobProgress)
        .filter(job => showCompleted || job.progress < 100)
        .slice(0, maxJobs)

    if (jobs.length === 0) {
        return null
    }

    return (
        <Card className="border-dashed">
            <CardHeader className="py-3">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Running Tasks
                    {!connected && (
                        <Badge variant="outline" className="text-xs text-yellow-500">
                            Offline
                        </Badge>
                    )}
                </CardTitle>
            </CardHeader>
            <CardContent className="py-2">
                <div className="space-y-2">
                    <AnimatePresence mode="popLayout">
                        {jobs.map(job => (
                            <JobProgressItem key={job.jobId} job={job} />
                        ))}
                    </AnimatePresence>
                </div>
            </CardContent>
        </Card>
    )
}

/**
 * Floating progress indicator for minimal UI
 */
export function FloatingJobProgress() {
    const { jobProgress, connected } = useWebSocket()

    const activeJobs = Object.values(jobProgress).filter(j => j.progress < 100 && !j.error)

    if (activeJobs.length === 0) return null

    const currentJob = activeJobs[0]
    const config = getJobConfig(currentJob.jobType)
    const Icon = config.icon

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            className="fixed bottom-20 right-4 z-50"
        >
            <div className="bg-background border rounded-full px-4 py-2 shadow-lg flex items-center gap-3">
                <Icon className={`h-4 w-4 ${config.color} animate-pulse`} />
                <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{config.label}</span>
                    <div className="w-20">
                        <Progress value={currentJob.progress} className="h-1.5" />
                    </div>
                    <span className="text-xs text-muted-foreground">
                        {currentJob.progress}%
                    </span>
                </div>
                {activeJobs.length > 1 && (
                    <Badge variant="secondary" className="text-xs">
                        +{activeJobs.length - 1}
                    </Badge>
                )}
            </div>
        </motion.div>
    )
}

/**
 * Simple inline progress for embedding in other components
 */
export function InlineJobProgress({
    jobId,
    showLabel = true
}: {
    jobId: string
    showLabel?: boolean
}) {
    const { jobProgress } = useWebSocket()
    const job = jobProgress[jobId]

    if (!job) return null

    const isComplete = job.progress >= 100
    const hasFailed = !!job.error

    return (
        <div className="space-y-1">
            {showLabel && (
                <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">
                        {job.message || getJobConfig(job.jobType).label}
                    </span>
                    <span className={hasFailed ? 'text-red-500' : ''}>
                        {hasFailed ? 'Failed' : `${job.progress}%`}
                    </span>
                </div>
            )}
            <Progress
                value={job.progress}
                className={`h-2 ${hasFailed ? 'bg-destructive/20' : ''}`}
            />
        </div>
    )
}

export default JobProgressTracker
