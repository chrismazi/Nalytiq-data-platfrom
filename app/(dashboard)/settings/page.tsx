"use client"

import { useEffect, useState } from "react"
import { DashboardHeader } from "@/components/dashboard-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { getCurrentUser } from "@/lib/api"

export default function SettingsPage() {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")

  useEffect(() => {
    async function fetchUser() {
      setLoading(true)
      setError(null)
      try {
        const userData = await getCurrentUser()
        setUser(userData)
        setName(userData.email.split("@")[0]) // Placeholder: use part before @ as name
        setEmail(userData.email)
      } catch (err: any) {
        setError(err.message || "Failed to load user info")
      } finally {
        setLoading(false)
      }
    }
    fetchUser()
  }, [])

  const handleSave = () => {
    // TODO: Implement save logic (update user profile)
    alert("Profile updated (not yet implemented)")
  }

  return (
    <div className="space-y-6 max-w-xl mx-auto">
      <DashboardHeader title="Settings" description="Manage your account and profile settings" />
      {loading ? (
        <div className="p-8 text-center">Loading...</div>
      ) : error ? (
        <div className="p-8 text-center text-red-500">{error}</div>
      ) : (
        <form className="space-y-4" onSubmit={e => { e.preventDefault(); handleSave(); }}>
          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <Input value={name} onChange={e => setName(e.target.value)} placeholder="Your name" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <Input value={email} onChange={e => setEmail(e.target.value)} placeholder="Your email" disabled />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <Input type="password" placeholder="New password (optional)" />
          </div>
          <Button type="submit">Save Changes</Button>
        </form>
      )}
    </div>
  )
} 