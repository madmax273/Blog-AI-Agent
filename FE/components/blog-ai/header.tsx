"use client"

import { Moon, Trash2, Copy } from "lucide-react"

interface HeaderProps {
  onClear: () => void
  onCopy: () => void
}

export function Header({ onClear, onCopy }: HeaderProps) {
  return (
    <header className="flex items-center justify-between py-4 sm:py-5 px-2 sm:px-4">
      <div className="text-lg sm:text-xl font-semibold text-primary">BlogAI</div>
      <div className="flex items-center gap-1 sm:gap-2">
        <button 
          className="p-2 text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Toggle dark mode"
        >
          <Moon className="size-4 sm:size-5" />
        </button>
        <button 
          className="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1.5 text-xs sm:text-sm text-muted-foreground hover:text-foreground transition-colors"
          onClick={onClear}
        >
          <Trash2 className="size-3.5 sm:size-4" />
          <span className="hidden xs:inline">Clear</span>
        </button>
        <button 
          className="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1.5 text-xs sm:text-sm text-muted-foreground hover:text-foreground transition-colors"
          onClick={onCopy}
        >
          <Copy className="size-3.5 sm:size-4" />
          <span className="hidden xs:inline">Copy</span>
        </button>
      </div>
    </header>
  )
}
