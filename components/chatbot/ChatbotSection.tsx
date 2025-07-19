import React from "react";

interface ChatbotSectionProps {
  data: any;
  columns: string[];
}

const ChatbotSection: React.FC<ChatbotSectionProps> = ({ data, columns }) => {
  // Placeholder: In the future, connect to backend chatbot and render chat UI
  return (
    <section className="mb-10">
      <h2 className="text-2xl font-semibold mb-4">AI Assistant / Chatbot</h2>
      <div className="bg-white rounded-lg shadow p-6 animate-fade-in">
        <p className="mb-2">Ask questions about your data and get smart, context-aware answers here.</p>
      </div>
    </section>
  );
};

export default ChatbotSection; 