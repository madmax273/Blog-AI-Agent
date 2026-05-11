"use client"

import { useState } from "react"
import { Check, FileText, Sparkles, Send } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function BillingPage() {
  const [annual, setAnnual] = useState(false)

  const plans = [
    {
      name: "Basic",
      price: annual ? 0 : 0,
      description: "Perfect for getting started",
      features: [
        "10 blogs per month",
        "50,000 words per month",
        "Basic AI assistance",
        "Email support",
        "Standard templates"
      ],
      popular: false
    },
    {
      name: "Pro",
      price: annual ? 19 : 24,
      description: "For serious content creators",
      features: [
        "50 blogs per month",
        "250,000 words per month",
        "Advanced AI assistance",
        "Priority email support",
        "Premium templates",
        "Custom branding",
        "Analytics dashboard"
      ],
      popular: true
    },
    {
      name: "Enterprise",
      price: annual ? 49 : 59,
      description: "For teams and agencies",
      features: [
        "Unlimited blogs",
        "Unlimited words",
        "Dedicated AI assistant",
        "24/7 phone support",
        "Custom integrations",
        "White-label solution",
        "Advanced analytics",
        "Team collaboration",
        "API access"
      ],
      popular: false
    }
  ]

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4 sm:px-6 py-12">
      {/* Header */}
      <div className="text-center mb-8 sm:mb-10">
        <div className="flex justify-center mb-4">
          <div
            className="w-14 h-14 sm:w-16 sm:h-16 rounded-full flex items-center justify-center"
            style={{
              background: 'linear-gradient(145deg, #ffffff, #f8f8fc)',
              boxShadow: '8px 8px 20px #d8d8e5, -8px -8px 20px #ffffff',
            }}
          >
            <Sparkles className="w-7 h-7 sm:w-8 sm:h-8 text-primary" />
          </div>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-primary mb-2">Plans & Pricing</h1>
        <p className="text-sm sm:text-base text-muted-foreground">
          Choose the perfect plan for your needs
        </p>
      </div>

      {/* Toggle */}
      <div className="flex items-center justify-center gap-3 mb-8 sm:mb-10">
        <span className={`text-sm font-medium ${!annual ? 'text-primary' : 'text-muted-foreground'}`}>
          Monthly
        </span>
        <button
          onClick={() => setAnnual(!annual)}
          className={`relative w-14 h-7 rounded-full transition-colors duration-200 ${
            annual ? 'bg-primary' : 'bg-muted'
          }`}
          style={{
            boxShadow: annual ? '4px 4px 12px #d8d8e5, -4px -4px 12px #ffffff' : 'inset 2px 2px 6px #d8d8e5, inset -2px -2px 6px #ffffff'
          }}
        >
          <div
            className={`absolute top-1 w-5 h-5 rounded-full bg-white transition-all duration-200 ${
              annual ? 'left-8' : 'left-1'
            }`}
          />
        </button>
        <span className={`text-sm font-medium ${annual ? 'text-primary' : 'text-muted-foreground'}`}>
          Annual <span className="text-xs text-muted-foreground">(Save 20%)</span>
        </span>
      </div>

      {/* Pricing Cards */}
      <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6 mb-10 sm:mb-12">
        {plans.map((plan) => (
          <div
            key={plan.name}
            className={`relative rounded-2xl sm:rounded-3xl p-6 sm:p-8 transition-all duration-300 ${
              plan.popular 
                ? 'ring-2 ring-primary scale-105' 
                : ''
            }`}
            style={{
              background: 'linear-gradient(145deg, #ffffff, #f8f8fc)',
              boxShadow: '8px 8px 20px #d8d8e5, -8px -8px 20px #ffffff',
            }}
          >
            {plan.popular && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-xs font-semibold px-3 py-1 rounded-full">
                Most Popular
              </div>
            )}
            
            <h3 className="text-xl sm:text-2xl font-bold text-foreground mb-2">{plan.name}</h3>
            <p className="text-sm text-muted-foreground mb-4">{plan.description}</p>
            
            <div className="mb-6">
              <span className="text-3xl sm:text-4xl font-bold text-primary">${plan.price}</span>
              <span className="text-muted-foreground">/month</span>
            </div>

            <ul className="space-y-3 mb-6">
              {plan.features.map((feature) => (
                <li key={feature} className="flex items-start gap-2 text-sm text-foreground">
                  <Check className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                  <span>{feature}</span>
                </li>
              ))}
            </ul>

            <Button
              className={`w-full ${
                plan.popular 
                  ? 'bg-primary text-primary-foreground hover:bg-primary/90' 
                  : 'bg-background border border-border text-primary hover:bg-secondary/30'
              }`}
              style={
                !plan.popular 
                  ? { boxShadow: '4px 4px 12px #d8d8e5, -4px -4px 12px #ffffff' }
                  : {}
              }
            >
              {plan.name === 'Basic' ? 'Get Started' : plan.name === 'Pro' ? 'Upgrade to Pro' : 'Contact Sales'}
            </Button>
          </div>
        ))}
      </div>

      {/* Feature Cards */}
      <div className="w-full max-w-md grid grid-cols-3 gap-3 sm:gap-4 mb-10 sm:mb-12">
        {[
          { icon: FileText, label: 'DRAFT' },
          { icon: Sparkles, label: 'ENHANCE' },
          { icon: Send, label: 'PUBLISH' },
        ].map((feature) => (
          <div
            key={feature.label}
            className="aspect-square rounded-xl sm:rounded-2xl flex flex-col items-center justify-center"
            style={{
              background: 'linear-gradient(145deg, #ffffff, #f8f8fc)',
              boxShadow: '6px 6px 16px #d8d8e5, -6px -6px 16px #ffffff',
            }}
          >
            <feature.icon className="w-5 h-5 sm:w-6 sm:h-6 text-primary mb-2" />
            <span className="text-[10px] sm:text-xs font-semibold text-muted-foreground text-center px-1">
              {feature.label}
            </span>
          </div>
        ))}
      </div>

      {/* Footer */}
      <footer className="text-center text-[10px] sm:text-xs text-muted-foreground space-y-3">
        <p className="uppercase tracking-wide">Generated with editorial precision by BlogAI.</p>
        <div className="flex gap-4 justify-center text-[10px] sm:text-xs">
          <Link href="/privacy" className="hover:text-foreground transition-colors">
            Privacy Policy
          </Link>
          <span>·</span>
          <Link href="/terms" className="hover:text-foreground transition-colors">
            Terms of Service
          </Link>
          <span>·</span>
          <Link href="/support" className="hover:text-foreground transition-colors">
            Contact Support
          </Link>
        </div>
      </footer>
    </div>
  )
}
