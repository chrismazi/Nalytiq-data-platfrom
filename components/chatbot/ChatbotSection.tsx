import React, { useState, useRef, useCallback } from "react";
import { Textarea } from "@/components/ui/textarea"

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

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-semibold mb-4">AI Assistant / Chatbot</h2>
      <div className="bg-white rounded-lg shadow p-6 animate-fade-in">
        <div className="mb-2">Ask questions about your data and get smart, context-aware answers here.</div>
        <div className="border rounded-lg p-4 h-64 overflow-y-auto mb-4" ref={scrollAreaRef}>
          {messages.length === 0 && <div className="text-muted-foreground">No messages yet. Ask something!</div>}
          {messages.map((msg, i) => (
            <div key={i} className={`mb-2 flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`rounded-lg px-4 py-2 max-w-[80%] ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted border border-border"}`}>{msg.content}</div>
            </div>
          ))}
          {isTyping && <div className="text-muted-foreground">AI is typing...</div>}
        </div>
        <form onSubmit={handleSendMessage} className="flex gap-2 items-end mt-2 bg-muted/40 p-2 rounded-lg">
          <Textarea
            placeholder="Type your question here..."
            value={input}
            onChange={e => setInput(e.target.value)}
            className="flex-1 resize-none min-h-[48px] max-h-[120px] border-2 border-primary focus:border-primary focus:ring-2 focus:ring-primary/50 text-base px-4 py-2 rounded-lg bg-white shadow"
            rows={2}
            disabled={isTyping}
          />
          <button
            type="submit"
            className="ml-2 h-12 w-12 rounded-lg bg-primary text-white shadow-lg flex items-center justify-center"
            disabled={isTyping || !input.trim()}
            aria-label="Send message"
          >
            {isTyping ? <span className="loader2 h-5 w-5 animate-spin" /> : <span className="send h-5 w-5" />}
          </button>
        </form>
      </div>
    </section>
  );
};

export default ChatbotSection; 