"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Zap,
    Activity,
    AlertTriangle,
    CheckCircle,
    Clock,
    Server,
    BarChart3,
    Shield,
    RefreshCw,
    Settings,
    TrendingUp,
    Loader2,
    ChevronRight,
    AlertCircle
} from 'lucide-react';

interface GatewayStatus {
    status: string;
    timestamp: string;
    circuits: {
        total: number;
        open: number;
        open_services: string[];
    };
    rate_limiting: {
        organizations_tracked: number;
    };
}

interface CircuitStatus {
    service: string;
    state: string;
    failure_count: number;
    success_count: number;
    last_failure: string | null;
    last_state_change: string;
    last_error: string | null;
}

interface RateLimitUsage {
    organization_code: string;
    requests_in_window: number;
    window_minutes: number;
    limit_per_minute: number;
    tokens_available: number;
    bucket_capacity: number;
}

export default function GatewayDashboard() {
    const [status, setStatus] = useState<GatewayStatus | null>(null);
    const [circuits, setCircuits] = useState<Record<string, any>>({});
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('overview');

    useEffect(() => {
        fetchGatewayData();
        const interval = setInterval(fetchGatewayData, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const fetchGatewayData = async () => {
        try {
            const [statusRes, circuitsRes] = await Promise.all([
                fetch('http://localhost:8000/api/v1/gateway/status'),
                fetch('http://localhost:8000/api/v1/gateway/circuits'),
            ]);

            setStatus(await statusRes.json());
            const circuitData = await circuitsRes.json();
            setCircuits(circuitData.circuits || {});
        } catch (error) {
            console.error('Failed to fetch gateway data:', error);
        } finally {
            setLoading(false);
        }
    };

    const getCircuitColor = (state: string) => {
        switch (state) {
            case 'closed': return 'from-emerald-500 to-green-600';
            case 'open': return 'from-red-500 to-rose-600';
            case 'half_open': return 'from-amber-500 to-orange-600';
            default: return 'from-slate-500 to-slate-600';
        }
    };

    const getCircuitIcon = (state: string) => {
        switch (state) {
            case 'closed': return CheckCircle;
            case 'open': return AlertTriangle;
            case 'half_open': return Clock;
            default: return AlertCircle;
        }
    };

    const StatCard = ({
        icon: Icon,
        label,
        value,
        status: cardStatus,
        color
    }: {
        icon: any;
        label: string;
        value: string | number;
        status?: 'healthy' | 'warning' | 'error';
        color: string;
    }) => (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50"
        >
            <div className="flex items-start justify-between">
                <div className={`p-3 rounded-xl bg-gradient-to-br ${color}`}>
                    <Icon className="w-6 h-6 text-white" />
                </div>
                {cardStatus && (
                    <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs ${cardStatus === 'healthy' ? 'bg-emerald-500/20 text-emerald-400' :
                            cardStatus === 'warning' ? 'bg-amber-500/20 text-amber-400' :
                                'bg-red-500/20 text-red-400'
                        }`}>
                        <span className="w-1.5 h-1.5 rounded-full animate-pulse"
                            style={{ backgroundColor: cardStatus === 'healthy' ? '#34d399' : cardStatus === 'warning' ? '#fbbf24' : '#f87171' }}
                        />
                        {cardStatus}
                    </div>
                )}
            </div>
            <div className="mt-4">
                <p className="text-3xl font-bold text-white">{value}</p>
                <p className="text-sm text-slate-400 mt-1">{label}</p>
            </div>
        </motion.div>
    );

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-8"
            >
                <div className="flex items-center justify-between">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600">
                                <Zap className="w-8 h-8 text-white" />
                            </div>
                            <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400 bg-clip-text text-transparent">
                                API Gateway
                            </h1>
                        </div>
                        <p className="text-slate-400">Monitor service routing, rate limiting, and circuit breakers</p>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className={`flex items-center gap-2 px-4 py-2 rounded-xl ${status?.status === 'operational'
                                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                            }`}>
                            <span className={`w-2 h-2 rounded-full animate-pulse ${status?.status === 'operational' ? 'bg-emerald-400' : 'bg-amber-400'
                                }`} />
                            {status?.status === 'operational' ? 'Operational' : 'Degraded'}
                        </div>

                        <button
                            onClick={fetchGatewayData}
                            className="flex items-center gap-2 px-4 py-2 bg-slate-700/50 hover:bg-slate-700 rounded-xl text-white transition-colors"
                        >
                            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                            Refresh
                        </button>
                    </div>
                </div>
            </motion.div>

            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
                </div>
            ) : (
                <div className="space-y-8">
                    {/* Stats Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <StatCard
                            icon={Activity}
                            label="Gateway Status"
                            value={status?.status === 'operational' ? 'Healthy' : 'Degraded'}
                            status={status?.status === 'operational' ? 'healthy' : 'warning'}
                            color="from-emerald-500 to-teal-600"
                        />
                        <StatCard
                            icon={Server}
                            label="Circuit Breakers"
                            value={status?.circuits.total || 0}
                            status={status?.circuits.open === 0 ? 'healthy' : 'warning'}
                            color="from-purple-500 to-indigo-600"
                        />
                        <StatCard
                            icon={AlertTriangle}
                            label="Open Circuits"
                            value={status?.circuits.open || 0}
                            color="from-red-500 to-rose-600"
                        />
                        <StatCard
                            icon={BarChart3}
                            label="Orgs Tracked"
                            value={status?.rate_limiting.organizations_tracked || 0}
                            color="from-cyan-500 to-blue-600"
                        />
                    </div>

                    {/* Circuit Breakers */}
                    <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-semibold text-white">Circuit Breakers</h2>
                            <div className="flex items-center gap-4">
                                <div className="flex items-center gap-2 text-sm text-slate-400">
                                    <span className="w-3 h-3 rounded-full bg-emerald-500" /> Closed
                                </div>
                                <div className="flex items-center gap-2 text-sm text-slate-400">
                                    <span className="w-3 h-3 rounded-full bg-amber-500" /> Half-Open
                                </div>
                                <div className="flex items-center gap-2 text-sm text-slate-400">
                                    <span className="w-3 h-3 rounded-full bg-red-500" /> Open
                                </div>
                            </div>
                        </div>

                        {Object.keys(circuits).length === 0 ? (
                            <div className="text-center py-12">
                                <Shield className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                                <h3 className="text-lg font-semibold text-white mb-2">No Circuit Breakers Active</h3>
                                <p className="text-slate-500">Circuit breakers will appear when services start processing requests.</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {Object.entries(circuits).map(([service, data]: [string, any]) => {
                                    const Icon = getCircuitIcon(data.state);
                                    return (
                                        <motion.div
                                            key={service}
                                            initial={{ opacity: 0, scale: 0.95 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50"
                                        >
                                            <div className="flex items-center justify-between mb-3">
                                                <div className="flex items-center gap-3">
                                                    <div className={`p-2 rounded-lg bg-gradient-to-br ${getCircuitColor(data.state)}`}>
                                                        <Icon className="w-4 h-4 text-white" />
                                                    </div>
                                                    <span className="text-white font-medium truncate">{service}</span>
                                                </div>
                                                <span className={`text-xs px-2 py-1 rounded-full capitalize ${data.state === 'closed' ? 'bg-emerald-500/20 text-emerald-400' :
                                                        data.state === 'open' ? 'bg-red-500/20 text-red-400' :
                                                            'bg-amber-500/20 text-amber-400'
                                                    }`}>
                                                    {data.state}
                                                </span>
                                            </div>
                                            <div className="grid grid-cols-2 gap-2 text-sm">
                                                <div className="bg-slate-700/30 rounded-lg p-2">
                                                    <p className="text-slate-400 text-xs">Failures</p>
                                                    <p className="text-white font-medium">{data.failure_count}</p>
                                                </div>
                                                <div className="bg-slate-700/30 rounded-lg p-2">
                                                    <p className="text-slate-400 text-xs">Last Failure</p>
                                                    <p className="text-white font-medium truncate">
                                                        {data.last_failure ? new Date(data.last_failure).toLocaleTimeString() : 'Never'}
                                                    </p>
                                                </div>
                                            </div>
                                        </motion.div>
                                    );
                                })}
                            </div>
                        )}
                    </div>

                    {/* Rate Limiting Info */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
                            <h2 className="text-xl font-semibold text-white mb-4">Rate Limiting</h2>
                            <div className="space-y-4">
                                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-700/30">
                                    <div>
                                        <p className="text-white font-medium">Default Org Limit</p>
                                        <p className="text-sm text-slate-400">Requests per minute per organization</p>
                                    </div>
                                    <span className="text-2xl font-bold text-cyan-400">1000</span>
                                </div>
                                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-700/30">
                                    <div>
                                        <p className="text-white font-medium">Default Service Limit</p>
                                        <p className="text-sm text-slate-400">Requests per minute per service</p>
                                    </div>
                                    <span className="text-2xl font-bold text-purple-400">100</span>
                                </div>
                                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-700/30">
                                    <div>
                                        <p className="text-white font-medium">Burst Multiplier</p>
                                        <p className="text-sm text-slate-400">Token bucket capacity multiplier</p>
                                    </div>
                                    <span className="text-2xl font-bold text-emerald-400">2x</span>
                                </div>
                            </div>
                        </div>

                        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
                            <h2 className="text-xl font-semibold text-white mb-4">Gateway Configuration</h2>
                            <div className="space-y-4">
                                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-700/30">
                                    <div className="flex items-center gap-3">
                                        <CheckCircle className="w-5 h-5 text-emerald-400" />
                                        <span className="text-white">Request Signing</span>
                                    </div>
                                    <span className="text-emerald-400 text-sm">Enabled</span>
                                </div>
                                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-700/30">
                                    <div className="flex items-center gap-3">
                                        <CheckCircle className="w-5 h-5 text-emerald-400" />
                                        <span className="text-white">Access Control</span>
                                    </div>
                                    <span className="text-emerald-400 text-sm">Enforced</span>
                                </div>
                                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-700/30">
                                    <div className="flex items-center gap-3">
                                        <CheckCircle className="w-5 h-5 text-emerald-400" />
                                        <span className="text-white">Audit Logging</span>
                                    </div>
                                    <span className="text-emerald-400 text-sm">Active</span>
                                </div>
                                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-700/30">
                                    <div className="flex items-center gap-3">
                                        <Settings className="w-5 h-5 text-slate-400" />
                                        <span className="text-white">Default Timeout</span>
                                    </div>
                                    <span className="text-slate-400 text-sm">30s</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
