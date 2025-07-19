import type React from "react"
import { AppSidebar } from "@/components/app-sidebar"
import { Header } from "@/components/header"
import { ChatbotButton } from "@/components/chatbot-button"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen">
      <AppSidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-6 overflow-auto">{children}</main>
        <ChatbotButton />
      </div>
    </div>
  )
}
