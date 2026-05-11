import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const API_BASE = "http://localhost:8000/api/v1"

interface User {
  id: number
  name: string
  email: string
  plan_type: string
  verified: boolean
  created_at: string
  updated_at: string
}

interface Quota {
  blogs_generated: number
  blogs_limit: number
  blogs_remaining: number
  words_generated: number
  words_limit: number
  words_remaining: number
  reset_date: string
  plan_type: string
}

interface AuthState {
  user: User | null
  token: string | null
  quota: Quota | null
  isLoading: boolean
  isAuthenticated: boolean
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  setQuota: (quota: Quota | null) => void
  setLoading: (loading: boolean) => void
  login: (email: string, password: string) => Promise<void>
  signup: (name: string, email: string, password: string) => Promise<void>
  logout: () => void
  fetchUserProfile: () => Promise<void>
  refreshQuota: () => Promise<void>
  initializeAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      quota: null,
      isLoading: true,
      isAuthenticated: false,

      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setToken: (token) => set({ token }),
      setQuota: (quota) => set({ quota }),
      setLoading: (isLoading) => set({ isLoading }),

      login: async (email: string, password: string) => {
        const formData = new FormData()
        formData.append("username", email)
        formData.append("password", password)

        const res = await fetch(`${API_BASE}/auth/login`, {
          method: "POST",
          body: formData
        })

        if (!res.ok) {
          const error = await res.json()
          throw new Error(error.detail || "Login failed")
        }

        const data = await res.json()
        set({ 
          token: data.access_token, 
          user: data.user, 
          isAuthenticated: true 
        })
        
        // Store in localStorage
        localStorage.setItem("access_token", data.access_token)
        localStorage.setItem("refresh_token", data.refresh_token)
        
        // Fetch quota after login
        await get().fetchUserProfile()
      },

      signup: async (name: string, email: string, password: string) => {
        const res = await fetch(`${API_BASE}/auth/signup`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, email, password })
        })

        if (!res.ok) {
          const error = await res.json()
          throw new Error(error.detail || "Signup failed")
        }

        const data = await res.json()
        set({ user: data.user })
      },

      logout: () => {
        localStorage.removeItem("access_token")
        localStorage.removeItem("refresh_token")
        set({ 
          user: null, 
          token: null, 
          quota: null, 
          isAuthenticated: false 
        })
      },

      fetchUserProfile: async () => {
        const { token } = get()
        if (!token) return

        try {
          const res = await fetch(`${API_BASE}/auth/me`, {
            headers: {
              Authorization: `Bearer ${token}`
            }
          })
          if (res.ok) {
            const data = await res.json()
            set({ user: data.user, quota: data.quota, isAuthenticated: true })
          } else {
            // Token invalid, clear it
            get().logout()
          }
        } catch (err) {
          console.error("Error fetching user profile:", err)
        } finally {
          set({ isLoading: false })
        }
      },

      refreshQuota: async () => {
        const { token } = get()
        if (!token) return
        
        try {
          const res = await fetch(`${API_BASE}/auth/me`, {
            headers: {
              Authorization: `Bearer ${token}`
            }
          })
          if (res.ok) {
            const data = await res.json()
            set({ quota: data.quota })
          }
        } catch (err) {
          console.error("Error refreshing quota:", err)
        }
      },

      initializeAuth: async () => {
        const token = localStorage.getItem('access_token')
        if (token) {
          set({ token })
          await get().fetchUserProfile()
        } else {
          set({ isLoading: false })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        token: state.token, 
        user: state.user,
        quota: state.quota 
      }),
    }
  )
)
