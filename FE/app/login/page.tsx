"use client"

import { useState } from "react"
import { Mail, Lock, FileText, Sparkles, Send } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/authStore"

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const { login } = useAuthStore()
  const router = useRouter()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setIsLoading(true)

    try {
      await login(email, password)
      // After successful login, redirect to main page
      router.push("/")
    } catch (err: any) {
      setError(err.message || "Login failed. Please check your credentials.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4 sm:px-6">
      {/* Header */}
      <div className="text-center mb-8 sm:mb-10">
        <div className="flex justify-center mb-4">
          <div
            className="w-14 h-14 sm:w-16 sm:h-16 rounded-full flex items-center justify-center"
            style={{
              background: 'linear-gradient(145deg, #ffffff, #f8f8fc)',
              boxShadow: '8px 8px 20px #d8d8e5, -8px -8px 20px #ffffff',
            }}
          >
            <FileText className="w-7 h-7 sm:w-8 sm:h-8 text-primary" />
          </div>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-primary mb-2">BlogAI</h1>
        <p className="text-sm sm:text-base text-muted-foreground">
          Elevate your editorial journey
        </p>
      </div>

      {/* Login Form Card */}
      <div
        className="w-full max-w-md rounded-2xl sm:rounded-3xl p-6 sm:p-8 md:p-10 mb-8 sm:mb-10"
        style={{
          background: 'linear-gradient(145deg, #ffffff, #f8f8fc)',
          boxShadow: '8px 8px 20px #d8d8e5, -8px -8px 20px #ffffff',
        }}
      >
        {/* Error Message */}
        {error && (
          <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg mb-4 text-sm">
            {error}
          </div>
        )}

        {/* Form Header */}
        <div className="text-center mb-6 sm:mb-8">
          <h2 className="text-xl sm:text-2xl font-bold text-foreground mb-1 sm:mb-2">
            Sign In
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground">
            Welcome back to your editorial journey
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-5 sm:space-y-6">
          {/* Email Field */}
          <div>
            <label className="block text-xs sm:text-sm font-medium text-foreground mb-2">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 sm:left-4 top-1/2 -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-muted-foreground" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="john@example.com"
                className="w-full bg-background border border-border rounded-lg sm:rounded-xl pl-10 sm:pl-12 pr-4 py-2.5 sm:py-3 text-sm sm:text-base placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                required
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Password Field */}
          <div>
            <label className="block text-xs sm:text-sm font-medium text-foreground mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 sm:left-4 top-1/2 -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-muted-foreground" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-background border border-border rounded-lg sm:rounded-xl pl-10 sm:pl-12 pr-4 py-2.5 sm:py-3 text-sm sm:text-base placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                required
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Sign In Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-background border border-border text-primary font-medium py-2.5 sm:py-3 px-4 rounded-lg sm:rounded-xl transition-all duration-200 flex items-center justify-center gap-2 hover:bg-secondary/30 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              boxShadow: '4px 4px 12px #d8d8e5, -4px -4px 12px #ffffff',
            }}
          >
            {isLoading ? "Signing In..." : "Sign In"}
            {!isLoading && <span className="text-lg">→</span>}
          </button>
        </form>

        {/* Sign Up Link */}
        <div className="text-center mt-6 sm:mt-8 text-xs sm:text-sm">
          <span className="text-muted-foreground">Don't have an account? </span>
          <Link href="/signup" className="text-primary font-medium hover:underline">
            Create Account
          </Link>
        </div>
      </div>

      {/* Feature Cards */}
      <div className="w-full max-w-md grid grid-cols-3 gap-3 sm:gap-4 mb-10 sm:mb-12">
        {[
          { icon: FileText, label: 'DRAFT' },
          { icon: Sparkles, label: 'ENHANCE' },
          { icon: Send, label: 'PUBLISH' },
        ].map((feature) => (
          <div
            key={feature.label}
            className="aspect-square rounded-xl sm:rounded-2xl flex flex-col items-center justify-center"
            style={{
              background: 'linear-gradient(145deg, #ffffff, #f8f8fc)',
              boxShadow: '6px 6px 16px #d8d8e5, -6px -6px 16px #ffffff',
            }}
          >
            <feature.icon className="w-5 h-5 sm:w-6 sm:h-6 text-primary mb-2" />
            <span className="text-[10px] sm:text-xs font-semibold text-muted-foreground text-center px-1">
              {feature.label}
            </span>
          </div>
        ))}
      </div>

      {/* Footer */}
      <footer className="text-center text-[10px] sm:text-xs text-muted-foreground space-y-3">
        <p className="uppercase tracking-wide">Generated with editorial precision by BlogAI.</p>
        <div className="flex gap-4 justify-center text-[10px] sm:text-xs">
          <Link href="/privacy" className="hover:text-foreground transition-colors">
            Privacy Policy
          </Link>
          <span>·</span>
          <Link href="/terms" className="hover:text-foreground transition-colors">
            Terms of Service
          </Link>
          <span>·</span>
          <Link href="/support" className="hover:text-foreground transition-colors">
            Contact Support
          </Link>
        </div>
      </footer>
    </div>
  )
}
