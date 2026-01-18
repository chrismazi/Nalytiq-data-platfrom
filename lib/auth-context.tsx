/**
 * Authentication Context and Provider
 * Provides seamless authentication throughout the app
 */
"use client"

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { useRouter, usePathname } from 'next/navigation'

// API base URL
const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

// Types
export interface User {
    id: number
    email: string
    role: 'admin' | 'analyst' | 'viewer'
}

export interface AuthContextType {
    user: User | null
    isLoading: boolean
    isAuthenticated: boolean
    login: (email: string, password: string) => Promise<void>
    register: (email: string, password: string, role: string) => Promise<void>
    logout: () => void
    loginAsDemo: () => Promise<void>
    checkAuth: () => Promise<boolean>
}

// Default demo credentials
export const DEMO_CREDENTIALS = {
    admin: { email: 'admin@nalytiq.rw', password: 'admin123' },
    analyst: { email: 'analyst@nalytiq.rw', password: 'analyst123' },
    demo: { email: 'demo@nalytiq.rw', password: 'demo123' }
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Token storage keys
const TOKEN_KEY = 'nalytiq_token'
const USER_KEY = 'nalytiq_user'

// Helper functions for token management
function getStoredToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(TOKEN_KEY)
}

function setStoredToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token)
}

function removeStoredToken(): void {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
}

function getStoredUser(): User | null {
    if (typeof window === 'undefined') return null
    const userStr = localStorage.getItem(USER_KEY)
    if (userStr) {
        try {
            return JSON.parse(userStr)
        } catch {
            return null
        }
    }
    return null
}

function setStoredUser(user: User): void {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
}

// Auth Provider Props
interface AuthProviderProps {
    children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
    const [user, setUser] = useState<User | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const router = useRouter()
    const pathname = usePathname()

    // Check if user is authenticated
    const checkAuth = useCallback(async (): Promise<boolean> => {
        const token = getStoredToken()
        if (!token) {
            setUser(null)
            setIsLoading(false)
            return false
        }

        try {
            const res = await fetch(`${API_URL}/auth/me`, {
                headers: { 'Authorization': `Bearer ${token}` }
            })

            if (res.ok) {
                const userData = await res.json()
                setUser(userData)
                setStoredUser(userData)
                setIsLoading(false)
                return true
            } else {
                // Token invalid
                removeStoredToken()
                setUser(null)
                setIsLoading(false)
                return false
            }
        } catch (error) {
            console.error('Auth check failed:', error)
            // On network error, try to use cached user
            const cachedUser = getStoredUser()
            if (cachedUser) {
                setUser(cachedUser)
            }
            setIsLoading(false)
            return !!cachedUser
        }
    }, [])

    // Login function
    const login = async (email: string, password: string): Promise<void> => {
        setIsLoading(true)

        const formData = new URLSearchParams()
        formData.append('username', email)
        formData.append('password', password)

        try {
            const res = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            })

            if (!res.ok) {
                const error = await res.json().catch(() => ({ detail: 'Login failed' }))
                throw new Error(error.detail || 'Invalid credentials')
            }

            const data = await res.json()
            setStoredToken(data.access_token)

            // Get user info
            const userRes = await fetch(`${API_URL}/auth/me`, {
                headers: { 'Authorization': `Bearer ${data.access_token}` }
            })

            if (userRes.ok) {
                const userData = await userRes.json()
                setUser(userData)
                setStoredUser(userData)
            }

            setIsLoading(false)
        } catch (error) {
            setIsLoading(false)
            throw error
        }
    }

    // Register function
    const register = async (email: string, password: string, role: string): Promise<void> => {
        setIsLoading(true)

        try {
            const res = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, role })
            })

            if (!res.ok) {
                const error = await res.json().catch(() => ({ detail: 'Registration failed' }))
                throw new Error(error.detail || 'Registration failed')
            }

            // Auto-login after registration
            await login(email, password)
        } catch (error) {
            setIsLoading(false)
            throw error
        }
    }

    // Logout function
    const logout = () => {
        removeStoredToken()
        setUser(null)
        router.push('/login')
    }

    // Quick demo login
    const loginAsDemo = async (): Promise<void> => {
        await login(DEMO_CREDENTIALS.demo.email, DEMO_CREDENTIALS.demo.password)
    }

    // Check auth on mount
    useEffect(() => {
        checkAuth()
    }, [checkAuth])

    // Auto-redirect logic
    useEffect(() => {
        if (isLoading) return

        const publicPaths = ['/login', '/register', '/']
        const isPublicPath = publicPaths.includes(pathname)

        if (!user && !isPublicPath) {
            // Not authenticated and trying to access protected route
            // Auto-login with demo for seamless experience
            loginAsDemo().then(() => {
                // Stay on current page
            }).catch(() => {
                router.push('/login')
            })
        }
    }, [user, isLoading, pathname, router])

    const value: AuthContextType = {
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        loginAsDemo,
        checkAuth
    }

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    )
}

// Hook to use auth context
export function useAuth() {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}

// HOC for protecting routes
export function withAuth<P extends object>(
    Component: React.ComponentType<P>,
    options?: { requiredRole?: 'admin' | 'analyst' | 'viewer' }
) {
    return function AuthenticatedComponent(props: P) {
        const { user, isLoading, isAuthenticated } = useAuth()
        const router = useRouter()

        useEffect(() => {
            if (!isLoading && !isAuthenticated) {
                router.push('/login')
            }

            if (options?.requiredRole && user && user.role !== options.requiredRole) {
                if (options.requiredRole === 'admin' && user.role !== 'admin') {
                    router.push('/dashboard')
                }
            }
        }, [isLoading, isAuthenticated, user, router])

        if (isLoading) {
            return (
                <div className="min-h-screen flex items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            )
        }

        if (!isAuthenticated) {
            return null
        }

        return <Component {...props} />
    }
}

// Auth guard component
export function AuthGuard({ children }: { children: ReactNode }) {
    const { isLoading, isAuthenticated, loginAsDemo } = useAuth()
    const [attempted, setAttempted] = useState(false)

    useEffect(() => {
        if (!isLoading && !isAuthenticated && !attempted) {
            setAttempted(true)
            // Auto-login for seamless experience
            loginAsDemo().catch(console.error)
        }
    }, [isLoading, isAuthenticated, attempted, loginAsDemo])

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-900 dark:to-gray-800">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                    <p className="text-muted-foreground">Loading Nalytiq...</p>
                </div>
            </div>
        )
    }

    return <>{children}</>
}

export default AuthContext
