"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Database,
    Search,
    Filter,
    Share2,
    Lock,
    Globe,
    Clock,
    Download,
    Eye,
    ChevronRight,
    Building2,
    BarChart3,
    FileSpreadsheet,
    Users,
    CheckCircle,
    AlertCircle,
    Loader2,
    Plus
} from 'lucide-react';

interface Dataset {
    id: string;
    name: string;
    description: string;
    organization_code: string;
    dataset_type: string;
    access_level: string;
    tags: string[];
    statistics: {
        row_count: number | null;
        column_count: number | null;
    };
    created_at: string;
    download_count: number;
    query_count: number;
}

interface CatalogStats {
    total_datasets: number;
    by_type: Record<string, number>;
    by_access_level: Record<string, number>;
    by_organization: Record<string, number>;
    total_downloads: number;
    total_queries: number;
}

const typeIcons: Record<string, any> = {
    census: Users,
    statistical: BarChart3,
    survey: FileSpreadsheet,
    administrative: Database,
    time_series: BarChart3,
    aggregate: BarChart3,
    geospatial: Globe,
    microdata: Database,
};

const typeColors: Record<string, string> = {
    census: 'from-blue-500 to-indigo-600',
    statistical: 'from-purple-500 to-pink-600',
    survey: 'from-emerald-500 to-teal-600',
    administrative: 'from-amber-500 to-orange-600',
    time_series: 'from-cyan-500 to-blue-600',
    aggregate: 'from-violet-500 to-purple-600',
    geospatial: 'from-green-500 to-emerald-600',
    microdata: 'from-rose-500 to-red-600',
};

