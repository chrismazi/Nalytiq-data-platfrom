"use client"

import { useEffect, useState } from "react"
import { DashboardHeader } from "@/components/dashboard-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { getCurrentUser, updateUser } from "@/lib/api"

export default function SettingsPage() {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [role, setRole] = useState("")
  const [password, setPassword] = useState("")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    async function fetchUser() {
      setLoading(true)
      setError(null)
      try {
        const userData = await getCurrentUser()
        setUser(userData)
        setName(userData.email.split("@")[0])
        setEmail(userData.email)
        setRole(userData.role)
      } catch (err: any) {
        setError(err.message || "Failed to load user info")
      } finally {
        setLoading(false)
      }
    }
    fetchUser()
  }, [])

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    setSuccess(null)
    try {
      if (password) {
        await updateUser({ password })
        setSuccess("Password updated successfully.")
        setPassword("")
      } else {
        setSuccess("Nothing to update.")
      }
    } catch (err: any) {
      setError(err.message || "Failed to update profile.")
    } finally {
      setSaving(false)
    }
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
          {success && <div className="p-2 bg-green-100 text-green-800 rounded text-center">{success}</div>}
          {error && <div className="p-2 bg-red-100 text-red-800 rounded text-center">{error}</div>}
          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <Input value={name} onChange={e => setName(e.target.value)} placeholder="Your name" disabled />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <Input value={email} onChange={e => setEmail(e.target.value)} placeholder="Your email" disabled />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Role</label>
            <Input value={role} disabled />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <Input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="New password (optional)" />
          </div>
          <Button type="submit" disabled={saving}>{saving ? "Saving..." : "Save Changes"}</Button>
        </form>
      )}
    </div>
  )
} 