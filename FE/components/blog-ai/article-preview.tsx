"use client"

import { Sparkles, SlidersHorizontal, Link2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import Image from "next/image"

interface ArticlePreviewProps {
  title: string
  tags: string[]
  content: string[]
  imageUrl: string
}

export function ArticlePreview({ title, tags, content, imageUrl }: ArticlePreviewProps) {
  return (
    <div className="relative">
      {/* Neumorphic article card - same width as prompt box */}
      <article 
        className="rounded-2xl sm:rounded-3xl p-4 sm:p-6 md:p-8 max-w-[680px]"
        style={{
          background: 'linear-gradient(145deg, #ffffff, #f8f8fc)',
          boxShadow: '8px 8px 20px #d8d8e5, -8px -8px 20px #ffffff',
        }}
      >
        <h1 className="text-xl sm:text-2xl md:text-3xl font-semibold text-primary leading-tight mb-3 text-balance">
          {title}
        </h1>
        
        <div className="flex gap-2 mb-4">
          {tags.map((tag) => (
            <Badge 
              key={tag} 
              variant="secondary" 
              className="text-[9px] sm:text-[10px] uppercase tracking-wider font-medium bg-muted/60 text-muted-foreground border-0 px-2 py-0.5 rounded-md"
            >
              {tag}
            </Badge>
          ))}
        </div>
        
        <div className="w-full h-px bg-border/60 mb-5" />
        
        <div className="space-y-4 text-foreground/80 text-xs sm:text-sm leading-relaxed">
          {content.slice(0, 2).map((paragraph, index) => (
            <p key={index}>{paragraph}</p>
          ))}
        </div>

        <div 
          className="my-5 sm:my-6 rounded-xl sm:rounded-2xl overflow-hidden"
          style={{
            boxShadow: '4px 4px 12px #d8d8e5, -4px -4px 12px #ffffff',
          }}
        >
          <Image
            src={imageUrl}
            alt="Article illustration"
            width={600}
            height={400}
            className="w-full h-auto object-cover"
          />
        </div>

        <div className="space-y-4 text-foreground/80 text-xs sm:text-sm leading-relaxed">
          {content.slice(2).map((paragraph, index) => (
            <p key={index}>{paragraph}</p>
          ))}
        </div>

        {content.length > 2 && (
          <>
            <h2 className="text-lg sm:text-xl font-semibold text-foreground mt-5 sm:mt-6 mb-3">
              The Synthesis of Man and Machine
            </h2>
            <p className="text-foreground/80 text-xs sm:text-sm leading-relaxed">
              The emotional response to a well-crafted piece of journalism should be one of competence and clarity. When the UI is invisible, the message becomes unavoidable. This is the core tenet of modern productivity software—tools that empower without intruding.
            </p>
          </>
        )}
      </article>

      {/* Floating action buttons - positioned outside the card on desktop */}
      <div className="absolute right-2 lg:right-[-60px] top-[200px] lg:top-1/2 lg:-translate-y-1/2 flex flex-col gap-2 sm:gap-3">
        {[
          { icon: Sparkles, label: "Enhance" },
          { icon: SlidersHorizontal, label: "Adjust" },
          { icon: Link2, label: "Link" },
        ].map(({ icon: Icon, label }) => (
          <button 
            key={label}
            className="size-8 sm:size-10 rounded-full flex items-center justify-center text-primary transition-all hover:scale-105"
            style={{
              background: 'linear-gradient(145deg, #ffffff, #f0f0f8)',
              boxShadow: '4px 4px 10px #d8d8e5, -4px -4px 10px #ffffff',
            }}
            aria-label={label}
          >
            <Icon className="size-3.5 sm:size-4" />
          </button>
        ))}
      </div>
    </div>
  )
}
