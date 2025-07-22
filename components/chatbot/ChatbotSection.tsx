import React, { useState, useRef, useCallback, useEffect } from "react";
import { Textarea } from "@/components/ui/textarea"
import { Bot, User } from "lucide-react"

interface ChatbotSectionProps {
  data: any;
  columns: string[];
}

const ChatbotSection: React.FC<ChatbotSectionProps> = ({ data, columns }) => {
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: string }[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  const sendToBackend = useCallback(async (question: string) => {
    setIsTyping(true);
    try {
      const res = await fetch(`${BACKEND_URL}/chatbot/`, {
        method: "POST",
        headers: { "Accept": "application/json" },
        body: (() => {
          const form = new FormData();
          form.append("question", question);
          form.append("context", JSON.stringify(data?.insights || {}));
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
  }, [data]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setMessages((prev) => [...prev, { role: "user", content: input }]);
    setInput("");
    setIsTyping(true);
    setTimeout(() => {
      if (scrollAreaRef.current) {
        scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
      }
    }, 100);
    const response = await sendToBackend(input);
    setMessages((prev) => [...prev, { role: "assistant", content: response }]);
    setTimeout(() => {
      if (scrollAreaRef.current) {
        scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
      }
    }, 100);
  };

  // Scroll to bottom on new message
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  return (
    <section className="mb-10">
      <div className="max-w-2xl mx-auto w-full">
        <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-xl border border-border flex flex-col h-[500px] md:h-[600px] relative">
          <div className="flex items-center gap-3 px-6 py-4 border-b border-border bg-muted rounded-t-2xl">
            <Bot className="h-6 w-6 text-primary" />
            <h2 className="text-lg font-semibold">Nalytiq AI Chatbot</h2>
          </div>
          <div
            ref={scrollAreaRef}
            className="flex-1 overflow-y-auto px-4 py-4 space-y-2 bg-background scrollbar-thin scrollbar-thumb-muted/60 scrollbar-track-transparent"
            tabIndex={0}
            aria-label="Chat messages"
          >
            {messages.length === 0 && <div className="text-muted-foreground text-center mt-10">No messages yet. Ask something!</div>}
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`flex items-end gap-2 max-w-[80%] ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                  {msg.role === "assistant" && <Bot className="h-5 w-5 text-primary mb-1" />}
                  {msg.role === "user" && <User className="h-5 w-5 text-muted-foreground mb-1" />}
                  <div className={`rounded-xl px-4 py-2 text-base shadow-sm ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted border border-border text-foreground"}`}>{msg.content}</div>
                </div>
              </div>
            ))}
            {isTyping && <div className="text-muted-foreground text-center">Nalytiq AI is typing...</div>}
          </div>
          <form onSubmit={handleSendMessage} className="flex gap-2 items-end p-4 border-t border-border bg-background sticky bottom-0 z-10">
            <Textarea
              placeholder="Type your question here..."
              value={input}
              onChange={e => setInput(e.target.value)}
              className="flex-1 resize-none min-h-[48px] max-h-[120px] border-2 border-primary focus:border-primary focus:ring-2 focus:ring-primary/50 text-base px-4 py-2 rounded-lg bg-white dark:bg-zinc-800 shadow"
              rows={2}
              disabled={isTyping}
              aria-label="Chat input"
            />
            <button
              type="submit"
              className="ml-2 h-12 w-12 rounded-lg bg-primary text-white shadow-lg flex items-center justify-center"
              disabled={isTyping || !input.trim()}
              aria-label="Send message"
            >
              {isTyping ? <span className="loader2 h-5 w-5 animate-spin" /> : <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M22 2L11 13" /><path d="M22 2L15 22L11 13L2 9L22 2Z" /></svg>}
            </button>
          </form>
        </div>
      </div>
    </section>
  );
};

export default ChatbotSection; 