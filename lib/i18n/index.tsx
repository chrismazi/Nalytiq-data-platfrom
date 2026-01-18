/**
 * Internationalization (i18n) Provider for Nalytiq
 * Supports English, Kinyarwanda, and French
 */
"use client"

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'

// Import translations
import en from './en.json'
import rw from './rw.json'
import fr from './fr.json'

// Available languages
export const LANGUAGES = {
    en: { code: 'en', name: 'English', nativeName: 'English', flag: '🇬🇧' },
    rw: { code: 'rw', name: 'Kinyarwanda', nativeName: 'Ikinyarwanda', flag: '🇷🇼' },
    fr: { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' }
} as const

export type LanguageCode = keyof typeof LANGUAGES
export type TranslationKey = string

// Translations map
const translations: Record<LanguageCode, typeof en> = {
    en,
    rw,
    fr
}

// Context type
interface I18nContextType {
    language: LanguageCode
    setLanguage: (lang: LanguageCode) => void
    t: (key: TranslationKey, params?: Record<string, string | number>) => string
    languages: typeof LANGUAGES
}

// Create context
const I18nContext = createContext<I18nContextType | undefined>(undefined)

// Get nested value from object using dot notation
function getNestedValue(obj: any, path: string): string | undefined {
    return path.split('.').reduce((current, key) => {
        return current && typeof current === 'object' ? current[key] : undefined
    }, obj)
}

// Replace parameters in string
function interpolate(text: string, params?: Record<string, string | number>): string {
    if (!params) return text

    return Object.entries(params).reduce((result, [key, value]) => {
        return result.replace(new RegExp(`{{${key}}}`, 'g'), String(value))
    }, text)
}

// Provider component
interface I18nProviderProps {
    children: ReactNode
    defaultLanguage?: LanguageCode
}

export function I18nProvider({ children, defaultLanguage = 'en' }: I18nProviderProps) {
    const [language, setLanguageState] = useState<LanguageCode>(defaultLanguage)
    const [isHydrated, setIsHydrated] = useState(false)

    // Load saved language preference
    useEffect(() => {
        const savedLang = localStorage.getItem('nalytiq-language') as LanguageCode
        if (savedLang && savedLang in LANGUAGES) {
            setLanguageState(savedLang)
        } else {
            // Try to detect browser language
            const browserLang = navigator.language.split('-')[0] as LanguageCode
            if (browserLang in LANGUAGES) {
                setLanguageState(browserLang)
            }
        }
        setIsHydrated(true)
    }, [])

    // Save language preference
    const setLanguage = (lang: LanguageCode) => {
        setLanguageState(lang)
        localStorage.setItem('nalytiq-language', lang)

        // Update HTML lang attribute
        document.documentElement.lang = lang
    }

    // Translation function
    const t = (key: TranslationKey, params?: Record<string, string | number>): string => {
        const value = getNestedValue(translations[language], key)

        if (value === undefined) {
            // Fallback to English
            const fallback = getNestedValue(translations.en, key)
            if (fallback === undefined) {
                console.warn(`Translation missing: ${key}`)
                return key
            }
            return interpolate(fallback, params)
        }

        return interpolate(value, params)
    }

    // Don't render until hydrated to avoid mismatch
    if (!isHydrated) {
        return null
    }

    return (
        <I18nContext.Provider value={{ language, setLanguage, t, languages: LANGUAGES }}>
            {children}
        </I18nContext.Provider>
    )
}

// Hook to use i18n
export function useI18n() {
    const context = useContext(I18nContext)
    if (context === undefined) {
        throw new Error('useI18n must be used within an I18nProvider')
    }
    return context
}

// Hook for just the translation function
export function useTranslation() {
    const { t } = useI18n()
    return t
}

// Language switcher component
export function LanguageSwitcher({ className = '' }: { className?: string }) {
    const { language, setLanguage, languages } = useI18n()

    return (
        <div className={`flex items-center gap-1 ${className}`}>
            {Object.values(languages).map((lang) => (
                <button
                    key={lang.code}
                    onClick={() => setLanguage(lang.code as LanguageCode)}
                    className={`
            px-2 py-1 text-sm rounded-md transition-colors
            ${language === lang.code
                            ? 'bg-primary text-primary-foreground'
                            : 'hover:bg-muted'}
          `}
                    title={lang.nativeName}
                >
                    {lang.flag}
                </button>
            ))}
        </div>
    )
}

// Select-based language switcher
export function LanguageSelect({ className = '' }: { className?: string }) {
    const { language, setLanguage, languages } = useI18n()

    return (
        <select
            value={language}
            onChange={(e) => setLanguage(e.target.value as LanguageCode)}
            className={`
        px-3 py-2 rounded-md border bg-background text-sm
        focus:outline-none focus:ring-2 focus:ring-primary
        ${className}
      `}
        >
            {Object.values(languages).map((lang) => (
                <option key={lang.code} value={lang.code}>
                    {lang.flag} {lang.nativeName}
                </option>
            ))}
        </select>
    )
}

// Higher-order component for translated components
export function withTranslation<P extends object>(
    Component: React.ComponentType<P & { t: (key: string) => string }>
) {
    return function TranslatedComponent(props: P) {
        const { t } = useI18n()
        return <Component {...props} t={t} />
    }
}

// Utility for server components (returns translations object)
export function getTranslations(lang: LanguageCode = 'en') {
    return translations[lang] || translations.en
}

// Format number with locale
export function formatNumber(value: number, lang: LanguageCode = 'en'): string {
    const locales: Record<LanguageCode, string> = {
        en: 'en-US',
        rw: 'rw-RW',
        fr: 'fr-FR'
    }
    return new Intl.NumberFormat(locales[lang]).format(value)
}

// Format date with locale
export function formatDate(date: Date | string, lang: LanguageCode = 'en', options?: Intl.DateTimeFormatOptions): string {
    const locales: Record<LanguageCode, string> = {
        en: 'en-US',
        rw: 'rw-RW',
        fr: 'fr-FR'
    }
    const dateObj = typeof date === 'string' ? new Date(date) : date
    return new Intl.DateTimeFormat(locales[lang], options).format(dateObj)
}

// Format relative time
export function formatRelativeTime(date: Date | string, lang: LanguageCode = 'en'): string {
    const locales: Record<LanguageCode, string> = {
        en: 'en-US',
        rw: 'rw-RW',
        fr: 'fr-FR'
    }

    const dateObj = typeof date === 'string' ? new Date(date) : date
    const now = new Date()
    const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000)

    const rtf = new Intl.RelativeTimeFormat(locales[lang], { numeric: 'auto' })

    if (diffInSeconds < 60) return rtf.format(-diffInSeconds, 'second')
    if (diffInSeconds < 3600) return rtf.format(-Math.floor(diffInSeconds / 60), 'minute')
    if (diffInSeconds < 86400) return rtf.format(-Math.floor(diffInSeconds / 3600), 'hour')
    if (diffInSeconds < 2592000) return rtf.format(-Math.floor(diffInSeconds / 86400), 'day')
    if (diffInSeconds < 31536000) return rtf.format(-Math.floor(diffInSeconds / 2592000), 'month')
    return rtf.format(-Math.floor(diffInSeconds / 31536000), 'year')
}
