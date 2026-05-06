"use client"

import { useState } from "react"
import { Header } from "@/components/blog-ai/header"
import { PromptInput } from "@/components/blog-ai/prompt-input"
import { ArticlePreview } from "@/components/blog-ai/article-preview"

const sampleArticle = {
  title: "The Future of AI-Assisted Journalism",
  tags: ["AI INSIGHTS", "TECHNOLOGY"],
  content: [
    "In the evolving landscape of digital media, the intersection of human creativity and artificial intelligence is creating a new paradigm for long-form content. Editorial minimalism isn't just a design choice; it's a statement about the value of focus in an era of constant distraction.",
    "As we move forward, tools like BlogAI act as an intellectual scaffold. They don't replace the writer's voice; they amplify it by handling the structural heavy lifting, allowing the creator to focus on the nuance, the narrative arc, and the emotional resonance that only a human can provide.",
    "Performance in writing is measured by clarity. By utilizing a high-performance environment that recedes into the background, creators can achieve a state of flow more rapidly. This distraction-free approach ensures that the primary focus remains where it belongs: on the written word.",
  ],
  imageUrl: "/images/workspace.jpg",
}

export default function BlogAIPage() {
  const [prompt, setPrompt] = useState("")
  const [tone, setTone] = useState("Professional")
  const [isGenerating, setIsGenerating] = useState(false)
  const [showPreview, setShowPreview] = useState(true)

  const handleGenerate = () => {
    if (!prompt.trim()) return
    setIsGenerating(true)
    setTimeout(() => {
      setIsGenerating(false)
      setShowPreview(true)
    }, 1500)
  }

  const handleClear = () => {
    setPrompt("")
    setShowPreview(false)
  }

  const handleCopy = () => {
    const text = `${sampleArticle.title}\n\n${sampleArticle.content.join("\n\n")}`
    navigator.clipboard.writeText(text)
  }

  

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto px-4 sm:px-6 lg:px-8 pb-8">
        <div className="max-w-[680px] mx-auto">
          <Header onClear={handleClear} onCopy={handleCopy} />
        </div>
        
        <main className="space-y-5 sm:space-y-6">

          {/* Content wrapper with extra space on right for floating buttons on larger screens */}
          <div className="max-w-[680px] lg:max-w-[740px] mx-auto">
            <div className="max-w-[680px]">
              <PromptInput
                value={prompt}
                onChange={setPrompt}
                tone={tone}
                onToneChange={setTone}
                onGenerate={handleGenerate}
                isGenerating={isGenerating}
              />
            </div>
          </div>

          {showPreview && (
            <div className="max-w-[680px] lg:max-w-[740px] mx-auto relative">
              <ArticlePreview
                title={sampleArticle.title}
                tags={sampleArticle.tags}
                content={sampleArticle.content}
                imageUrl={sampleArticle.imageUrl}
              />
            </div>
          )}
        </main>

        <footer className="mt-10 sm:mt-12 text-center max-w-[680px] mx-auto">
          <p className="text-[10px] sm:text-xs text-muted-foreground">
            Generated with editorial precision by BlogAI. No tracking, no distractions.
          </p>
        </footer>
      </div>
    </div>
  )
}
