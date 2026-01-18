"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Bell, HelpCircle, Search, LogOut, User, Settings, Shield, BarChart3 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ThemeToggle } from "@/components/theme-toggle"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { getCurrentUser } from "@/lib/api"

interface UserInfo {
  id: number
  email: string
  role: string
}

const ROLE_ICONS: Record<string, typeof Shield> = {
  admin: Shield,
  analyst: BarChart3,
  viewer: User,
}

const ROLE_COLORS: Record<string, string> = {
  admin: "bg-red-500",
  analyst: "bg-blue-500",
  viewer: "bg-green-500",
}

export function Header() {
  const [showSearch, setShowSearch] = useState(false)
  const [user, setUser] = useState<UserInfo | null>(null)
  const router = useRouter()

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const userData = await getCurrentUser()
        setUser(userData)
      } catch (error) {
        // Not logged in or error fetching user
        console.log("Not authenticated")
      }
    }
    fetchUser()
  }, [])

  const handleLogout = () => {
    localStorage.removeItem("token")
    localStorage.removeItem("nalytiq_token")
    localStorage.removeItem("nalytiq_user")
    router.push("/login")
  }

  const getInitials = (email: string) => {
    const name = email.split("@")[0]
    return name.substring(0, 2).toUpperCase()
  }

  const RoleIcon = user ? ROLE_ICONS[user.role] || User : User
  const roleColor = user ? ROLE_COLORS[user.role] || "bg-gray-500" : "bg-gray-500"

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

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-9 px-2 gap-2">
              <Avatar className="h-8 w-8">
                <AvatarFallback className={`${roleColor} text-white text-xs`}>
                  {user ? getInitials(user.email) : "?"}
                </AvatarFallback>
              </Avatar>
              <div className="hidden md:flex flex-col items-start text-left">
                <span className="text-sm font-medium truncate max-w-[120px]">
                  {user ? user.email.split("@")[0] : "Guest"}
                </span>
                <Badge variant="outline" className="text-[10px] px-1 py-0 capitalize">
                  {user?.role || "loading"}
                </Badge>
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">{user?.email || "Not logged in"}</p>
                <p className="text-xs leading-none text-muted-foreground capitalize flex items-center gap-1">
                  <RoleIcon className="h-3 w-3" />
                  {user?.role || "guest"}
                </p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => router.push("/settings")}>
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="text-red-600">
              <LogOut className="mr-2 h-4 w-4" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}

