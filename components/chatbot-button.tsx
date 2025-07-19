"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Bot, X, Send, Loader2, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export function ChatbotButton() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<{ role: "user" | "assistant" | "system"; content: string }[]>([
    {
      role: "assistant",
      content:
        "Hello! I'm your NISR AI assistant. I can help you with questions about Rwanda's statistics, surveys, and reports. How can I assist you today?",
    },
  ])
  const [input, setInput] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [activeTab, setActiveTab] = useState("chat")
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

      if (input.toLowerCase().includes("inflation")) {
        response =
          "Rwanda's inflation rate was 4.2% as of the latest data from April 2023. This represents a slight increase from the previous month's 3.9%. The main contributors to this increase were food and non-alcoholic beverages, housing, and transportation costs."
      } else if (input.toLowerCase().includes("eicv")) {
        response =
          "The EICV (Integrated Household Living Conditions Survey) is Rwanda's main survey for monitoring poverty and living conditions. The latest completed survey was EICV6, conducted in 2018-2019. It showed that the poverty rate decreased to 38.2% from 39.1% in the previous survey."
      } else if (input.toLowerCase().includes("population")) {
        response =
          "According to the latest estimates, Rwanda's population is approximately 13.2 million people, with an annual growth rate of 2.4%. The population is relatively young, with about 40% under the age of 15."
      } else if (input.toLowerCase().includes("gdp") || input.toLowerCase().includes("economic growth")) {
        response =
          "Rwanda's GDP growth rate was 7.8% in 2022, showing strong recovery after the pandemic slowdown. The services sector contributed 47% to GDP, followed by agriculture at 26% and industry at 18%. The government projects growth of 6.5-7.5% for 2023."
      } else if (input.toLowerCase().includes("education") || input.toLowerCase().includes("literacy")) {
        response =
          "Rwanda's literacy rate stands at 73.2% for the population aged 15 and above. Primary school enrollment is at 98.5%, while secondary school enrollment is at 42.3%. The government has prioritized education with 15% of the national budget allocated to the sector."
      } else if (input.toLowerCase().includes("health") || input.toLowerCase().includes("healthcare")) {
        response =
          "Rwanda has made significant progress in healthcare with life expectancy increasing to 69.2 years. Infant mortality has decreased to 27 per 1,000 live births. Over 90% of the population is covered by health insurance, primarily through the community-based health insurance scheme (Mutuelle de Santé)."
      } else {
        response =
          "Thank you for your question. Based on NISR's latest data, I can provide you with detailed information on various national statistics including demographics, economic indicators, social metrics, and more. Could you please specify which area you're interested in?"
      }

      setMessages((prev) => [...prev, { role: "assistant", content: response }])
      setIsTyping(false)

      // Auto scroll to bottom after response
      setTimeout(() => {
        if (scrollAreaRef.current) {
          scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
        }
      }, 100)
    }, 1500)
  }

  // Auto scroll to bottom when chat opens
  useEffect(() => {
    if (isOpen && scrollAreaRef.current) {
      setTimeout(() => {
        if (scrollAreaRef.current) {
          scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
        }
      }, 100)
    }
  }, [isOpen, activeTab])

  const suggestedQuestions = [
    "What is Rwanda's current inflation rate?",
    "Tell me about the EICV survey",
    "What is the population of Rwanda?",
    "What was Rwanda's GDP growth in 2022?",
    "What is the literacy rate in Rwanda?",
    "Tell me about healthcare in Rwanda",
  ]

  const recentReports = [
    {
      title: "Rwanda Economic Outlook 2023",
      date: "May 2, 2023",
      pages: 48,
    },
    {
      title: "Population Health Survey Results",
      date: "April 18, 2023",
      pages: 36,
    },
    {
      title: "Education Statistics Annual Report",
      date: "March 30, 2023",
      pages: 52,
    },
  ]

  return (
    <>
      <Button
        className="fixed bottom-6 right-6 rounded-full h-14 w-14 shadow-lg z-50"
        onClick={() => setIsOpen(true)}
        aria-label="Open AI Assistant"
      >
        <Bot className="h-6 w-6" />
      </Button>

      {isOpen && (
        <Card className="fixed bottom-6 right-6 w-80 md:w-[400px] h-[600px] shadow-xl flex flex-col animate-in z-50">
          <CardHeader className="border-b px-4 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-md bg-primary/10">
                  <Bot className="h-5 w-5 text-primary" />
                </div>
                <CardTitle className="text-lg font-medium">NISR AI Assistant</CardTitle>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setIsOpen(false)} aria-label="Close">
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>

          <Tabs defaultValue="chat" className="flex-1 flex flex-col" onValueChange={setActiveTab}>
            <div className="border-b px-4">
              <TabsList className="h-10">
                <TabsTrigger value="chat" className="data-[state=active]:bg-muted">
                  Chat
                </TabsTrigger>
                <TabsTrigger value="reports" className="data-[state=active]:bg-muted">
                  Reports
                </TabsTrigger>
                <TabsTrigger value="datasets" className="data-[state=active]:bg-muted">
                  Datasets
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="chat" className="flex-1 flex flex-col p-0 m-0 data-[state=active]:flex">
              <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
                <div className="space-y-4">
                  {messages.map((message, index) => (
                    <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div
                        className={`rounded-lg px-4 py-2 max-w-[80%] ${
                          message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                        }`}
                      >
                        {message.content}
                      </div>
                    </div>
                  ))}
                  {isTyping && (
                    <div className="flex justify-start">
                      <div className="rounded-lg px-4 py-2 max-w-[80%] bg-muted">
                        <div className="flex space-x-1">
                          <div className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce" />
                          <div className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce delay-75" />
                          <div className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce delay-150" />
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {messages.length <= 1 && (
                  <div className="mt-6">
                    <p className="text-sm text-muted-foreground mb-3">Try asking:</p>
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

              <CardFooter className="border-t p-4">
                <form onSubmit={handleSendMessage} className="flex w-full gap-2">
                  <Input
                    placeholder="Ask a question..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    className="flex-1"
                  />
                  <Button type="submit" size="icon" disabled={isTyping || !input.trim()}>
                    {isTyping ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  </Button>
                </form>
              </CardFooter>
            </TabsContent>

            <TabsContent value="reports" className="flex-1 p-4 overflow-auto data-[state=active]:flex-col">
              <div className="space-y-4">
                <h3 className="text-sm font-medium">Recent Reports</h3>
                {recentReports.map((report, index) => (
                  <div key={index} className="border rounded-lg p-3 hover:bg-muted/50 cursor-pointer transition-colors">
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-md bg-primary/10">
                        <FileText className="h-4 w-4 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium text-sm">{report.title}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <p className="text-xs text-muted-foreground">{report.date}</p>
                          <Badge variant="outline" className="text-xs">
                            {report.pages} pages
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                <div className="mt-4">
                  <h3 className="text-sm font-medium mb-2">Ask about reports</h3>
                  <div className="space-y-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full justify-start text-sm"
                      onClick={() => {
                        setActiveTab("chat")
                        setInput("Summarize the Rwanda Economic Outlook 2023")
                      }}
                    >
                      Summarize the Rwanda Economic Outlook 2023
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full justify-start text-sm"
                      onClick={() => {
                        setActiveTab("chat")
                        setInput("What are the key findings from the Health Survey?")
                      }}
                    >
                      What are the key findings from the Health Survey?
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full justify-start text-sm"
                      onClick={() => {
                        setActiveTab("chat")
                        setInput("Compare education statistics from 2022 to 2023")
                      }}
                    >
                      Compare education statistics from 2022 to 2023
                    </Button>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="datasets" className="flex-1 p-4 overflow-auto data-[state=active]:flex-col">
              <div className="space-y-4">
                <h3 className="text-sm font-medium">Available Datasets</h3>
                {[
                  {
                    name: "EICV6 Survey Data",
                    type: "Household Survey",
                    records: "12,456 households",
                  },
                  {
                    name: "Health Indicators 2022",
                    type: "Health Statistics",
                    records: "5,234 records",
                  },
                  {
                    name: "Economic Census 2023",
                    type: "Economic Data",
                    records: "28,912 businesses",
                  },
                ].map((dataset, index) => (
                  <div key={index} className="border rounded-lg p-3 hover:bg-muted/50 cursor-pointer transition-colors">
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-md bg-primary/10">
                        <FileText className="h-4 w-4 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium text-sm">{dataset.name}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <p className="text-xs text-muted-foreground">{dataset.type}</p>
                          <Badge variant="outline" className="text-xs">
                            {dataset.records}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                <div className="mt-4">
                  <h3 className="text-sm font-medium mb-2">Ask about datasets</h3>
                  <div className="space-y-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full justify-start text-sm"
                      onClick={() => {
                        setActiveTab("chat")
                        setInput("What variables are in the EICV6 Survey?")
                      }}
                    >
                      What variables are in the EICV6 Survey?
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full justify-start text-sm"
                      onClick={() => {
                        setActiveTab("chat")
                        setInput("Show me correlations in the Health Indicators dataset")
                      }}
                    >
                      Show me correlations in the Health Indicators dataset
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full justify-start text-sm"
                      onClick={() => {
                        setActiveTab("chat")
                        setInput("Generate a visualization from the Economic Census")
                      }}
                    >
                      Generate a visualization from the Economic Census
                    </Button>
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </Card>
      )}
    </>
  )
}
