"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { Header } from "@/components/blog-ai/header"
import { Navbar } from "@/components/blog-ai/navbar"
import { PromptInput } from "@/components/blog-ai/prompt-input"
import { ArticlePreview } from "@/components/blog-ai/article-preview"
import { PlanPreview } from "@/components/blog-ai/plan-preview"
import { AuthModal } from "@/components/auth-modal"
import { QuotaModal } from "@/components/quota-modal"
import { useAuthStore } from "@/stores/authStore"
import { Button } from "@/components/ui/button"

const API_BASE = "http://localhost:8000/api/v1/blog"

export default function BlogAIPage() {
  const router = useRouter()
  const { user, token, quota, isAuthenticated, isLoading: authLoading, refreshQuota } = useAuthStore()
  const [prompt, setPrompt] = useState("")
  const [tone, setTone] = useState("Professional")
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [showQuotaModal, setShowQuotaModal] = useState(false)
  
  // App States: idle -> generating_plan -> awaiting_approval -> generating_article -> completed
  const [status, setStatus] = useState("idle")
  const [threadId, setThreadId] = useState<string | null>(null)
  const [plan, setPlan] = useState<any>(null)
  const [articleContent, setArticleContent] = useState<string | null>(null)
  const [articleTitle, setArticleTitle] = useState<string>("")
  const [userThreads, setUserThreads] = useState<any[]>([])
  const [isLoadingThreads, setIsLoadingThreads] = useState(false)
  
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Load state from localStorage on mount
  useEffect(() => {
    const savedState = localStorage.getItem('blogState')
    if (savedState) {
      try {
        const state = JSON.parse(savedState)
        setPrompt(state.prompt || "")
        setTone(state.tone || "Professional")
        setStatus(state.status || "idle")
        setThreadId(state.threadId || null)
        setPlan(state.plan || null)
        setArticleContent(state.articleContent || null)
        setArticleTitle(state.articleTitle || "")
        
        // Resume polling if status is not idle or completed
        if (state.threadId && (state.status === "generating_plan" || state.status === "generating_article")) {
          startPolling(state.threadId)
        }
      } catch (err) {
        console.error("Error loading state from localStorage:", err)
      }
    }
  }, [])

  // Save state to localStorage whenever it changes
  useEffect(() => {
    const state = {
      prompt,
      tone,
      status,
      threadId,
      plan,
      articleContent,
      articleTitle
    }
    localStorage.setItem('blogState', JSON.stringify(state))
  }, [prompt, tone, status, threadId, plan, articleContent, articleTitle])

  const handleClear = () => {
    setPrompt("")
    setTone("Professional")
    setStatus("idle")
    setThreadId(null)
    setPlan(null)
    setArticleContent(null)
    setArticleTitle("")
    stopPolling()
    localStorage.removeItem('blogState')
  }

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
  }

  const pollStatus = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/status/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      const data = await res.json()
      
      if (data.status === "awaiting_approval") {
        setStatus("awaiting_approval")
        setPlan(data.plan)
        stopPolling()
      } else if (data.status === "completed") {
        setStatus("completed")
        // Use html_content if available, fallback to markdown_content
        setArticleContent(data.html_content || data.markdown_content)
        setArticleTitle(data.topic || "Generated Article")
        stopPolling()
        fetchUserThreads() // Refresh threads after completion
        refreshQuota() // Refresh quota after completion
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
    if (!user) return
    setIsLoadingThreads(true)
    try {
      const res = await fetch(`${API_BASE}/threads`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) {
        console.error("Threads API error:", res.status, res.statusText)
        setUserThreads([])
        return
      }
      const data = await res.json()
      setUserThreads(data.threads || [])
    } catch (err) {
      console.error("Error fetching user threads:", err)
      setUserThreads([])
    } finally {
      setIsLoadingThreads(false)
    }
  }

  useEffect(() => {
    if (isAuthenticated && user) {
      fetchUserThreads()
    }
    return () => stopPolling()
  }, [user, isAuthenticated])

  const handleGenerate = async () => {
    if (!prompt.trim()) return
    
    // Check authentication
    if (!isAuthenticated || !user) {
      setShowAuthModal(true)
      return
    }

    // Check quota
    if (quota && quota.blogs_remaining <= 0) {
      setShowQuotaModal(true)
      return
    }
    
    setStatus("generating_plan")
    setPlan(null)
    setArticleContent(null)
    
    try {
      const res = await fetch(`${API_BASE}/generate`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
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
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ approval: approvalStatus, suggestions: feedback })
      })
      
      startPolling(threadId)
    } catch (err) {
      console.error("Resume error:", err)
      setStatus("awaiting_approval") // revert on error
    }
  }

  const handleCopy = () => {
    if (articleContent) {
      navigator.clipboard.writeText(articleContent)
    }
  }

  const isGenerating = status === "generating_plan" || status === "generating_article"

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="mx-auto px-4 sm:px-6 lg:px-8 pb-8 w-full max-w-[1400px]">
        {/* Header and Prompt Area */}
        <div className="mx-auto transition-all duration-300 flex justify-center w-full">
          <div className="w-full max-w-3xl space-y-6">
            <div className="flex items-center justify-between">
              <Header onClear={handleClear} onCopy={handleCopy} />
              {(status !== "idle" || plan || articleContent) && (
                <Button 
                  size="sm"
                  onClick={handleClear}
                  className="bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  Create New
                </Button>
              )}
            </div>
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
        
        {/* Main Content Area */}
        <main className="mx-auto mt-6 flex flex-col lg:flex-row items-start gap-6 transition-all duration-300 justify-center w-full">
          
          {/* Center Column (Main Content) */}
          <div className={`w-full space-y-5 sm:space-y-6 ${plan ? 'lg:w-[66%]' : 'lg:w-full max-w-3xl mx-auto'}`}>
            
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
                  content={articleContent}
                  imageUrl="/images/workspace.jpg"
                />
              </div>
            )}
          </div>

          {/* Right Sidebar (Plan or Spacer) */}
          {plan ? (
            <aside className="w-full lg:w-[33%] shrink-0 sticky top-6">
              <PlanPreview 
                plan={plan} 
                onApprove={(feedback) => handleApproval("approved", feedback)}
                onReject={(feedback) => handleApproval("rejected", feedback)}
                isReadOnly={status === "generating_article" || status === "completed"}
              />
            </aside>
          ) : null}
        </main>

        {/* Footer Area */}
        <div className="mx-auto transition-all duration-300 flex justify-center w-full mt-10 sm:mt-12">
          <footer className="w-full max-w-3xl text-center">
            <p className="text-[10px] sm:text-xs text-muted-foreground">
              Generated with editorial precision by BlogAI. No tracking, no distractions.
            </p>
          </footer>
        </div>
      </div>

      {/* Modals */}
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
      <QuotaModal isOpen={showQuotaModal} onClose={() => setShowQuotaModal(false)} quota={quota || undefined} />
    </div>
  )
}
