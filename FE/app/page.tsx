"use client"

import { useState, useEffect, useRef } from "react"
import { Header } from "@/components/blog-ai/header"
import { PromptInput } from "@/components/blog-ai/prompt-input"
import { ArticlePreview } from "@/components/blog-ai/article-preview"
import { PlanPreview } from "@/components/blog-ai/plan-preview"
import ReactMarkdown from 'react-markdown'

const API_BASE = "http://localhost:8000/api/v1/blog"
const USER_ID_TEST = process.env.NEXT_PUBLIC_USER_ID_TEST || "user-1"

export default function BlogAIPage() {
  const [prompt, setPrompt] = useState("")
  const [tone, setTone] = useState("Professional")
  const [userId] = useState(USER_ID_TEST)
  
  // App States: idle -> generating_plan -> awaiting_approval -> generating_article -> completed
  const [status, setStatus] = useState("idle")
  const [threadId, setThreadId] = useState<string | null>(null)
  const [plan, setPlan] = useState<any>(null)
  const [articleContent, setArticleContent] = useState<string | null>(null)
  const [articleTitle, setArticleTitle] = useState<string>("")
  const [userThreads, setUserThreads] = useState<any[]>([])
  const [isLoadingThreads, setIsLoadingThreads] = useState(false)
  
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
        setArticleTitle(data.topic || "Generated Article")
        stopPolling()
        fetchUserThreads() // Refresh threads after completion
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

  const fetchUserThreads = async () => {
    if (!userId) return
    setIsLoadingThreads(true)
    try {
      const res = await fetch(`${API_BASE}/threads/${userId}`)
      const data = await res.json()
      setUserThreads(data.threads || [])
    } catch (err) {
      console.error("Error fetching user threads:", err)
    } finally {
      setIsLoadingThreads(false)
    }
  }

  useEffect(() => {
    fetchUserThreads()
    return () => stopPolling()
  }, [userId])

  const handleGenerate = async () => {
    if (!prompt.trim()) return
    
    setStatus("generating_plan")
    setPlan(null)
    setArticleContent(null)
    
    try {
      const res = await fetch(`${API_BASE}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, tone, recency_days: 7, user_id: userId })
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
      <div className="mx-auto px-4 sm:px-6 lg:px-8 pb-8 w-full max-w-[1400px]">
        {/* Header and Prompt Area */}
        <div className="mx-auto transition-all duration-300 flex justify-center w-full gap-6">
          <div className="hidden lg:block lg:w-[25%] xl:w-[20%] shrink-0"></div>
          <div className="w-full lg:w-[50%] xl:w-[55%] shrink-0 space-y-6">
            <Header onClear={handleClear} onCopy={handleCopy} />
            <PromptInput
              value={prompt}
              onChange={setPrompt}
              tone={tone}
              onToneChange={setTone}
              onGenerate={handleGenerate}
              isGenerating={isGenerating}
            />
          </div>
          <div className="hidden lg:block lg:w-[25%] xl:w-[25%] shrink-0"></div>
        </div>
        
        {/* Main Content Area */}
        <main className="mx-auto mt-6 flex flex-col lg:flex-row items-start gap-6 transition-all duration-300 justify-center w-full">
          
          {/* Left Sidebar (Previous Blogs) */}
          <aside className="hidden lg:block w-full lg:w-[25%] xl:w-[20%] shrink-0 space-y-4 sticky top-6">
            <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider mb-4 px-1">Previous Blogs</h3>
            <div className="space-y-5">
               {isLoadingThreads ? (
                 <div className="text-center py-8 text-sm text-muted-foreground animate-pulse">
                   Loading threads...
                 </div>
               ) : userThreads.length === 0 ? (
                 <div className="text-center py-8 text-sm text-muted-foreground">
                   No previous threads
                 </div>
               ) : (
                 userThreads.map((thread: any) => (
                  <div key={thread.thread_id} className="flex flex-col rounded-2xl overflow-hidden bg-background border border-border shadow-sm hover:shadow-md cursor-pointer transition-all hover:border-primary/30 group">
                     <div className="w-full h-32 overflow-hidden">
                       <img src="/images/workspace.jpg" alt={thread.topic} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" />
                     </div>
                     <div className="p-4 bg-card relative">
                       <p className="text-sm font-semibold text-foreground leading-snug line-clamp-2">{thread.topic || "Untitled Thread"}</p>
                       <p className="text-xs text-muted-foreground mt-2">{thread.created_at || "Recently"}</p>
                     </div>
                  </div>
                 ))
               )}
            </div>
          </aside>

          {/* Center Column (Main Content) */}
          <div className="w-full lg:w-[50%] xl:w-[55%] shrink-0 space-y-5 sm:space-y-6">
            
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

            {status === "completed" && articleContent && (
              <div className="w-full relative">
                <ArticlePreview
                  title={articleTitle || "Generated Article"}
                  tags={["AI GENERATED", tone.toUpperCase()]}
                  content={articleContent.split('\n\n').filter(p => p.trim() !== '')} 
                  imageUrl="/images/workspace.jpg"
                />
              </div>
            )}
          </div>

          {/* Right Sidebar (Plan or Spacer) */}
          {plan ? (
            <aside className="w-full lg:w-[25%] xl:w-[25%] shrink-0 sticky top-6">
              <PlanPreview 
                plan={plan} 
                onApprove={(feedback) => handleApproval("approved", feedback)}
                onReject={(feedback) => handleApproval("rejected", feedback)}
                isReadOnly={status === "generating_article" || status === "completed"}
              />
            </aside>
          ) : (
            <div className="hidden lg:block lg:w-[25%] xl:w-[25%] shrink-0"></div>
          )}
        </main>

        {/* Footer Area */}
        <div className="mx-auto transition-all duration-300 flex justify-center w-full gap-6 mt-10 sm:mt-12">
          <div className="hidden lg:block lg:w-[25%] xl:w-[20%] shrink-0"></div>
          <footer className="w-full lg:w-[50%] xl:w-[55%] shrink-0 text-center">
            <p className="text-[10px] sm:text-xs text-muted-foreground">
              Generated with editorial precision by BlogAI. No tracking, no distractions.
            </p>
          </footer>
          <div className="hidden lg:block lg:w-[25%] xl:w-[25%] shrink-0"></div>
        </div>
      </div>
    </div>
  )
}
