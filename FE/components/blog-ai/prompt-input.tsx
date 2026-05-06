"use client"

import { Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"

interface PromptInputProps {
  value: string
  onChange: (value: string) => void
  tone: string
  onToneChange: (tone: string) => void
  onGenerate: () => void
  isGenerating: boolean
}

const tones = ["Professional", "Casual", "Creative"]

export function PromptInput({
  value,
  onChange,
  tone,
  onToneChange,
  onGenerate,
  isGenerating,
}: PromptInputProps) {
  return (
    <div className="space-y-4 sm:space-y-5">
      {/* Neumorphic textarea container */}
      <div 
        className="rounded-2xl p-4 sm:p-5"
        style={{
          background: 'linear-gradient(145deg, #f0f0f8, #e8e8f2)',
          boxShadow: 'inset 4px 4px 8px #d8d8e5, inset -4px -4px 8px #ffffff',
        }}
      >
        <textarea
          placeholder="What would you like to write about?"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full min-h-[80px] sm:min-h-[100px] resize-none bg-transparent text-foreground placeholder:text-muted-foreground/50 focus:outline-none text-sm sm:text-base"
        />
      </div>

      {/* Tone selector and generate button */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
          <span className="text-[10px] sm:text-xs text-muted-foreground uppercase tracking-widest font-medium">
            Tone:
          </span>
          <div className="flex gap-2 sm:gap-3">
            {tones.map((t) => (
              <button
                key={t}
                onClick={() => onToneChange(t)}
                className="px-4 sm:px-5 py-2 sm:py-2.5 text-xs sm:text-sm rounded-full transition-all font-medium"
                style={{
                  background: 'linear-gradient(145deg, #f5f5fb, #e8e8f2)',
                  boxShadow: tone === t 
                    ? 'inset 2px 2px 5px #d8d8e5, inset -2px -2px 5px #ffffff'
                    : '4px 4px 8px #d8d8e5, -4px -4px 8px #ffffff',
                  color: tone === t ? '#6366f1' : '#9ca3af',
                }}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
        <Button
          onClick={onGenerate}
          disabled={isGenerating || !value.trim()}
          className="bg-primary hover:bg-primary/90 text-primary-foreground rounded-full px-5 sm:px-6 py-2.5 gap-2 text-sm font-medium w-full sm:w-auto"
          style={{
            boxShadow: '4px 4px 12px rgba(99, 102, 241, 0.3), -2px -2px 8px rgba(255, 255, 255, 0.8)',
          }}
        >
          <Sparkles className="size-4" />
          Generate
        </Button>
      </div>
    </div>
  )
}
