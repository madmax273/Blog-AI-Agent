"use client"

import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation"

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
}

export function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const router = useRouter()

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
      <div className="bg-card border border-border rounded-2xl p-6 sm:p-8 max-w-md w-full shadow-lg">
        <h2 className="text-2xl font-semibold text-foreground mb-4">Please Sign In</h2>
        <p className="text-muted-foreground mb-6">
          You need to sign in to generate blog articles. Create an account or sign in to continue.
        </p>
        <div className="flex flex-col sm:flex-row gap-3">
          <Button
            variant="outline"
            className="flex-1"
            onClick={() => {
              onClose()
              router.push("/login")
            }}
          >
            Sign In
          </Button>
          <Button
            className="flex-1"
            onClick={() => {
              onClose()
              router.push("/signup")
            }}
          >
            Create Account
          </Button>
        </div>
      </div>
    </div>
  )
}