export default function FederationPage() {
    const [datasets, setDatasets] = useState<Dataset[]>([]);
    const [stats, setStats] = useState<CatalogStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedType, setSelectedType] = useState<string | null>(null);
    const [selectedAccess, setSelectedAccess] = useState<string | null>(null);
    const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);

    useEffect(() => {
        fetchData();
    }, [searchQuery, selectedType, selectedAccess]);

    const fetchData = async () => {
        setLoading(true);
        try {
            // Build query params
            const params = new URLSearchParams();
            if (searchQuery) params.append('query', searchQuery);
            if (selectedType) params.append('dataset_type', selectedType);
            if (selectedAccess) params.append('access_level', selectedAccess);

            const [datasetsRes, statsRes] = await Promise.all([
                fetch(`http://localhost:8000/api/v1/federation/catalog/datasets?${params.toString()}`),
                fetch('http://localhost:8000/api/v1/federation/catalog/statistics'),
            ]);

            const datasetsData = await datasetsRes.json();
            const statsData = await statsRes.json();

            setDatasets(datasetsData.datasets || []);
            setStats(statsData);
        } catch (error) {
            console.error('Failed to fetch data:', error);
        } finally {
            setLoading(false);
        }
    };

    const DatasetCard = ({ dataset }: { dataset: Dataset }) => {
        const Icon = typeIcons[dataset.dataset_type] || Database;
        const gradientColor = typeColors[dataset.dataset_type] || 'from-gray-500 to-slate-600';

        return (
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                whileHover={{ y: -4 }}
                onClick={() => setSelectedDataset(dataset)}
                className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50 hover:border-slate-600/50 transition-all duration-300 cursor-pointer group"
            >
                <div className="flex items-start justify-between mb-4">
                    <div className={`p-3 rounded-xl bg-gradient-to-br ${gradientColor}`}>
                        <Icon className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex items-center gap-2">
                        {dataset.access_level === 'public' ? (
                            <span className="flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-emerald-500/20 text-emerald-400">
                                <Globe className="w-3 h-3" />
                                Public
                            </span>
                        ) : dataset.access_level === 'restricted' ? (
                            <span className="flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-amber-500/20 text-amber-400">
                                <Lock className="w-3 h-3" />
                                Restricted
                            </span>
                        ) : (
                            <span className="flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-red-500/20 text-red-400">
                                <Lock className="w-3 h-3" />
                                Internal
                            </span>
                        )}
                    </div>
                </div>

                <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-blue-400 transition-colors">
                    {dataset.name}
                </h3>
                <p className="text-sm text-slate-400 line-clamp-2 mb-4">
                    {dataset.description}
                </p>

                <div className="flex flex-wrap gap-2 mb-4">
                    {dataset.tags?.slice(0, 3).map((tag) => (
                        <span key={tag} className="text-xs px-2 py-1 rounded-md bg-slate-700/50 text-slate-300">
                            {tag}
                        </span>
                    ))}
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-slate-700/50">
                    <div className="flex items-center gap-4 text-sm text-slate-500">
                        <span className="flex items-center gap-1">
                            <Download className="w-3 h-3" />
                            {dataset.download_count || 0}
                        </span>
                        <span className="flex items-center gap-1">
                            <Eye className="w-3 h-3" />
                            {dataset.query_count || 0}
                        </span>
                    </div>
                    <div className="flex items-center gap-1 text-sm text-slate-500">
                        {dataset.statistics?.row_count && (
                            <span>{(dataset.statistics.row_count / 1000000).toFixed(1)}M rows</span>
                        )}
                    </div>
                </div>
            </motion.div>
        );
    };

    const StatCard = ({
        icon: Icon,
        label,
        value,
        color
    }: {
        icon: any;
        label: string;
        value: string | number;
        color: string;
    }) => (
        <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl rounded-xl p-5 border border-slate-700/50"
        >
            <div className="flex items-center gap-4">
                <div className={`p-3 rounded-xl bg-gradient-to-br ${color}`}>
                    <Icon className="w-5 h-5 text-white" />
                </div>
                <div>
                    <p className="text-2xl font-bold text-white">{value}</p>
                    <p className="text-sm text-slate-400">{label}</p>
                </div>
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
                            <div className="p-2 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600">
                                <Database className="w-8 h-8 text-white" />
                            </div>
                            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-rose-400 bg-clip-text text-transparent">
                                Data Federation
                            </h1>
                        </div>
                        <p className="text-slate-400">Discover and access datasets across R-NDIP member organizations</p>
                    </div>

                    <button className="flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-purple-500 to-pink-600 rounded-xl text-white font-medium hover:opacity-90 transition-opacity">
                        <Plus className="w-5 h-5" />
                        Register Dataset
                    </button>
                </div>
            </motion.div>

            {/* Stats Grid */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
                    <StatCard
                        icon={Database}
                        label="Total Datasets"
                        value={stats.total_datasets}
                        color="from-blue-500 to-indigo-600"
                    />
                    <StatCard
                        icon={Globe}
                        label="Public"
                        value={stats.by_access_level?.public || 0}
                        color="from-emerald-500 to-teal-600"
                    />
                    <StatCard
                        icon={Lock}
                        label="Restricted"
                        value={stats.by_access_level?.restricted || 0}
                        color="from-amber-500 to-orange-600"
                    />
                    <StatCard
                        icon={Download}
                        label="Downloads"
                        value={stats.total_downloads}
                        color="from-purple-500 to-pink-600"
                    />
                    <StatCard
                        icon={BarChart3}
                        label="Queries"
                        value={stats.total_queries}
                        color="from-cyan-500 to-blue-600"
                    />
                </div>
            )}

            {/* Search and Filters */}
            <div className="flex flex-wrap gap-4 mb-8">
                <div className="flex-1 min-w-[300px]">
                    <div className="relative">
                        <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-500" />
                        <input
                            type="text"
                            placeholder="Search datasets by name, description, or tags..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-12 pr-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500"
                        />
                    </div>
                </div>

                <select
                    value={selectedType || ''}
                    onChange={(e) => setSelectedType(e.target.value || null)}
                    className="px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                >
                    <option value="">All Types</option>
                    <option value="census">Census</option>
                    <option value="statistical">Statistical</option>
                    <option value="survey">Survey</option>
                    <option value="administrative">Administrative</option>
                    <option value="time_series">Time Series</option>
                    <option value="geospatial">Geospatial</option>
                </select>

                <select
                    value={selectedAccess || ''}
                    onChange={(e) => setSelectedAccess(e.target.value || null)}
                    className="px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                >
                    <option value="">All Access Levels</option>
                    <option value="public">Public</option>
                    <option value="restricted">Restricted</option>
                    <option value="internal">Internal</option>
                </select>
            </div>

            {/* Dataset Grid */}
            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
                </div>
            ) : datasets.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {datasets.map((dataset) => (
                        <DatasetCard key={dataset.id} dataset={dataset} />
                    ))}
                </div>
            ) : (
                <div className="text-center py-20">
                    <Database className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">No datasets found</h3>
                    <p className="text-slate-500">Try adjusting your search or filters</p>
                </div>
            )}

            {/* Dataset Detail Modal */}
            <AnimatePresence>
                {selectedDataset && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                        onClick={() => setSelectedDataset(null)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            onClick={(e) => e.stopPropagation()}
                            className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl border border-slate-700/50 w-full max-w-2xl max-h-[90vh] overflow-y-auto"
                        >
                            <div className="p-6 border-b border-slate-700/50">
                                <div className="flex items-start justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className={`p-3 rounded-xl bg-gradient-to-br ${typeColors[selectedDataset.dataset_type] || 'from-gray-500 to-slate-600'}`}>
                                            {React.createElement(typeIcons[selectedDataset.dataset_type] || Database, { className: 'w-6 h-6 text-white' })}
                                        </div>
                                        <div>
                                            <h2 className="text-2xl font-bold text-white">{selectedDataset.name}</h2>
                                            <p className="text-slate-400">{selectedDataset.organization_code}</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => setSelectedDataset(null)}
                                        className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors text-slate-400"
                                    >
                                        ✕
                                    </button>
                                </div>
                            </div>

                            <div className="p-6 space-y-6">
                                <div>
                                    <h3 className="text-sm font-medium text-slate-400 mb-2">Description</h3>
                                    <p className="text-white">{selectedDataset.description}</p>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="p-4 rounded-xl bg-slate-800/50">
                                        <p className="text-sm text-slate-400">Rows</p>
                                        <p className="text-xl font-bold text-white">
                                            {selectedDataset.statistics?.row_count?.toLocaleString() || 'N/A'}
                                        </p>
                                    </div>
                                    <div className="p-4 rounded-xl bg-slate-800/50">
                                        <p className="text-sm text-slate-400">Columns</p>
                                        <p className="text-xl font-bold text-white">
                                            {selectedDataset.statistics?.column_count || 'N/A'}
                                        </p>
                                    </div>
                                </div>

                                <div>
                                    <h3 className="text-sm font-medium text-slate-400 mb-2">Tags</h3>
                                    <div className="flex flex-wrap gap-2">
                                        {selectedDataset.tags?.map((tag) => (
                                            <span key={tag} className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-300 text-sm">
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                <div className="flex gap-3 pt-4 border-t border-slate-700/50">
                                    {selectedDataset.access_level === 'public' ? (
                                        <button className="flex-1 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-medium hover:opacity-90 transition-opacity">
                                            Access Dataset
                                        </button>
                                    ) : (
                                        <button className="flex-1 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-600 text-white font-medium hover:opacity-90 transition-opacity">
                                            Request Access
                                        </button>
                                    )}
                                    <button className="px-6 py-3 rounded-xl bg-slate-700/50 text-white font-medium hover:bg-slate-700 transition-colors">
                                        View Schema
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
