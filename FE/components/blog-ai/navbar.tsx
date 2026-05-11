"use client"

import Link from "next/link"
import { FileText, CreditCard, Menu, X, User, LogOut, ChevronDown } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/stores/authStore"
import { useRouter } from "next/navigation"

export function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [isProfileDropdownOpen, setIsProfileDropdownOpen] = useState(false)
  const { user, isAuthenticated, logout } = useAuthStore()
  const router = useRouter()

  const handleLogout = () => {
    logout()
    setIsProfileDropdownOpen(false)
    router.push("/")
  }

  return (
    <nav className="bg-card border-b border-border">
      <div className="mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-2">
              <span className="text-2xl font-bold text-primary">BlogAI</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-6">
            <Link
              href="/previous-blogs"
              className="flex items-center space-x-2 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
            >
              <FileText className="h-4 w-4" />
              <span>Previous Blogs</span>
            </Link>
            <Link
              href="/billing"
              className="flex items-center space-x-2 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
            >
              <CreditCard className="h-4 w-4" />
              <span>Plans</span>
            </Link>

            {/* User Profile / Sign In */}
            <div className="relative">
              {isAuthenticated && user ? (
                <div className="relative">
                  <button
                    onClick={() => setIsProfileDropdownOpen(!isProfileDropdownOpen)}
                    className="flex items-center space-x-2 text-sm font-medium text-foreground hover:text-primary transition-colors py-2 px-3 rounded-lg hover:bg-muted/50"
                  >
                    <User className="h-4 w-4" />
                    <span className="max-w-[150px] truncate">{user.name}</span>
                    <ChevronDown className="h-3 w-3" />
                  </button>

                  {/* Dropdown Menu */}
                  {isProfileDropdownOpen && (
                    <div className="absolute right-0 mt-2 w-48 bg-card border border-border rounded-lg shadow-lg py-2 z-50">
                      <div className="px-4 py-2 border-b border-border">
                        <p className="text-sm font-medium text-foreground">{user.name}</p>
                        <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                      </div>
                      <button
                        onClick={handleLogout}
                        className="flex items-center space-x-2 w-full px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                      >
                        <LogOut className="h-4 w-4" />
                        <span>Sign Out</span>
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <Link href="/login">
                  <Button variant="default" size="sm">
                    Sign In
                  </Button>
                </Link>
              )}
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
            >
              {isMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </Button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden py-4 space-y-3 border-t border-border">
            <Link
              href="/previous-blogs"
              className="flex items-center space-x-2 text-sm font-medium text-primary hover:text-primary/80 transition-colors py-2"
              onClick={() => setIsMenuOpen(false)}
            >
              <FileText className="h-4 w-4" />
              <span>Previous Blogs</span>
            </Link>
            <Link
              href="/billing"
              className="flex items-center space-x-2 text-sm font-medium text-primary hover:text-primary/80 transition-colors py-2"
              onClick={() => setIsMenuOpen(false)}
            >
              <CreditCard className="h-4 w-4" />
              <span>Plans</span>
            </Link>

            {/* Mobile User Profile / Sign In */}
            <div className="border-t border-border pt-3">
              {isAuthenticated && user ? (
                <div className="space-y-2">
                  <div className="px-2 py-2">
                    <p className="text-sm font-medium text-foreground">{user.name}</p>
                    <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="flex items-center space-x-2 w-full px-2 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors rounded-lg"
                  >
                    <LogOut className="h-4 w-4" />
                    <span>Sign Out</span>
                  </button>
                </div>
              ) : (
                <Link href="/login" onClick={() => setIsMenuOpen(false)}>
                  <Button variant="default" size="sm" className="w-full">
                    Sign In
                  </Button>
                </Link>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}
