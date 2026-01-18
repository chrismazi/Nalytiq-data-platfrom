"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Shield,
    Users,
    Lock,
    AlertTriangle,
    CheckCircle,
    Key,
    FileText,
    Eye,
    UserCog,
    Plus,
    Search,
    RefreshCw,
    ChevronRight,
    Settings,
    Activity,
    TrendingUp,
    AlertCircle,
    Loader2
} from 'lucide-react';

interface RBACStats {
    total_users_with_roles: number;
    total_custom_roles: number;
    role_assignments: Record<string, number>;
    access_decisions_logged: number;
}

interface ComplianceStats {
    total_consent_records: number;
    total_subjects_with_consent: number;
    datasets_with_retention_policy: number;
    processing_records: number;
    total_breaches: number;
    open_breaches: number;
}

interface SecurityPolicies {
    password_policy: Record<string, any>;
    session_policy: Record<string, any>;
    api_policy: Record<string, any>;
    blocked_ips_count: number;
    active_api_keys: number;
}

interface Role {
    type: string;
    permissions: string[];
}

export default function SecurityDashboard() {
    const [activeTab, setActiveTab] = useState('overview');
    const [rbacStats, setRbacStats] = useState<RBACStats | null>(null);
    const [complianceStats, setComplianceStats] = useState<ComplianceStats | null>(null);
    const [policies, setPolicies] = useState<SecurityPolicies | null>(null);
    const [roles, setRoles] = useState<Record<string, Role>>({});
    const [loading, setLoading] = useState(true);
    const [showRoleModal, setShowRoleModal] = useState(false);
    const [selectedRole, setSelectedRole] = useState<string | null>(null);

    useEffect(() => {
        fetchSecurityData();
    }, []);

    const fetchSecurityData = async () => {
        setLoading(true);
        try {
            const [rbacRes, complianceRes, policiesRes, rolesRes] = await Promise.all([
                fetch('http://localhost:8000/api/v1/security/rbac/statistics'),
                fetch('http://localhost:8000/api/v1/security/compliance/statistics'),
                fetch('http://localhost:8000/api/v1/security/policies'),
                fetch('http://localhost:8000/api/v1/security/rbac/roles'),
            ]);

            setRbacStats(await rbacRes.json());
            setComplianceStats(await complianceRes.json());
            setPolicies(await policiesRes.json());
            setRoles(await rolesRes.json());
        } catch (error) {
            console.error('Failed to fetch security data:', error);
        } finally {
            setLoading(false);
        }
    };

    const tabs = [
        { id: 'overview', label: 'Overview', icon: Activity },
        { id: 'roles', label: 'Roles & Permissions', icon: Users },
        { id: 'compliance', label: 'Compliance', icon: FileText },
        { id: 'policies', label: 'Security Policies', icon: Settings },
    ];

    const StatCard = ({
        icon: Icon,
        label,
        value,
        subtext,
        color,
        trend
    }: {
        icon: any;
        label: string;
        value: string | number;
        subtext?: string;
        color: string;
        trend?: 'up' | 'down' | 'neutral';
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
                {trend && (
                    <div className={`flex items-center gap-1 text-sm ${trend === 'up' ? 'text-emerald-400' : trend === 'down' ? 'text-red-400' : 'text-slate-400'
                        }`}>
                        <TrendingUp className={`w-4 h-4 ${trend === 'down' ? 'rotate-180' : ''}`} />
                    </div>
                )}
            </div>
            <div className="mt-4">
                <p className="text-3xl font-bold text-white">{value}</p>
                <p className="text-sm text-slate-400 mt-1">{label}</p>
                {subtext && <p className="text-xs text-slate-500 mt-1">{subtext}</p>}
            </div>
        </motion.div>
    );

    const RoleCard = ({ roleName, role }: { roleName: string; role: Role }) => (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            whileHover={{ scale: 1.02 }}
            onClick={() => { setSelectedRole(roleName); setShowRoleModal(true); }}
            className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl rounded-xl p-5 border border-slate-700/50 cursor-pointer hover:border-purple-500/50 transition-all"
        >
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${role.type === 'built_in'
                            ? 'bg-gradient-to-br from-purple-500 to-indigo-600'
                            : 'bg-gradient-to-br from-amber-500 to-orange-600'
                        }`}>
                        <UserCog className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h3 className="text-white font-semibold capitalize">{roleName.replace(/_/g, ' ')}</h3>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${role.type === 'built_in'
                                ? 'bg-purple-500/20 text-purple-400'
                                : 'bg-amber-500/20 text-amber-400'
                            }`}>
                            {role.type === 'built_in' ? 'Built-in' : 'Custom'}
                        </span>
                    </div>
                </div>
                <ChevronRight className="w-5 h-5 text-slate-500" />
            </div>
            <div className="flex flex-wrap gap-1.5 mt-3">
                {role.permissions.slice(0, 4).map((perm) => (
                    <span key={perm} className="text-xs px-2 py-1 rounded-md bg-slate-700/50 text-slate-300">
                        {perm.split(':')[0]}
                    </span>
                ))}
                {role.permissions.length > 4 && (
                    <span className="text-xs px-2 py-1 rounded-md bg-slate-700/50 text-slate-400">
                        +{role.permissions.length - 4} more
                    </span>
                )}
            </div>
        </motion.div>
    );

    const PolicySection = ({ title, policy, icon: Icon }: { title: string; policy: Record<string, any>; icon: any }) => (
        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl rounded-xl p-6 border border-slate-700/50">
            <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600">
                    <Icon className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-white">{title}</h3>
            </div>
            <div className="space-y-3">
                {Object.entries(policy).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between py-2 border-b border-slate-700/30 last:border-0">
                        <span className="text-sm text-slate-400 capitalize">{key.replace(/_/g, ' ')}</span>
                        <span className="text-sm text-white font-medium">
                            {typeof value === 'boolean' ? (
                                value ? (
                                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                                ) : (
                                    <AlertCircle className="w-4 h-4 text-slate-500" />
                                )
                            ) : Array.isArray(value) ? (
                                value.join(', ')
                            ) : (
                                String(value)
                            )}
                        </span>
                    </div>
                ))}
            </div>
        </div>
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
                            <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600">
                                <Shield className="w-8 h-8 text-white" />
                            </div>
                            <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400 bg-clip-text text-transparent">
                                Security & Compliance
                            </h1>
                        </div>
                        <p className="text-slate-400">Manage roles, permissions, privacy, and regulatory compliance</p>
                    </div>

                    <button
                        onClick={fetchSecurityData}
                        className="flex items-center gap-2 px-4 py-2 bg-slate-700/50 hover:bg-slate-700 rounded-xl text-white transition-colors"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                </div>
            </motion.div>

            {/* Tabs */}
            <div className="flex gap-2 mb-8 overflow-x-auto pb-2">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium transition-all whitespace-nowrap ${activeTab === tab.id
                                ? 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white'
                                : 'bg-slate-800/50 text-slate-400 hover:text-white hover:bg-slate-700/50'
                            }`}
                    >
                        <tab.icon className="w-4 h-4" />
                        {tab.label}
                    </button>
                ))}
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
                </div>
            ) : (
                <>
                    {/* Overview Tab */}
                    {activeTab === 'overview' && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="space-y-8"
                        >
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                <StatCard
                                    icon={Users}
                                    label="Users with Roles"
                                    value={rbacStats?.total_users_with_roles || 0}
                                    color="from-purple-500 to-indigo-600"
                                    trend="up"
                                />
                                <StatCard
                                    icon={Key}
                                    label="Active API Keys"
                                    value={policies?.active_api_keys || 0}
                                    color="from-cyan-500 to-blue-600"
                                />
                                <StatCard
                                    icon={FileText}
                                    label="Consent Records"
                                    value={complianceStats?.total_consent_records || 0}
                                    color="from-emerald-500 to-teal-600"
                                />
                                <StatCard
                                    icon={AlertTriangle}
                                    label="Open Breaches"
                                    value={complianceStats?.open_breaches || 0}
                                    subtext={complianceStats?.open_breaches === 0 ? 'All clear!' : 'Requires attention'}
                                    color={complianceStats?.open_breaches === 0 ? 'from-emerald-500 to-green-600' : 'from-red-500 to-rose-600'}
                                />
                            </div>

                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {/* Role Distribution */}
                                <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
                                    <h3 className="text-lg font-semibold text-white mb-4">Role Distribution</h3>
                                    <div className="space-y-3">
                                        {Object.entries(rbacStats?.role_assignments || {}).slice(0, 6).map(([role, count]) => (
                                            <div key={role} className="flex items-center gap-4">
                                                <div className="flex-1">
                                                    <div className="flex items-center justify-between mb-1">
                                                        <span className="text-sm text-slate-300 capitalize">{role.replace(/_/g, ' ')}</span>
                                                        <span className="text-sm text-slate-400">{count}</span>
                                                    </div>
                                                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                                                        <motion.div
                                                            initial={{ width: 0 }}
                                                            animate={{ width: `${Math.min((count as number / 10) * 100, 100)}%` }}
                                                            className="h-full bg-gradient-to-r from-purple-500 to-indigo-600 rounded-full"
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Security Status */}
                                <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
                                    <h3 className="text-lg font-semibold text-white mb-4">Security Status</h3>
                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
                                            <div className="flex items-center gap-3">
                                                <CheckCircle className="w-5 h-5 text-emerald-400" />
                                                <span className="text-white">Password Policy</span>
                                            </div>
                                            <span className="text-emerald-400 text-sm">Active</span>
                                        </div>
                                        <div className="flex items-center justify-between p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
                                            <div className="flex items-center gap-3">
                                                <CheckCircle className="w-5 h-5 text-emerald-400" />
                                                <span className="text-white">Session Security</span>
                                            </div>
                                            <span className="text-emerald-400 text-sm">Enforced</span>
                                        </div>
                                        <div className="flex items-center justify-between p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
                                            <div className="flex items-center gap-3">
                                                <CheckCircle className="w-5 h-5 text-emerald-400" />
                                                <span className="text-white">API Rate Limiting</span>
                                            </div>
                                            <span className="text-emerald-400 text-sm">Enabled</span>
                                        </div>
                                        <div className="flex items-center justify-between p-3 rounded-xl bg-slate-700/30 border border-slate-600/30">
                                            <div className="flex items-center gap-3">
                                                <Lock className="w-5 h-5 text-slate-400" />
                                                <span className="text-white">Blocked IPs</span>
                                            </div>
                                            <span className="text-slate-400 text-sm">{policies?.blocked_ips_count || 0}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {/* Roles Tab */}
                    {activeTab === 'roles' && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="space-y-6"
                        >
                            <div className="flex items-center justify-between">
                                <h2 className="text-xl font-semibold text-white">
                                    All Roles ({Object.keys(roles).length})
                                </h2>
                                <button className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-xl text-white font-medium hover:opacity-90 transition-opacity">
                                    <Plus className="w-4 h-4" />
                                    Create Custom Role
                                </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {Object.entries(roles).map(([roleName, role]) => (
                                    <RoleCard key={roleName} roleName={roleName} role={role} />
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {/* Compliance Tab */}
                    {activeTab === 'compliance' && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="space-y-6"
                        >
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                <StatCard
                                    icon={FileText}
                                    label="Consent Records"
                                    value={complianceStats?.total_consent_records || 0}
                                    color="from-blue-500 to-indigo-600"
                                />
                                <StatCard
                                    icon={Users}
                                    label="Subjects with Consent"
                                    value={complianceStats?.total_subjects_with_consent || 0}
                                    color="from-purple-500 to-pink-600"
                                />
                                <StatCard
                                    icon={Activity}
                                    label="Processing Records"
                                    value={complianceStats?.processing_records || 0}
                                    color="from-emerald-500 to-teal-600"
                                />
                            </div>

                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
                                    <h3 className="text-lg font-semibold text-white mb-4">Breach Status</h3>
                                    {complianceStats?.open_breaches === 0 ? (
                                        <div className="flex flex-col items-center justify-center py-8">
                                            <div className="p-4 rounded-full bg-emerald-500/20 mb-4">
                                                <CheckCircle className="w-12 h-12 text-emerald-400" />
                                            </div>
                                            <h4 className="text-xl font-semibold text-white mb-2">No Open Breaches</h4>
                                            <p className="text-slate-400 text-center">Your organization is in good standing with no active data breach incidents.</p>
                                        </div>
                                    ) : (
                                        <div className="flex flex-col items-center justify-center py-8">
                                            <div className="p-4 rounded-full bg-red-500/20 mb-4">
                                                <AlertTriangle className="w-12 h-12 text-red-400" />
                                            </div>
                                            <h4 className="text-xl font-semibold text-white mb-2">{complianceStats?.open_breaches} Open Breaches</h4>
                                            <p className="text-red-400 text-center">Immediate attention required. Review and respond within 72 hours.</p>
                                        </div>
                                    )}
                                </div>

                                <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
                                    <h3 className="text-lg font-semibold text-white mb-4">Retention Policies</h3>
                                    <div className="space-y-3">
                                        <div className="p-4 rounded-xl bg-slate-700/30">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-white font-medium">Datasets with Policy</span>
                                                <span className="text-2xl font-bold text-white">{complianceStats?.datasets_with_retention_policy || 0}</span>
                                            </div>
                                            <p className="text-sm text-slate-400">Data retention policies configured</p>
                                        </div>
                                        <button className="w-full py-3 rounded-xl bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 transition-colors">
                                            Configure Retention Policy
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {/* Policies Tab */}
                    {activeTab === 'policies' && policies && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
                        >
                            <PolicySection title="Password Policy" policy={policies.password_policy} icon={Lock} />
                            <PolicySection title="Session Policy" policy={policies.session_policy} icon={Users} />
                            <PolicySection title="API Policy" policy={policies.api_policy} icon={Key} />

                            <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl rounded-xl p-6 border border-slate-700/50">
                                <div className="flex items-center gap-3 mb-4">
                                    <div className="p-2 rounded-lg bg-gradient-to-br from-red-500 to-rose-600">
                                        <AlertTriangle className="w-5 h-5 text-white" />
                                    </div>
                                    <h3 className="text-lg font-semibold text-white">IP Blocking</h3>
                                </div>
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between p-4 rounded-xl bg-slate-700/30">
                                        <span className="text-white">Currently Blocked</span>
                                        <span className="text-2xl font-bold text-white">{policies.blocked_ips_count}</span>
                                    </div>
                                    <button className="w-full py-3 rounded-xl bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors">
                                        Manage Blocked IPs
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </>
            )}

            {/* Role Detail Modal */}
            <AnimatePresence>
                {showRoleModal && selectedRole && roles[selectedRole] && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                        onClick={() => setShowRoleModal(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            onClick={(e) => e.stopPropagation()}
                            className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl border border-slate-700/50 w-full max-w-2xl max-h-[80vh] overflow-y-auto"
                        >
                            <div className="p-6 border-b border-slate-700/50">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className={`p-3 rounded-xl ${roles[selectedRole].type === 'built_in'
                                                ? 'bg-gradient-to-br from-purple-500 to-indigo-600'
                                                : 'bg-gradient-to-br from-amber-500 to-orange-600'
                                            }`}>
                                            <UserCog className="w-6 h-6 text-white" />
                                        </div>
                                        <div>
                                            <h2 className="text-2xl font-bold text-white capitalize">{selectedRole.replace(/_/g, ' ')}</h2>
                                            <span className={`text-sm ${roles[selectedRole].type === 'built_in' ? 'text-purple-400' : 'text-amber-400'
                                                }`}>
                                                {roles[selectedRole].type === 'built_in' ? 'Built-in Role' : 'Custom Role'}
                                            </span>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => setShowRoleModal(false)}
                                        className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors text-slate-400"
                                    >
                                        ✕
                                    </button>
                                </div>
                            </div>

                            <div className="p-6">
                                <h3 className="text-sm font-medium text-slate-400 mb-3">
                                    Permissions ({roles[selectedRole].permissions.length})
                                </h3>
                                <div className="grid grid-cols-2 gap-2">
                                    {roles[selectedRole].permissions.map((perm) => (
                                        <div key={perm} className="flex items-center gap-2 p-2 rounded-lg bg-slate-700/30">
                                            <CheckCircle className="w-4 h-4 text-emerald-400" />
                                            <span className="text-sm text-white">{perm}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
