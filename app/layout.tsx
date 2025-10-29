import type React from "react"
import { Inter } from "next/font/google"
import type { Metadata } from "next"
import { ThemeProvider } from "@/components/theme-provider"
import { ErrorBoundary } from "@/components/error-boundary"
import { Toaster } from "sonner"
import "./globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Nalytiq | Intelligent Data Platform",
  description: "Nalytiq - AI-powered analytics and reporting portal for Rwanda's National Institute of Statistics",
  generator: 'Prince Chris Mazimpaka',
  keywords: ['data analytics', 'rwanda', 'NISR', 'statistics', 'AI', 'machine learning'],
  authors: [{ name: 'Chris Mazimpaka', url: 'https://chrismazii.online' }],
  creator: 'Chris Mazimpaka',
  publisher: 'NISR Rwanda',
  robots: 'index, follow',
  openGraph: {
    title: 'Nalytiq | Intelligent Data Platform',
    description: 'AI-powered analytics and reporting portal for Rwanda',
    type: 'website',
    locale: 'en_RW',
    siteName: 'Nalytiq',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ErrorBoundary>
          <ThemeProvider attribute="class" defaultTheme="light" enableSystem disableTransitionOnChange>
            {children}
            <Toaster 
              position="top-right" 
              expand={false}
              richColors 
              closeButton
              toastOptions={{
                duration: 4000,
                className: 'toast',
              }}
            />
          </ThemeProvider>
        </ErrorBoundary>
      </body>
    </html>
  )
}
