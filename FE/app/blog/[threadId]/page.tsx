"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { Navbar } from "@/components/blog-ai/navbar"
import { Calendar, Clock, ArrowLeft, FileText, Copy, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/stores/authStore"

const API_BASE = "http://localhost:8000/api/v1/blog"

export default function BlogDetailPage() {
  const params = useParams()
  const router = useRouter()
  const { token, isAuthenticated, isLoading: authLoading } = useAuthStore()
  const [blog, setBlog] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [showAuthModal, setShowAuthModal] = useState(false)

  const fetchBlog = async () => {
    if (!params.threadId) return
    setIsLoading(true)
    try {
      const res = await fetch(`${API_BASE}/threads/${params.threadId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) {
        console.error("Blog API error:", res.status, res.statusText)
        return
      }
      const data = await res.json()
      setBlog(data)
    } catch (err) {
      console.error("Error fetching blog:", err)
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
    fetchBlog()
  }, [isAuthenticated, authLoading, params.threadId])

  const formatDate = (dateString: string) => {
    if (!dateString) return "Recently"
    const date = new Date(dateString)
    return date.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    })
  }

  const handleCopy = () => {
    if (blog?.content) {
      navigator.clipboard.writeText(blog.content)
    }
  }

  const handleBack = () => {
    router.push("/previous-blogs")
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="animate-pulse text-muted-foreground">Loading blog...</div>
        </div>
      </div>
    )
  }

  if (!blog) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <FileText className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground mb-6">Blog not found</p>
            <button
              onClick={handleBack}
              className="px-4 py-2 text-primary hover:text-primary/80 transition-colors rounded-lg hover:bg-primary/10"
            >
              <ArrowLeft className="mr-2 h-4 w-4 inline" />
              Back to Previous Blogs
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Check if blog is completed
  if (blog.status !== 'completed') {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div
              className="w-20 h-20 sm:w-24 sm:h-24 rounded-full flex items-center justify-center mx-auto mb-6"
              style={{
                background: 'linear-gradient(145deg, #ffffff, #f8f8fc)',
                boxShadow: '8px 8px 20px #d8d8e5, -8px -8px 20px #ffffff',
              }}
            >
              <Clock className="w-10 h-10 sm:w-12 sm:h-12 text-primary" />
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-foreground mb-2">Blog Not Processed Yet</h2>
            <p className="text-muted-foreground mb-6">
              This blog is still being generated. Please check back later.
            </p>
            <button
              onClick={handleBack}
              className="px-4 py-2 text-primary hover:text-primary/80 transition-colors rounded-lg hover:bg-primary/10"
            >
              <ArrowLeft className="mr-2 h-4 w-4 inline" />
              Back to Previous Blogs
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full max-w-4xl">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-sm sm:text-base text-primary hover:text-primary/80 transition-colors mb-4"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Previous Blogs
          </button>
          
          <div
            className="w-full rounded-2xl sm:rounded-3xl p-6 sm:p-8 md:p-10"
            style={{
              background: 'linear-gradient(145deg, #ffffff, #f8f8fc)',
              boxShadow: '8px 8px 20px #d8d8e5, -8px -8px 20px #ffffff',
            }}
          >
            {/* Blog Title */}
            <h1 className="text-2xl sm:text-3xl font-bold text-primary mb-4">
              {blog.title || blog.topic || "Untitled Blog"}
            </h1>

            {/* Metadata */}
            <div className="flex flex-wrap items-center gap-4 sm:gap-6 text-xs sm:text-sm text-muted-foreground mb-6 pb-6 border-b border-border">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-primary" />
                <span>{formatDate(blog.created_at)}</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-primary" />
                <span className={`capitalize ${
                  blog.status === 'completed' ? 'text-green-600' :
                  blog.status === 'processing' ? 'text-yellow-600' :
                  'text-muted-foreground'
                }`}>
                  {blog.status || 'Unknown'}
                </span>
              </div>
              <div className="flex items-center gap-2 ml-auto">
                <button
                  onClick={handleCopy}
                  className="p-2 text-primary hover:text-primary/80 transition-colors rounded-lg hover:bg-primary/10"
                >
                  <Copy className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Blog Content */}
            <div
              className="prose prose-sm sm:prose-base max-w-none text-foreground"
              dangerouslySetInnerHTML={{ __html: blog.content || blog.markdown_content || "" }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
