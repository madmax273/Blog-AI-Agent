"use client"

import { useState, useEffect, useRef } from "react"
import { Header } from "@/components/blog-ai/header"
import { PromptInput } from "@/components/blog-ai/prompt-input"
import { ArticlePreview } from "@/components/blog-ai/article-preview"
import { PlanPreview } from "@/components/blog-ai/plan-preview"
import ReactMarkdown from 'react-markdown'

const API_BASE = "http://localhost:8000/api/v1/blog"

export default function BlogAIPage() {
  const [prompt, setPrompt] = useState("")
  const [tone, setTone] = useState("Professional")
  
  // App States: idle -> generating_plan -> awaiting_approval -> generating_article -> completed
  const [status, setStatus] = useState("idle")
  const [threadId, setThreadId] = useState<string | null>(null)
  const [plan, setPlan] = useState<any>(null)
  const [articleContent, setArticleContent] = useState<string | null>(null)
  const [articleTitle, setArticleTitle] = useState<string>("")
  
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
  }

  const pollStatus = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/status/${id}`)
      const data = await res.json()
      
      if (data.status === "awaiting_approval") {
        setStatus("awaiting_approval")
        setPlan(data.plan)
        stopPolling()
      } else if (data.status === "completed") {
        setStatus("completed")
        setArticleContent(data.markdown_content)
        if (data.plan) {
          setArticleTitle(data.plan.blog_title)
        }
        stopPolling()
      } else if (data.status === "error") {
        setStatus("idle")
        alert("An error occurred during generation.")
        stopPolling()
      }
    } catch (err) {
      console.error("Polling error:", err)
    }
  }

  const startPolling = (id: string) => {
    stopPolling()
    pollIntervalRef.current = setInterval(() => pollStatus(id), 3000)
  }

  useEffect(() => {
    return () => stopPolling()
  }, [])

  const handleGenerate = async () => {
    if (!prompt.trim()) return
    
    setStatus("generating_plan")
    setPlan(null)
    setArticleContent(null)
    
    try {
      const res = await fetch(`${API_BASE}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, tone, recency_days: 7 })
      })
      const data = await res.json()
      
      if (data.thread_id) {
        setThreadId(data.thread_id)
        startPolling(data.thread_id)
      }
    } catch (err) {
      console.error("Generate error:", err)
      setStatus("idle")
    }
  }

  const handleApproval = async (approvalStatus: "approved" | "rejected", feedback: string) => {
    if (!threadId) return
    
    setStatus("generating_article")
    
    try {
      await fetch(`${API_BASE}/resume/${threadId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approval: approvalStatus, suggestions: feedback })
      })
      
      startPolling(threadId)
    } catch (err) {
      console.error("Resume error:", err)
      setStatus("awaiting_approval") // revert on error
    }
  }

  const handleClear = () => {
    setPrompt("")
    setStatus("idle")
    setPlan(null)
    setArticleContent(null)
    stopPolling()
  }

  const handleCopy = () => {
    if (articleContent) {
      navigator.clipboard.writeText(articleContent)
    }
  }

  const isGenerating = status === "generating_plan" || status === "generating_article"

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto px-4 sm:px-6 lg:px-8 pb-8">
        <div className="max-w-[680px] mx-auto">
          <Header onClear={handleClear} onCopy={handleCopy} />
        </div>
        
        <main className="space-y-5 sm:space-y-6">
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
            
            {status === "generating_plan" && (
              <div className="text-center py-8 text-sm text-muted-foreground animate-pulse">
                Analyzing request and building a plan...
              </div>
            )}
            
            {status === "generating_article" && (
              <div className="text-center py-8 text-sm text-muted-foreground animate-pulse">
                Writing your article based on the approved plan...
              </div>
            )}
          </div>

          {status === "awaiting_approval" && plan && (
            <div className="max-w-[680px] lg:max-w-[740px] mx-auto relative">
              <PlanPreview 
                plan={plan} 
                onApprove={(feedback) => handleApproval("approved", feedback)}
                onReject={(feedback) => handleApproval("rejected", feedback)}
              />
            </div>
          )}

          {status === "completed" && articleContent && (
            <div className="max-w-[680px] lg:max-w-[740px] mx-auto relative">
              <ArticlePreview
                title={articleTitle || "Generated Article"}
                tags={["AI GENERATED", tone.toUpperCase()]}
                content={articleContent.split('\n\n').filter(p => p.trim() !== '')} 
                imageUrl="/images/workspace.jpg"
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
