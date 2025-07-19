import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { SidebarProvider } from "@/components/ui/sidebar"
import { LayoutClientWrapper } from '@/components/LayoutClientWrapper';

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "NISR Rwanda | Intelligent Data Platform",
  description: "National Institute of Statistics of Rwanda - AI-powered analytics and reporting portal",
  generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <LayoutClientWrapper>
          <ThemeProvider attribute="class" defaultTheme="light" enableSystem disableTransitionOnChange>
            <SidebarProvider>{children}</SidebarProvider>
          </ThemeProvider>
        </LayoutClientWrapper>
      </body>
    </html>
  )
}
