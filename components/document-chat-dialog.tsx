"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Bot, FileText, Loader2, Send } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"

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

    // Simulate AI response
    setTimeout(() => {
      let response = ""

      if (input.toLowerCase().includes("poverty")) {
        response =
          "Based on the EICV6 data, the poverty rate in Rwanda is 38.2%, which represents a decrease from 39.1% in the previous survey. Urban areas have a poverty rate of 15.8% while rural areas are at 43.1%. The Eastern Province showed the most significant reduction in poverty levels."
      } else if (input.toLowerCase().includes("education") || input.toLowerCase().includes("literacy")) {
        response =
          "The EICV6 data shows that 73.2% of Rwanda's population aged 15 and above is literate. There's a gender gap with 77.6% literacy for males and 69.4% for females. Secondary school enrollment has increased by 12.3% compared to the previous survey period."
      } else if (input.toLowerCase().includes("income") || input.toLowerCase().includes("economic")) {
        response =
          "According to the EICV6 data, the average monthly household income is 132,684 RWF. There's significant variation by province with Kigali City having the highest average at 372,648 RWF and the Eastern Province having the lowest at 89,456 RWF. Non-farm wage employment has increased by 8.2% since the last survey."
      } else if (input.toLowerCase().includes("electricity") || input.toLowerCase().includes("water")) {
        response =
          "The EICV6 data indicates that 51.2% of households have access to electricity, up from 27.1% in the previous survey. For clean water access, 87.4% of households have access to an improved water source, though only 12.3% have piped water directly to their dwelling or yard."
      } else if (input.toLowerCase().includes("gender") || input.toLowerCase().includes("women")) {
        response =
          "Gender analysis of the EICV6 data shows that female-headed households (23.1% of all households) have a higher poverty rate (42.6%) compared to male-headed households (36.8%). Women's participation in the labor force is 84.3%, slightly lower than men's at 87.6%."
      } else if (
        input.toLowerCase().includes("chart") ||
        input.toLowerCase().includes("graph") ||
        input.toLowerCase().includes("visualization")
      ) {
        response =
          "I can create visualizations based on the EICV6 data. Here's a breakdown of poverty rates by province:\n\n- Kigali City: 13.9%\n- Southern Province: 41.4%\n- Western Province: 41.6%\n- Northern Province: 42.3%\n- Eastern Province: 37.4%\n\nWould you like me to generate a bar chart or another type of visualization for this data?"
      } else if (input.toLowerCase().includes("compare") || input.toLowerCase().includes("correlation")) {
        response =
          "Analyzing correlations in the EICV6 data, I found a strong positive correlation (r=0.78) between education level and household income. There's also a notable correlation between access to electricity and internet usage (r=0.65), suggesting infrastructure dependencies. Would you like me to explore other correlations?"
      } else {
        response =
          "Based on my analysis of the EICV6 data, I can provide insights on poverty rates, education levels, income distribution, access to utilities, gender disparities, and regional variations. What specific aspect would you like me to elaborate on?"
      }

      setMessages((prev) => [...prev, { role: "assistant", content: response }])
      setIsTyping(false)

      // Auto scroll to bottom after response
      setTimeout(() => {
        if (scrollAreaRef.current) {
          scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
        }
      }, 100)
    }, 2000)
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

            <div className="p-4 border-t">
              <form onSubmit={handleSendMessage} className="flex gap-2">
                <Input
                  placeholder="Ask a question about your data..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  className="flex-1"
                />
                <Button type="submit" size="icon" disabled={isTyping || !input.trim()}>
                  {isTyping ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
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
