"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Building2,
    X,
    Check,
    AlertCircle,
} from 'lucide-react';

interface RegisterOrganizationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

const MEMBER_CLASSES = [
    { value: 'GOV', label: 'Government', description: 'Government agencies and ministries' },
    { value: 'COM', label: 'Commercial', description: 'Private sector companies' },
    { value: 'ORG', label: 'Non-Profit', description: 'NGOs and non-profit organizations' },
    { value: 'MUN', label: 'Municipality', description: 'Local government entities' },
];

export default function RegisterOrganizationModal({
    isOpen,
    onClose,
    onSuccess
}: RegisterOrganizationModalProps) {
    const [formData, setFormData] = useState({
        code: '',
        name: '',
        member_class: 'GOV',
        contact_email: '',
        contact_phone: '',
        address: '',
        website: '',
        description: '',
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        setError('');
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await fetch('http://localhost:8000/api/v1/xroad/organizations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Registration failed');
            }

            setSuccess(true);
            setTimeout(() => {
                onSuccess();
                onClose();
                setSuccess(false);
                setFormData({
                    code: '',
                    name: '',
                    member_class: 'GOV',
                    contact_email: '',
                    contact_phone: '',
                    address: '',
                    website: '',
                    description: '',
                });
            }, 1500);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                onClick={onClose}
            >
                <motion.div
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.95, opacity: 0 }}
                    onClick={(e) => e.stopPropagation()}
                    className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl border border-slate-700/50 w-full max-w-2xl max-h-[90vh] overflow-y-auto"
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-slate-700/50">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600">
                                <Building2 className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h2 className="text-xl font-semibold text-white">Register Organization</h2>
                                <p className="text-sm text-slate-400">Add a new member to the X-Road network</p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                        >
                            <X className="w-5 h-5 text-slate-400" />
                        </button>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="p-6 space-y-6">
                        {success ? (
                            <motion.div
                                initial={{ scale: 0.8, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                className="text-center py-12"
                            >
                                <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                                    <Check className="w-8 h-8 text-emerald-400" />
                                </div>
                                <h3 className="text-xl font-semibold text-white mb-2">Registration Successful!</h3>
                                <p className="text-slate-400">Organization has been registered and is pending verification.</p>
                            </motion.div>
                        ) : (
                            <>
                                {/* Organization Code & Name */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-2">
                                            Organization Code *
                                        </label>
                                        <input
                                            type="text"
                                            name="code"
                                            value={formData.code}
                                            onChange={handleChange}
                                            placeholder="e.g., RW-GOV-MINICT"
                                            required
                                            className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-2">
                                            Organization Name *
                                        </label>
                                        <input
                                            type="text"
                                            name="name"
                                            value={formData.name}
                                            onChange={handleChange}
                                            placeholder="Full organization name"
                                            required
                                            className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
                                        />
                                    </div>
                                </div>

                                {/* Member Class */}
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">
                                        Member Class *
                                    </label>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                        {MEMBER_CLASSES.map((cls) => (
                                            <button
                                                key={cls.value}
                                                type="button"
                                                onClick={() => setFormData({ ...formData, member_class: cls.value })}
                                                className={`p-3 rounded-xl border text-left transition-all ${formData.member_class === cls.value
                                                        ? 'bg-blue-500/20 border-blue-500 text-blue-400'
                                                        : 'bg-slate-900/50 border-slate-700 text-slate-300 hover:border-slate-600'
                                                    }`}
                                            >
                                                <p className="font-medium">{cls.label}</p>
                                                <p className="text-xs text-slate-500 mt-1">{cls.value}</p>
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Contact Info */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-2">
                                            Contact Email *
                                        </label>
                                        <input
                                            type="email"
                                            name="contact_email"
                                            value={formData.contact_email}
                                            onChange={handleChange}
                                            placeholder="contact@example.gov.rw"
                                            required
                                            className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-2">
                                            Contact Phone
                                        </label>
                                        <input
                                            type="tel"
                                            name="contact_phone"
                                            value={formData.contact_phone}
                                            onChange={handleChange}
                                            placeholder="+250 xxx xxx xxx"
                                            className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
                                        />
                                    </div>
                                </div>

                                {/* Address & Website */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-2">
                                            Address
                                        </label>
                                        <input
                                            type="text"
                                            name="address"
                                            value={formData.address}
                                            onChange={handleChange}
                                            placeholder="Physical address"
                                            className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-2">
                                            Website
                                        </label>
                                        <input
                                            type="url"
                                            name="website"
                                            value={formData.website}
                                            onChange={handleChange}
                                            placeholder="https://example.gov.rw"
                                            className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
                                        />
                                    </div>
                                </div>

                                {/* Description */}
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">
                                        Description
                                    </label>
                                    <textarea
                                        name="description"
                                        value={formData.description}
                                        onChange={handleChange}
                                        placeholder="Brief description of the organization..."
                                        rows={3}
                                        className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 resize-none"
                                    />
                                </div>

                                {/* Error */}
                                {error && (
                                    <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400">
                                        <AlertCircle className="w-5 h-5" />
                                        <span>{error}</span>
                                    </div>
                                )}

                                {/* Actions */}
                                <div className="flex justify-end gap-3 pt-4 border-t border-slate-700/50">
                                    <button
                                        type="button"
                                        onClick={onClose}
                                        className="px-6 py-3 rounded-xl bg-slate-700/50 text-slate-300 font-medium hover:bg-slate-700 transition-colors"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={loading}
                                        className="px-6 py-3 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {loading ? 'Registering...' : 'Register Organization'}
                                    </button>
                                </div>
                            </>
                        )}
                    </form>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}
