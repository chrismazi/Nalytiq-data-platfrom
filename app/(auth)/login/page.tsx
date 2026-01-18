"use client"

import type React from "react"
import { useState, useEffect } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Eye, EyeOff, Lock, User, Zap, Shield, BarChart3 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { loginUser, getCurrentUser } from "@/lib/api"

// Demo credentials for quick access
const DEMO_ACCOUNTS = [
  { email: "admin@nalytiq.rw", password: "admin123", role: "Admin", icon: Shield, color: "text-red-500" },
  { email: "analyst@nalytiq.rw", password: "analyst123", role: "Analyst", icon: BarChart3, color: "text-blue-500" },
  { email: "demo@nalytiq.rw", password: "demo123", role: "Demo", icon: Zap, color: "text-green-500" },
]

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [checkingAuth, setCheckingAuth] = useState(true)
  const router = useRouter()

  // Check if already logged in
  useEffect(() => {
    const checkExistingAuth = async () => {
      try {
        await getCurrentUser()
        // Already logged in, redirect to dashboard
        router.push("/dashboard")
      } catch {
        // Not logged in, show login form
        setCheckingAuth(false)
      }
    }
    checkExistingAuth()
  }, [router])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    await performLogin(email, password)
  }

  const performLogin = async (loginEmail: string, loginPassword: string) => {
    setIsLoading(true)
    setError(null)
    try {
      await loginUser(loginEmail, loginPassword)
      router.push("/dashboard")
    } catch (err) {
      setError("Invalid email or password")
      setIsLoading(false)
    }
  }

  const handleDemoLogin = async (account: typeof DEMO_ACCOUNTS[0]) => {
    setEmail(account.email)
    setPassword(account.password)
    await performLogin(account.email, account.password)
  }

  if (checkingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-900 dark:to-gray-800">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Checking authentication...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-900 dark:to-gray-800 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-2">
            <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-primary/70 text-primary-foreground font-bold text-2xl">N</div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Nalytiq</h1>
          <p className="text-gray-600 dark:text-gray-400">AI-Powered Analytics Platform</p>
        </div>

        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle>Sign In</CardTitle>
            <CardDescription>Access the Nalytiq platform</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Quick Demo Login Buttons */}
            <div className="space-y-2">
              <Label className="text-xs text-muted-foreground">Quick Access</Label>
              <div className="grid grid-cols-3 gap-2">
                {DEMO_ACCOUNTS.map((account) => {
                  const Icon = account.icon
                  return (
                    <Button
                      key={account.email}
                      variant="outline"
                      size="sm"
                      className="flex flex-col h-auto py-3 gap-1"
                      onClick={() => handleDemoLogin(account)}
                      disabled={isLoading}
                    >
                      <Icon className={`h-4 w-4 ${account.color}`} />
                      <span className="text-xs">{account.role}</span>
                    </Button>
                  )
                })}
              </div>
            </div>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <Separator className="w-full" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted-foreground">or login manually</span>
              </div>
            </div>

            <form onSubmit={handleLogin}>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="email"
                      placeholder="name@nalytiq.rw"
                      type="email"
                      required
                      className="pl-10"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      required
                      className="pl-10"
                      value={password}
                      onChange={e => setPassword(e.target.value)}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-0 top-0 h-full px-3 py-2 text-muted-foreground"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      <span className="sr-only">{showPassword ? "Hide password" : "Show password"}</span>
                    </Button>
                  </div>
                </div>
                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? "Signing in..." : "Sign In"}
                </Button>
                {error && <div className="text-red-600 text-sm text-center">{error}</div>}
              </div>
            </form>
          </CardContent>
          <CardFooter className="flex flex-col space-y-2">
            <div className="text-sm text-muted-foreground text-center">
              Don&apos;t have an account?{" "}
              <Link href="/register" className="underline underline-offset-4 hover:text-primary">
                Register here
              </Link>
            </div>
          </CardFooter>
        </Card>

        {/* Demo credentials info */}
        <div className="mt-4 p-4 rounded-lg bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm">
          <p className="text-xs text-center text-muted-foreground">
            <strong>Demo Mode:</strong> Click any quick access button above to login instantly
          </p>
        </div>
      </div>
    </div>
  )
}

