"use client"

import { useState } from "react"
import { Bell, HelpCircle, Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ThemeToggle } from "@/components/theme-toggle"
import { SidebarTrigger } from "@/components/ui/sidebar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export function Header() {
  const [showSearch, setShowSearch] = useState(false)

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-background px-4 md:px-6">
      <SidebarTrigger />

      {showSearch ? (
        <div className="flex-1 md:flex-initial md:w-96 relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search..." className="pl-10 w-full" onBlur={() => setShowSearch(false)} autoFocus />
        </div>
      ) : (
        <Button variant="outline" size="icon" className="md:hidden" onClick={() => setShowSearch(true)}>
          <Search className="h-4 w-4" />
          <span className="sr-only">Search</span>
        </Button>
      )}

      <div className="hidden md:flex md:flex-1">
        <div className="relative w-96">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search..." className="pl-10 w-full" />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="icon" className="relative">
              <Bell className="h-4 w-4" />
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-medium text-primary-foreground">
                3
              </span>
              <span className="sr-only">Notifications</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Notifications</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>New dataset uploaded: "Health Indicators 2023"</DropdownMenuItem>
            <DropdownMenuItem>Report generation complete: "Economic Outlook Q2"</DropdownMenuItem>
            <DropdownMenuItem>System update scheduled for May 10, 2023</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <Button variant="outline" size="icon">
          <HelpCircle className="h-4 w-4" />
          <span className="sr-only">Help</span>
        </Button>

        <ThemeToggle />
      </div>
    </header>
  )
}
