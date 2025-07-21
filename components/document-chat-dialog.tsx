"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { useCallback } from "react"
import { Bot, FileText, Loader2, Send } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"

interface DocumentChatDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  insights?: { warnings?: string[]; insights?: string[] }
}

export function DocumentChatDialog({ open, onOpenChange, insights }: DocumentChatDialogProps) {
  const [messages, setMessages] = useState<{ role: "user" | "assistant" | "system"; content: string }[]>([
    {
      role: "system",
      content: "Document loaded: EICV6 Survey Data 2023",
    },
    {
      role: "assistant",
      content:
        "I've analyzed the EICV6 Survey Data. This dataset contains information on household living conditions across Rwanda. What specific insights would you like to explore?",
    },
  ])
  const [input, setInput] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  // Helper to send chat to backend
  const sendToBackend = useCallback(async (question: string) => {
    setIsTyping(true);
    try {
      const res = await fetch(`${BACKEND_URL}/chatbot/`, {
        method: "POST",
        headers: { "Accept": "application/json" },
        body: (() => {
          const form = new FormData();
          form.append("question", question);
          form.append("context", JSON.stringify(insights || {}));
          return form;
        })(),
      });
      if (!res.ok) throw new Error(await res.text());
      const json = await res.json();
      return json.answer || "(No answer from backend)";
    } catch (e: any) {
      return `Error: ${e.message}`;
    } finally {
      setIsTyping(false);
    }
  }, [insights]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault()

    if (!input.trim()) return

    // Add user message
    const userMessage = { role: "user" as const, content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsTyping(true)

    // Auto scroll to bottom
    setTimeout(() => {
      if (scrollAreaRef.current) {
        scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
      }
    }, 100)

    // Real backend AI response
    sendToBackend(input).then((response) => {
      setMessages((prev) => [...prev, { role: "assistant", content: response }])
      // Auto scroll to bottom after response
      setTimeout(() => {
        if (scrollAreaRef.current) {
          scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
        }
      }, 100)
    })
  }

  // Auto scroll to bottom when dialog opens
  useEffect(() => {
    if (open && scrollAreaRef.current) {
      setTimeout(() => {
        if (scrollAreaRef.current) {
          scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
        }
      }, 100)
    }
  }, [open])

  const suggestedQuestions = [
    "What is the poverty rate by province?",
    "How does education level correlate with income?",
    "What are the gender disparities in employment?",
    "Show me access to electricity by region",
    "Compare urban vs rural living conditions",
    "Generate a visualization of income distribution",
  ]

  const warnings = insights?.warnings || [];
  const highlights = insights?.insights || [];
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] max-h-[80vh] flex flex-col p-0 gap-0">
        <DialogHeader className="p-4 border-b">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-md bg-primary/10">
                <Bot className="h-5 w-5 text-primary" />
              </div>
              <div>
                <DialogTitle>Data Assistant</DialogTitle>
                <DialogDescription>Chat with your uploaded dataset</DialogDescription>
              </div>
            </div>
            <Badge variant="outline" className="flex items-center gap-1">
              <FileText className="h-3 w-3" />
              EICV6 Survey Data
            </Badge>
          </div>
        </DialogHeader>

        <Tabs defaultValue="chat" className="flex-1 flex flex-col">
          <div className="border-b px-4">
            <TabsList className="h-10">
              <TabsTrigger value="chat" className="data-[state=active]:bg-muted">
                Chat
              </TabsTrigger>
              <TabsTrigger value="insights" className="data-[state=active]:bg-muted">
                Key Insights
              </TabsTrigger>
              <TabsTrigger value="visualizations" className="data-[state=active]:bg-muted">
                Visualizations
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="chat" className="flex-1 flex flex-col p-0 m-0 data-[state=active]:flex">
            <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
              <div className="space-y-4">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${
                      message.role === "user"
                        ? "justify-end"
                        : message.role === "system"
                          ? "justify-center"
                          : "justify-start"
                    }`}
                  >
                    {message.role === "system" ? (
                      <div className="bg-muted text-xs rounded-full px-3 py-1 text-muted-foreground">
                        {message.content}
                      </div>
                    ) : (
                      <div
                        className={`rounded-lg px-4 py-2 max-w-[80%] ${
                          message.role === "user"
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted border border-border"
                        }`}
                      >
                        {message.content.split("\n").map((line, i) => (
                          <p key={i} className={i > 0 ? "mt-2" : ""}>
                            {line}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                {isTyping && (
                  <div className="flex justify-start">
                    <div className="rounded-lg px-4 py-2 max-w-[80%] bg-muted border border-border">
                      <div className="flex space-x-1">
                        <div className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce" />
                        <div className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce delay-75" />
                        <div className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce delay-150" />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {messages.length <= 2 && (
                <div className="mt-6">
                  <p className="text-sm text-muted-foreground mb-3">Suggested questions:</p>
                  <div className="flex flex-wrap gap-2">
                    {suggestedQuestions.map((question, index) => (
                      <Button
                        key={index}
                        variant="outline"
                        size="sm"
                        className="text-xs"
                        onClick={() => {
                          setInput(question)
                        }}
                      >
                        {question}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
            </ScrollArea>

            <div className="p-4 border-t bg-muted/40">
              <form onSubmit={handleSendMessage} className="flex gap-2 items-end">
                <Textarea
                  placeholder="Type your question here..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  className="flex-1 resize-none min-h-[48px] max-h-[120px] border-2 border-primary focus:border-primary focus:ring-2 focus:ring-primary/50 text-base px-4 py-2 rounded-lg bg-white shadow"
                  rows={2}
                  disabled={isTyping}
                />
                <Button
                  type="submit"
                  size="icon"
                  className="ml-2 h-12 w-12 rounded-lg bg-primary text-white shadow-lg"
                  disabled={isTyping || !input.trim()}
                  aria-label="Send message"
                >
                  {isTyping ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
                </Button>
              </form>
            </div>
          </TabsContent>

          <TabsContent value="insights" className="flex-1 p-4 overflow-auto data-[state=active]:flex-col">
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium mb-2">Automated Insights & Warnings</h3>
                <ul className="space-y-2">
                  {warnings.length === 0 && highlights.length === 0 && (
                    <li className="text-muted-foreground">No insights or warnings detected for this dataset.</li>
                  )}
                  {warnings.map((w, i) => (
                    <li key={"warn-"+i} className="text-yellow-800 dark:text-yellow-200 flex items-center gap-2"><span role="img" aria-label="warning">⚠️</span> {w}</li>
                  ))}
                  {highlights.map((h, i) => (
                    <li key={"insight-"+i} className="text-green-800 dark:text-green-200 flex items-center gap-2"><span role="img" aria-label="insight">✅</span> {h}</li>
                  ))}
                </ul>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="visualizations" className="flex-1 p-4 overflow-auto data-[state=active]:flex-col">
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium mb-2">Poverty Rate by Province</h3>
                <div className="border rounded-lg p-4 h-[300px] flex items-center justify-center bg-muted/50">
                  <div className="text-center">
                    <p className="text-muted-foreground">Visualization would appear here</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      (Bar chart showing poverty rates across provinces)
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium mb-2">Education Level vs. Income</h3>
                <div className="border rounded-lg p-4 h-[300px] flex items-center justify-center bg-muted/50">
                  <div className="text-center">
                    <p className="text-muted-foreground">Visualization would appear here</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      (Scatter plot showing correlation between education and income)
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium mb-2">Access to Utilities Over Time</h3>
                <div className="border rounded-lg p-4 h-[300px] flex items-center justify-center bg-muted/50">
                  <div className="text-center">
                    <p className="text-muted-foreground">Visualization would appear here</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      (Line chart showing electricity and water access trends)
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
