"""
Enhanced AI Chatbot with Google Gemini Integration
Provides intelligent data analysis assistance using LLMs
Falls back to local Ollama if cloud APIs unavailable
"""
import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    GEMINI = "gemini"
    OLLAMA = "ollama"
    NONE = "none"


@dataclass
class ChatMessage:
    """Chat message structure"""
    role: str  # "user", "assistant", "system"
    content: str
    
    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}
    
    def to_gemini_format(self) -> dict:
        """Convert to Gemini API format"""
        # Gemini uses 'user' and 'model' roles
        role = "model" if self.role == "assistant" else "user"
        return {"role": role, "parts": [{"text": self.content}]}


@dataclass
class ChatConfig:
    """Chat configuration"""
    provider: LLMProvider = LLMProvider.OLLAMA
    gemini_api_key: Optional[str] = None
    ollama_host: str = "http://localhost:11434"
    model_name: str = "gemma:2b"
    gemini_model: str = "gemini-1.5-flash"  # Fast and capable model
    max_tokens: int = 2000
    temperature: float = 0.7
    system_prompt: str = """You are Nalytiq Assistant, an expert data analyst AI for Rwanda's National Institute of Statistics (NISR). 

You help users:
- Understand their data and generate insights
- Interpret statistical results and ML model outputs
- Suggest appropriate analyses and visualizations
- Explain data quality issues and how to fix them
- Provide context on Rwanda-specific indicators

Always be helpful, accurate, and explain concepts clearly. When discussing data, be specific about column names and values when available.
If you don't have enough information to answer, ask clarifying questions.
Respond in the user's language when possible (English, French, or Kinyarwanda)."""


class GeminiChat:
    """Google Gemini API integration"""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy load the Gemini client"""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model)
            except ImportError:
                logger.error("Google Generative AI package not installed. Install with: pip install google-generativeai")
                raise
        return self._client
    
    async def chat(self, messages: List[ChatMessage], max_tokens: int = 2000) -> str:
        """Send chat request to Gemini"""
        try:
            client = self._get_client()
            
            # Build the prompt with system context and conversation
            system_content = ""
            conversation_parts = []
            
            for msg in messages:
                if msg.role == "system":
                    system_content += msg.content + "\n\n"
                else:
                    conversation_parts.append(msg.to_gemini_format())
            
            # Create chat with system instruction
            chat = client.start_chat(history=conversation_parts[:-1] if len(conversation_parts) > 1 else [])
            
            # Get the last user message
            last_message = messages[-1].content if messages else ""
            
            # Combine system prompt with user message for context
            full_prompt = f"{system_content}\nUser: {last_message}" if system_content else last_message
            
            # Generate response
            response = await asyncio.to_thread(
                chat.send_message,
                full_prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": 0.7
                }
            )
            
            return response.text
            
        except ImportError:
            logger.error("Google Generative AI package not installed. Install with: pip install google-generativeai")
            raise
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise


class OllamaChat:
    """Ollama local LLM integration"""
    
    def __init__(self, host: str = "http://localhost:11434", model: str = "gemma:2b"):
        self.host = host
        self.model = model
    
    async def chat(self, messages: List[ChatMessage], max_tokens: int = 2000) -> str:
        """Send chat request to Ollama"""
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Build prompt from messages
                prompt = "\n".join([f"{m.role}: {m.content}" for m in messages])
                prompt += "\nassistant:"
                
                response = await client.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens
                        }
                    }
                )
                response.raise_for_status()
                return response.json().get("response", "")
                
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise


class EnhancedChatbot:
    """
    Enhanced chatbot with Google Gemini and Ollama providers
    Automatically falls back to available provider
    """
    
    def __init__(self, config: ChatConfig = None):
        self.config = config or ChatConfig()
        self.conversation_history: List[ChatMessage] = []
        self.data_context: Dict[str, Any] = {}
        
        # Initialize provider
        self._provider = self._init_provider()
    
    def _init_provider(self):
        """Initialize the best available provider"""
        # Try Gemini first (primary provider)
        gemini_key = self.config.gemini_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if gemini_key:
            try:
                import google.generativeai
                self.config.provider = LLMProvider.GEMINI
                logger.info("Using Google Gemini as AI provider")
                return GeminiChat(gemini_key, self.config.gemini_model)
            except ImportError:
                logger.warning("google-generativeai package not installed")
        
        # Fall back to Ollama
        try:
            self.config.provider = LLMProvider.OLLAMA
            logger.info("Using Ollama as AI provider (fallback)")
            return OllamaChat(self.config.ollama_host, self.config.model_name)
        except Exception:
            self.config.provider = LLMProvider.NONE
            logger.warning("No AI provider available")
            return None
    
    def set_data_context(self, context: Dict[str, Any]):
        """Set data context for the conversation"""
        self.data_context = context
    
    def _build_context_message(self) -> str:
        """Build context message from data"""
        if not self.data_context:
            return ""
        
        context_parts = ["Current data context:"]
        
        if "dataset_name" in self.data_context:
            context_parts.append(f"- Dataset: {self.data_context['dataset_name']}")
        
        if "columns" in self.data_context:
            context_parts.append(f"- Columns: {', '.join(self.data_context['columns'][:20])}")
        
        if "shape" in self.data_context:
            context_parts.append(f"- Rows: {self.data_context['shape'][0]}, Columns: {self.data_context['shape'][1]}")
        
        if "data_types" in self.data_context:
            dtypes = self.data_context['data_types']
            context_parts.append(f"- Data types: {json.dumps(dtypes)[:200]}")
        
        if "statistics" in self.data_context:
            stats = self.data_context['statistics']
            context_parts.append(f"- Basic statistics: {json.dumps(stats)[:300]}")
        
        if "quality_score" in self.data_context:
            context_parts.append(f"- Data quality score: {self.data_context['quality_score']}")
        
        if "insights" in self.data_context:
            insights = self.data_context['insights'][:5]
            context_parts.append(f"- Key insights: {json.dumps(insights)}")
        
        if "warnings" in self.data_context:
            warnings = self.data_context['warnings'][:3]
            context_parts.append(f"- Data warnings: {json.dumps(warnings)}")
        
        if "analysis_results" in self.data_context:
            results = self.data_context['analysis_results']
            context_parts.append(f"- Recent analysis: {json.dumps(results)[:500]}")
        
        return "\n".join(context_parts)
    
    async def chat(self, user_message: str, include_context: bool = True) -> str:
        """
        Process user message and return assistant response
        """
        if self._provider is None:
            return self._fallback_response(user_message)
        
        # Build messages
        messages = [ChatMessage(role="system", content=self.config.system_prompt)]
        
        # Add data context if available
        if include_context and self.data_context:
            context_msg = self._build_context_message()
            if context_msg:
                messages.append(ChatMessage(role="system", content=context_msg))
        
        # Add conversation history (last 10 messages)
        messages.extend(self.conversation_history[-10:])
        
        # Add user message
        user_msg = ChatMessage(role="user", content=user_message)
        messages.append(user_msg)
        self.conversation_history.append(user_msg)
        
        try:
            # Get response from provider
            response = await self._provider.chat(messages, self.config.max_tokens)
            
            # Save to history
            assistant_msg = ChatMessage(role="assistant", content=response)
            self.conversation_history.append(assistant_msg)
            
            return response
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return self._fallback_response(user_message)
    
    def _fallback_response(self, user_message: str) -> str:
        """Generate fallback response when LLM is unavailable"""
        user_lower = user_message.lower()
        
        # Pattern matching for common questions
        if any(word in user_lower for word in ["hello", "hi", "hey", "muraho"]):
            return "Hello! I'm the Nalytiq Assistant. I can help you analyze your data and understand statistical results. How can I help you today?"
        
        if "help" in user_lower:
            return """I can help you with:
