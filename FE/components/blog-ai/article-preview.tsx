"use client"

import { Sparkles, SlidersHorizontal, Link2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import Image from "next/image"

interface ArticlePreviewProps {
  title: string
  tags: string[]
  content: string
  imageUrl: string
}

export function ArticlePreview({ title, tags, content, imageUrl }: ArticlePreviewProps) {
  return (
    <div className="relative">
      {/* Neumorphic article card - same width as prompt box */}
      <article 
        className="rounded-2xl sm:rounded-3xl p-4 sm:p-6 md:p-8 w-full"
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

        <div
          className="prose prose-sm sm:prose prose-base max-w-none text-foreground/80 leading-relaxed
                     prose-headings:font-semibold prose-headings:text-foreground
                     prose-h1:text-2xl sm:prose-h1:text-3xl prose-h1:mb-4 prose-h1:mt-6
                     prose-h2:text-xl sm:prose-h2:text-2xl prose-h2:mb-3 prose-h2:mt-5
                     prose-h3:text-lg sm:prose-h3:text-xl prose-h3:mb-2 prose-h3:mt-4
                     prose-p:text-xs sm:prose-p:text-sm prose-p:mb-4
                     prose-ul:list-disc prose-ul:pl-6 prose-ul:mb-4 prose-ul:space-y-2
                     prose-li:text-xs sm:prose-li:text-sm
                     prose-a:text-primary prose-a:no-underline hover:prose-a:underline
                     prose-strong:text-foreground prose-strong:font-semibold
                     prose-code:text-xs sm:prose-code:text-sm prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:rounded"
          dangerouslySetInnerHTML={{ __html: content }}
        />
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
