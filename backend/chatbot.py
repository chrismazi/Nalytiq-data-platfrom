import ollama

def ask_chatbot(question: str, context: dict) -> dict:
    # Build a context string from backend insights and any other relevant data
    dashboard_context = "You are a data analysis assistant. Here are the latest insights and warnings:\n"
    if context.get("warnings"):
        dashboard_context += "Warnings:\n" + "\n".join(f"- {w}" for w in context["warnings"]) + "\n"
    if context.get("insights"):
        dashboard_context += "Insights:\n" + "\n".join(f"- {i}" for i in context["insights"]) + "\n"
    dashboard_context += "\nPlease answer the user's question using this context."

    messages = [
        {"role": "system", "content": dashboard_context},
        {"role": "user", "content": question}
    ]
    response = ollama.chat(model="gemma:2b", messages=messages)
    return {"answer": response['message']['content'] if response and 'message' in response else "I couldn't generate an answer."} 