• **Data Upload**: Upload CSV, Excel, or Stata files for analysis
• **Data Quality**: Understand data quality scores and fix issues
• **Analysis**: Run statistical analyses, cross-tabulations, and grouped statistics
• **Visualization**: Create charts and graphs from your data
• **Machine Learning**: Train predictive models using your data
• **Export**: Download reports in PDF, Excel, or CSV format

What would you like to explore?"""
        
        if any(word in user_lower for word in ["column", "variable", "field"]):
            if self.data_context and "columns" in self.data_context:
                cols = ", ".join(self.data_context["columns"][:15])
                more = f" (+{len(self.data_context['columns']) - 15} more)" if len(self.data_context["columns"]) > 15 else ""
                return f"Your dataset has these columns: {cols}{more}\n\nWhich columns would you like to analyze?"
        
        if any(word in user_lower for word in ["missing", "null", "empty"]):
            return "To handle missing values, you can use the Data Transformation page (/transform). Options include:\n• Fill with mean/median/mode\n• Forward/backward fill\n• Drop rows with missing values\n• Fill with a custom value"
        
        if any(word in user_lower for word in ["model", "predict", "ml", "machine learning"]):
            return """For machine learning, we support:
• **Random Forest**: Good general-purpose algorithm
• **XGBoost**: Best for structured/tabular data
• **Neural Network**: Best for complex patterns

Go to ML Training (/ml-training) to train a model. You'll need to select a target variable and features to include."""
        
        return "I'm currently running in offline mode with limited capabilities. For the best experience, please ensure the AI service is running or add your GEMINI_API_KEY to the environment. In the meantime, I can help with basic questions about data analysis."
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_provider_info(self) -> Dict[str, str]:
        """Get information about the active provider"""
        return {
            "provider": self.config.provider.value,
            "model": getattr(self._provider, "model", self.config.model_name),
            "status": "active" if self._provider else "offline"
        }


# Suggested prompts for users
SUGGESTED_PROMPTS = [
    "What columns are in my dataset?",
    "Summarize the key statistics of this data",
    "What are the main data quality issues?",
    "Which variables are most correlated?",
    "How should I clean this data?",
    "What analysis would you recommend?",
    "Explain the ML model results",
    "What insights can you find in this data?",
    "Help me understand the cross-tabulation results",
    "Compare the different categories in my data"
]


# Pre-built analysis prompts
ANALYSIS_PROMPTS = {
    "data_quality": "Analyze the data quality of this dataset. What issues exist and how can they be fixed?",
    "summary": "Provide a comprehensive summary of this dataset including key statistics and patterns.",
    "correlations": "Which variables in this dataset are most strongly correlated and what might this indicate?",
    "outliers": "Identify potential outliers in this dataset and explain their significance.",
    "recommendations": "Based on this data, what analyses would you recommend performing?",
    "model_interpret": "Explain the machine learning model results in simple terms. What are the key predictors?",
    "trend_analysis": "What trends or patterns can you identify in this time series data?",
    "segment_analysis": "How do the different segments or categories in this data compare?",
}


# Create global chatbot instance
_chatbot_instance = None


def get_chatbot(config: ChatConfig = None) -> EnhancedChatbot:
    """Get or create the global chatbot instance"""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = EnhancedChatbot(config)
    return _chatbot_instance


async def ask_chatbot(question: str, context: Dict[str, Any] = None) -> str:
    """Quick helper to ask the chatbot a question"""
    chatbot = get_chatbot()
    if context:
        chatbot.set_data_context(context)
    return await chatbot.chat(question)
