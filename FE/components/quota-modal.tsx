"use client"

import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation"

interface QuotaModalProps {
  isOpen: boolean
  onClose: () => void
  quota?: {
    blogs_generated: number
    blogs_limit: number
    blogs_remaining: number
    plan_type: string
  }
}

export function QuotaModal({ isOpen, onClose, quota }: QuotaModalProps) {
  const router = useRouter()

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
      <div className="bg-card border border-border rounded-2xl p-6 sm:p-8 max-w-md w-full shadow-lg">
        <h2 className="text-2xl font-semibold text-foreground mb-2">Plan Limit Reached</h2>
        <p className="text-muted-foreground mb-4">
          You've reached your monthly limit of {quota?.blogs_limit || 10} blog generations.
        </p>
        <div className="bg-muted/50 rounded-lg p-4 mb-6">
          <p className="text-sm text-foreground">
            <span className="font-medium">Current Plan:</span> {quota?.plan_type || "Basic"}<br />
            <span className="font-medium">Generated:</span> {quota?.blogs_generated || 0} / {quota?.blogs_limit || 10}
          </p>
        </div>
        <p className="text-sm text-muted-foreground mb-6">
          Upgrade to Pro for unlimited blog generation and advanced features.
        </p>
        <div className="flex flex-col sm:flex-row gap-3">
          <Button
            variant="outline"
            className="flex-1"
            onClick={onClose}
          >
            Maybe Later
          </Button>
          <Button
            className="flex-1"
            onClick={() => {
              onClose()
              router.push("/billing")
            }}
          >
            Upgrade Plan
          </Button>
        </div>
      </div>
    </div>
  )
}
