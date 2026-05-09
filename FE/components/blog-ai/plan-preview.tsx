"use client"

import { useState } from "react"
import { Check, X, Send } from "lucide-react"
import { Button } from "@/components/ui/button"

interface PlanTask {
  id: string
  title: string
  goal: string
  bullets: string[]
}

interface Plan {
  blog_title: string
  audience: string
  tone: string
  blog_kind: string
  tasks: PlanTask[]
}

interface PlanPreviewProps {
  plan: Plan
  onApprove: (feedback: string) => void
  onReject: (feedback: string) => void
}

export function PlanPreview({ plan, onApprove, onReject }: PlanPreviewProps) {
  const [feedback, setFeedback] = useState("")

  return (
    <div className="relative">
      <div 
        className="rounded-2xl sm:rounded-3xl p-4 sm:p-6 md:p-8 max-w-[680px]"
        style={{
          background: 'linear-gradient(145deg, #ffffff, #f8f8fc)',
          boxShadow: '8px 8px 20px #d8d8e5, -8px -8px 20px #ffffff',
        }}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-primary">Proposed Plan</h2>
          <span className="text-xs uppercase tracking-wider font-medium bg-amber-100 text-amber-800 px-2 py-0.5 rounded-md">
            Awaiting Approval
          </span>
        </div>

        <h1 className="text-lg sm:text-xl font-medium text-foreground leading-tight mb-3">
          Title: {plan.blog_title}
        </h1>
        
        <div className="grid grid-cols-2 gap-4 mb-6 text-sm text-muted-foreground">
          <div><span className="font-medium text-foreground">Audience:</span> {plan.audience}</div>
          <div><span className="font-medium text-foreground">Tone:</span> {plan.tone}</div>
          <div><span className="font-medium text-foreground">Kind:</span> {plan.blog_kind}</div>
        </div>
        
        <div className="w-full h-px bg-border/60 mb-5" />
        
        <div className="space-y-6">
          <h3 className="font-semibold text-foreground">Sections:</h3>
          {plan.tasks?.map((task, idx) => (
            <div key={task.id} className="text-sm">
              <h4 className="font-medium text-primary mb-1">
                {idx + 1}. {task.title}
              </h4>
              <p className="text-muted-foreground mb-2 text-xs">{task.goal}</p>
              <ul className="list-disc pl-5 space-y-1 text-xs text-foreground/80">
                {task.bullets?.map((bullet, bIdx) => (
                  <li key={bIdx}>{bullet}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="w-full h-px bg-border/60 my-6" />

        <div className="space-y-4">
          <h3 className="font-medium text-sm text-foreground">Your Feedback (Optional)</h3>
          <div 
            className="rounded-xl p-3"
            style={{
              background: 'linear-gradient(145deg, #f0f0f8, #e8e8f2)',
              boxShadow: 'inset 4px 4px 8px #d8d8e5, inset -4px -4px 8px #ffffff',
            }}
          >
            <textarea
              placeholder="Any changes you want to make? e.g., 'Make the intro more engaging' or 'Add a section about X'"
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              className="w-full min-h-[60px] resize-none bg-transparent text-foreground placeholder:text-muted-foreground/50 focus:outline-none text-xs sm:text-sm"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <Button
              onClick={() => onReject(feedback)}
              variant="outline"
              className="flex-1 rounded-full gap-2 text-xs sm:text-sm font-medium"
            >
              <X className="size-3.5" />
              Revise Plan
            </Button>
            <Button
              onClick={() => onApprove(feedback)}
              className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground rounded-full gap-2 text-xs sm:text-sm font-medium"
              style={{
                boxShadow: '4px 4px 12px rgba(99, 102, 241, 0.3), -2px -2px 8px rgba(255, 255, 255, 0.8)',
              }}
            >
              <Check className="size-3.5" />
              Approve & Generate
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
