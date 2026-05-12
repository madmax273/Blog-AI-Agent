"use client"

import { useState, useEffect } from "react"
import { Navbar } from "@/components/blog-ai/navbar"
import { useAuthStore } from "@/stores/authStore"
import { AuthModal } from "@/components/auth-modal"
import { Calendar, Clock, FileText, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { useRouter } from "next/navigation"

const API_BASE = "http://localhost:8000/api/v1/blog"

export default function PreviousBlogsPage() {
  const router = useRouter()
  const { user, token, isAuthenticated, isLoading: authLoading } = useAuthStore()
  const [threads, setThreads] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showAuthModal, setShowAuthModal] = useState(false)

  const fetchThreads = async () => {
    if (!user) return
    setIsLoading(true)
    try {
      const res = await fetch(`${API_BASE}/threads`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) {
        console.error("Threads API error:", res.status, res.statusText)
        setThreads([])
        return
      }
      const data = await res.json()
      setThreads(data.threads || [])
    } catch (err) {
      console.error("Error fetching user threads:", err)
      setThreads([])
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    // Wait for auth to load before checking
    if (authLoading) return
    
    if (!isAuthenticated) {
      setShowAuthModal(true)
      return
    }
    fetchThreads()
  }, [isAuthenticated, user, authLoading])

  const formatDate = (dateString: string) => {
    if (!dateString) return "Recently"
    const date = new Date(dateString)
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric"
    })
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full max-w-[1400px]">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-primary mb-2">Previous Blogs</h1>
          <p className="text-muted-foreground">View and manage your previously generated blog articles</p>
        </div>

        {/* Loading State */}
        {isLoading ? (
          <div className="text-center py-16">
            <div className="animate-pulse text-muted-foreground">Loading your blogs...</div>
          </div>
        ) : threads.length === 0 ? (
          /* Empty State */
          <div className="text-center py-16">
            <FileText className="h-16 w-16 text-primary mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-foreground mb-2">No blogs yet</h3>
            <p className="text-muted-foreground mb-6">You haven't generated any blog articles yet.</p>
            <Button onClick={() => router.push("/")}>
              <ArrowRight className="mr-2 h-4 w-4" />
              Generate Your First Blog
            </Button>
          </div>
        ) : (
          /* Blogs Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {threads.map((thread) => (
              <div
                key={thread.thread_id}
                className="flex flex-col rounded-2xl overflow-hidden bg-card border border-border shadow-sm hover:shadow-md cursor-pointer transition-all hover:border-primary/30 group"
                onClick={() => router.push(`/blog/${thread.thread_id}`)}
              >
                {/* Image */}
                <div className="w-full h-48 overflow-hidden bg-muted">
                  <img
                    src={
                      thread.image_urls && thread.image_urls.length > 0
                        ? (typeof thread.image_urls[0] === "string"
                            ? thread.image_urls[0]
                            : thread.image_urls[0]?.unsplash_url
                              || thread.image_urls[0]?.url
                              || thread.image_urls[0]?.regular
                              || "/images/workspace.jpg")
                        : "/images/workspace.jpg"
                    }
                    alt={thread.topic}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = "/images/workspace.jpg"
                    }}
                  />
                </div>

                {/* Content */}
                <div className="p-5 flex-1 flex flex-col">
                  <h3 className="text-lg font-semibold text-primary leading-snug line-clamp-2 mb-3">
                    {thread.title || thread.topic || "Untitled Blog"}
                  </h3>

                  {/* Metadata */}
                  <div className="flex items-center gap-4 text-xs text-muted-foreground mb-4">
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      <span>{formatDate(thread.created_at)}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      <span className={`capitalize ${
                        thread.status === 'completed' ? 'text-green-600' :
                        thread.status === 'processing' ? 'text-yellow-600' :
                        'text-muted-foreground'
                      }`}>
                        {thread.status || 'Unknown'}
                      </span>
                    </div>
                  </div>

                  {/* Status Badge */}
                  <div className="mt-auto">
                    <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                      thread.status === 'completed'
                        ? 'bg-green-100 text-green-700'
                        : thread.status === 'processing'
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {thread.status === 'completed' ? 'Completed' :
                       thread.status === 'processing' ? 'Processing' :
                       thread.status || 'Unknown'}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Auth Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
      />
    </div>
  )
}
