"use client";

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    Shield,
    Building2,
    Server,
    Key,
    Activity,
    CheckCircle,
    AlertTriangle,
    Clock,
    RefreshCw,
    ChevronRight,
    Globe,
    Lock,
    FileText
} from 'lucide-react';

interface XRoadStatus {
    instance: string;
    version: string;
    status: string;
    timestamp: string;
    statistics: {
        total_transactions: number;
        organizations_registered: number;
        services_registered: number;
    };
}

interface Organization {
    id: string;
    code: string;
    name: string;
    member_class: string;
    status: string;
    contact_email: string;
    verified_at: string | null;
}

interface Service {
    id: string;
    organization_code: string;
    subsystem_code: string;
    service_code: string;
    title: string;
    status: string;
}

export default function XRoadDashboard() {
    const [status, setStatus] = useState<XRoadStatus | null>(null);
    const [organizations, setOrganizations] = useState<Organization[]>([]);
    const [services, setServices] = useState<Service[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('overview');

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            // Fetch X-Road status
            const statusRes = await fetch('http://localhost:8000/api/v1/xroad/status');
            const statusData = await statusRes.json();
            setStatus(statusData);

            // Fetch organizations
            const orgsRes = await fetch('http://localhost:8000/api/v1/xroad/organizations');
            const orgsData = await orgsRes.json();
            setOrganizations(orgsData.organizations || []);

            // Fetch services
            const servicesRes = await fetch('http://localhost:8000/api/v1/xroad/services');
            const servicesData = await servicesRes.json();
            setServices(servicesData.services || []);
        } catch (error) {
            console.error('Failed to fetch X-Road data:', error);
        } finally {
            setLoading(false);
        }
    };

    const StatCard = ({
        icon: Icon,
        label,
        value,
        color,
        sublabel
    }: {
        icon: any;
        label: string;
        value: string | number;
        color: string;
        sublabel?: string;
    }) => (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50 hover:border-slate-600/50 transition-all duration-300"
        >
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-slate-400 text-sm font-medium mb-1">{label}</p>
                    <h3 className="text-3xl font-bold text-white">{value}</h3>
                    {sublabel && <p className="text-slate-500 text-xs mt-1">{sublabel}</p>}
                </div>
                <div className={`p-3 rounded-xl bg-gradient-to-br ${color}`}>
                    <Icon className="w-6 h-6 text-white" />
                </div>
            </div>
        </motion.div>
    );

    const tabs = [
        { id: 'overview', label: 'Overview', icon: Activity },
        { id: 'organizations', label: 'Organizations', icon: Building2 },
        { id: 'services', label: 'Services', icon: Server },
        { id: 'security', label: 'Security', icon: Shield },
    ];

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
                            <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600">
                                <Globe className="w-8 h-8 text-white" />
                            </div>
                            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                                R-NDIP X-Road
                            </h1>
                        </div>
                        <p className="text-slate-400">Rwanda National Data Intelligence Platform - Secure Data Exchange</p>
                    </div>

                    <div className="flex items-center gap-4">
                        {status && (
                            <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${status.status === 'operational'
                                    ? 'bg-emerald-500/20 text-emerald-400'
                                    : 'bg-amber-500/20 text-amber-400'
                                }`}>
                                {status.status === 'operational' ? (
                                    <CheckCircle className="w-4 h-4" />
                                ) : (
                                    <AlertTriangle className="w-4 h-4" />
                                )}
                                <span className="font-medium capitalize">{status.status}</span>
                            </div>
                        )}
                        <button
                            onClick={fetchData}
                            className="p-3 rounded-xl bg-slate-700/50 hover:bg-slate-600/50 transition-colors"
                        >
                            <RefreshCw className={`w-5 h-5 text-slate-300 ${loading ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                </div>
            </motion.div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <StatCard
                    icon={Building2}
                    label="Organizations"
                    value={status?.statistics.organizations_registered || 0}
                    color="from-blue-500 to-blue-600"
                    sublabel="Registered members"
                />
                <StatCard
                    icon={Server}
                    label="Services"
                    value={status?.statistics.services_registered || 0}
                    color="from-purple-500 to-purple-600"
                    sublabel="Available endpoints"
                />
                <StatCard
                    icon={Activity}
                    label="Transactions"
                    value={status?.statistics.total_transactions || 0}
                    color="from-emerald-500 to-emerald-600"
                    sublabel="Data exchanges"
                />
                <StatCard
                    icon={Shield}
                    label="Instance"
                    value={status?.instance || 'RW'}
                    color="from-amber-500 to-orange-600"
                    sublabel={`v${status?.version || '1.0.0'}`}
                />
            </div>

            {/* Tabs */}
            <div className="flex gap-2 mb-6 p-1 bg-slate-800/50 rounded-xl w-fit">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${activeTab === tab.id
                                ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                                : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                            }`}
                    >
                        <tab.icon className="w-4 h-4" />
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <motion.div
                key={activeTab}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3 }}
            >
                {activeTab === 'overview' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Recent Organizations */}
                        <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold text-white">Recent Organizations</h3>
                                <Building2 className="w-5 h-5 text-slate-500" />
                            </div>
                            <div className="space-y-3">
                                {organizations.slice(0, 5).map((org) => (
                                    <div
                                        key={org.id}
                                        className="flex items-center justify-between p-3 rounded-xl bg-slate-900/50 hover:bg-slate-700/30 transition-colors"
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className={`w-3 h-3 rounded-full ${org.status === 'active' ? 'bg-emerald-400' :
                                                    org.status === 'pending' ? 'bg-amber-400' : 'bg-slate-400'
                                                }`} />
                                            <div>
                                                <p className="font-medium text-white">{org.name}</p>
                                                <p className="text-sm text-slate-500">{org.code}</p>
                                            </div>
                                        </div>
                                        <span className={`text-xs px-2 py-1 rounded-full ${org.member_class === 'GOV' ? 'bg-blue-500/20 text-blue-400' :
                                                org.member_class === 'COM' ? 'bg-purple-500/20 text-purple-400' :
                                                    'bg-slate-500/20 text-slate-400'
                                            }`}>
                                            {org.member_class}
                                        </span>
                                    </div>
                                ))}
                                {organizations.length === 0 && (
                                    <p className="text-slate-500 text-center py-4">No organizations registered yet</p>
                                )}
                            </div>
                        </div>

                        {/* System Info */}
                        <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold text-white">System Information</h3>
                                <FileText className="w-5 h-5 text-slate-500" />
                            </div>
                            <div className="space-y-4">
                                <div className="flex items-center justify-between py-3 border-b border-slate-700/50">
                                    <span className="text-slate-400">Instance ID</span>
                                    <span className="text-white font-mono">{status?.instance || 'RW'}</span>
                                </div>
                                <div className="flex items-center justify-between py-3 border-b border-slate-700/50">
                                    <span className="text-slate-400">Version</span>
                                    <span className="text-white font-mono">{status?.version || '1.0.0'}</span>
                                </div>
                                <div className="flex items-center justify-between py-3 border-b border-slate-700/50">
                                    <span className="text-slate-400">Status</span>
                                    <span className="text-emerald-400 font-medium capitalize">{status?.status || 'Unknown'}</span>
                                </div>
                                <div className="flex items-center justify-between py-3">
                                    <span className="text-slate-400">Last Updated</span>
                                    <span className="text-white text-sm">
                                        {status?.timestamp ? new Date(status.timestamp).toLocaleString() : 'N/A'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'organizations' && (
                    <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-semibold text-white">Registered Organizations</h3>
                            <button className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg text-white font-medium hover:opacity-90 transition-opacity">
                                + Register Organization
                            </button>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="text-left text-slate-400 text-sm border-b border-slate-700/50">
                                        <th className="pb-3 font-medium">Organization</th>
                                        <th className="pb-3 font-medium">Code</th>
                                        <th className="pb-3 font-medium">Class</th>
                                        <th className="pb-3 font-medium">Status</th>
                                        <th className="pb-3 font-medium">Contact</th>
                                        <th className="pb-3 font-medium">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {organizations.map((org) => (
                                        <tr key={org.id} className="border-b border-slate-700/30 hover:bg-slate-700/20">
                                            <td className="py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
                                                        <Building2 className="w-5 h-5 text-blue-400" />
                                                    </div>
                                                    <span className="font-medium text-white">{org.name}</span>
                                                </div>
                                            </td>
                                            <td className="py-4 font-mono text-slate-300">{org.code}</td>
                                            <td className="py-4">
                                                <span className={`px-2 py-1 rounded text-xs font-medium ${org.member_class === 'GOV' ? 'bg-blue-500/20 text-blue-400' :
                                                        org.member_class === 'COM' ? 'bg-purple-500/20 text-purple-400' :
                                                            'bg-slate-500/20 text-slate-400'
                                                    }`}>
                                                    {org.member_class}
                                                </span>
                                            </td>
                                            <td className="py-4">
                                                <span className={`flex items-center gap-1 text-sm ${org.status === 'active' ? 'text-emerald-400' :
                                                        org.status === 'pending' ? 'text-amber-400' :
                                                            'text-slate-400'
                                                    }`}>
                                                    <span className={`w-2 h-2 rounded-full ${org.status === 'active' ? 'bg-emerald-400' :
                                                            org.status === 'pending' ? 'bg-amber-400' :
                                                                'bg-slate-400'
                                                        }`} />
                                                    {org.status}
                                                </span>
                                            </td>
                                            <td className="py-4 text-slate-400 text-sm">{org.contact_email}</td>
                                            <td className="py-4">
                                                <button className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors">
                                                    <ChevronRight className="w-4 h-4 text-slate-400" />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {organizations.length === 0 && (
                                <div className="text-center py-12">
                                    <Building2 className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                                    <p className="text-slate-500">No organizations registered yet</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {activeTab === 'services' && (
                    <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-semibold text-white">Registered Services</h3>
                            <button className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg text-white font-medium hover:opacity-90 transition-opacity">
                                + Register Service
                            </button>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {services.map((service) => (
                                <div
                                    key={service.id}
                                    className="p-4 rounded-xl bg-slate-900/50 border border-slate-700/50 hover:border-slate-600/50 transition-colors"
                                >
                                    <div className="flex items-start justify-between mb-3">
                                        <div className="p-2 rounded-lg bg-purple-500/20">
                                            <Server className="w-5 h-5 text-purple-400" />
                                        </div>
                                        <span className={`text-xs px-2 py-1 rounded-full ${service.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' :
                                                'bg-slate-500/20 text-slate-400'
                                            }`}>
                                            {service.status}
                                        </span>
                                    </div>
                                    <h4 className="font-medium text-white mb-1">{service.title}</h4>
                                    <p className="text-sm text-slate-500 font-mono">{service.service_code}</p>
                                    <div className="mt-3 pt-3 border-t border-slate-700/50">
                                        <p className="text-xs text-slate-500">
                                            {service.organization_code} / {service.subsystem_code}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                        {services.length === 0 && (
                            <div className="text-center py-12">
                                <Server className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                                <p className="text-slate-500">No services registered yet</p>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'security' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold text-white">Security Status</h3>
                                <Lock className="w-5 h-5 text-slate-500" />
                            </div>
                            <div className="space-y-4">
                                <div className="flex items-center gap-3 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                                    <div>
                                        <p className="text-white font-medium">PKI Infrastructure</p>
                                        <p className="text-sm text-slate-400">Root CA active and signing</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                                    <div>
                                        <p className="text-white font-medium">Message Signing</p>
                                        <p className="text-sm text-slate-400">RSA-SHA256 enabled</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                                    <div>
                                        <p className="text-white font-medium">Encryption</p>
                                        <p className="text-sm text-slate-400">AES-256-CBC + RSA-OAEP</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                                    <div>
                                        <p className="text-white font-medium">Audit Logging</p>
                                        <p className="text-sm text-slate-400">Non-repudiation enabled</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold text-white">Certificates</h3>
                                <Key className="w-5 h-5 text-slate-500" />
                            </div>
                            <div className="text-center py-8">
                                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center mx-auto mb-4">
                                    <Key className="w-8 h-8 text-amber-400" />
                                </div>
                                <p className="text-white font-medium mb-2">R-NDIP Root CA</p>
                                <p className="text-sm text-slate-500 mb-4">SHA256-RSA (4096 bit)</p>
                                <div className="flex items-center justify-center gap-2 text-sm text-emerald-400">
                                    <CheckCircle className="w-4 h-4" />
                                    <span>Active and Trusted</span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </motion.div>
        </div>
    );
}
