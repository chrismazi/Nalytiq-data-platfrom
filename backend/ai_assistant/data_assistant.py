"""Intelligent Data Assistant.

Unified interface for AI-powered data platform assistance.
Combines RAG, NL-to-SQL, and specialized agents for comprehensive
data discovery, analysis, and reporting support.

This module provides the main user-facing AI interface following
Google design principles for production systems.

Example usage:
    assistant = get_data_assistant()
    
    # General Q&A
    answer = await assistant.ask("What datasets contain population data?")
    
    # Data query
    query = await assistant.query_data("Show population by province")
    
    # Recommendations
    recs = await assistant.recommend_datasets(
        purpose="health analysis",
        organization="MOH"
    )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .rag_engine import RAGEngine, RAGResponse, get_rag_engine
from .nl_to_sql import NLToSQLConverter, NLToSQLResult, get_nl_to_sql_converter
from .vector_store import Document, get_vector_store

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """Types of user intents the assistant can handle."""
    QUESTION = "question"           # General Q&A about data/platform
    DATA_QUERY = "data_query"       # Request to query actual data
    RECOMMENDATION = "recommendation"  # Request for dataset recommendations
    EXPLANATION = "explanation"     # Explain a concept or result
    COMPARISON = "comparison"       # Compare datasets or values
    TREND_ANALYSIS = "trend"        # Analyze trends over time
    HELP = "help"                   # General help request
    UNKNOWN = "unknown"


@dataclass
class AssistantResponse:
    """Response from the data assistant.
    
    Attributes:
        message: The main response text.
        intent: Detected user intent.
        data: Any structured data in the response.
        sql: Generated SQL if applicable.
        sources: Source documents used.
        suggestions: Follow-up suggestions.
        confidence: Overall confidence score.
    """
    message: str
    intent: IntentType
    data: Optional[Dict[str, Any]] = None
    sql: Optional[str] = None
    sources: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "message": self.message,
            "intent": self.intent.value,
            "data": self.data,
            "sql": self.sql,
            "sources": self.sources,
            "suggestions": self.suggestions,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


class IntentClassifier:
    """Classifies user intent from natural language.
    
    Uses keyword matching and patterns as a fast first-pass classifier.
    For production, consider fine-tuned classification model.
    """
    
    # Keywords for each intent type
    INTENT_PATTERNS = {
        IntentType.DATA_QUERY: [
            "show me", "get", "list", "query", "fetch", "retrieve",
            "how many", "count", "sum", "average", "total",
            "by province", "by district", "by year", "by month",
            "group by", "order by", "top", "bottom",
        ],
        IntentType.RECOMMENDATION: [
            "recommend", "suggest", "which dataset", "what data",
            "should i use", "best dataset", "relevant data",
            "find data for", "data about",
        ],
        IntentType.EXPLANATION: [
            "explain", "what is", "what does", "describe",
            "tell me about", "define", "meaning of",
            "how does", "why is",
        ],
        IntentType.COMPARISON: [
            "compare", "difference between", "vs", "versus",
            "better", "worse", "higher", "lower",
            "more than", "less than",
        ],
        IntentType.TREND_ANALYSIS: [
            "trend", "over time", "change", "growth",
            "increase", "decrease", "forecast", "predict",
            "historical", "timeline",
        ],
        IntentType.HELP: [
            "help", "how to", "how do i", "guide",
            "tutorial", "getting started", "assistance",
        ],
    }
    
    def classify(self, text: str) -> IntentType:
        """Classify intent from user text.
        
        Args:
            text: User input text.
            
        Returns:
            Detected intent type.
        """
        text_lower = text.lower()
        
        # Score each intent
        scores = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            score = sum(1 for p in patterns if p in text_lower)
            scores[intent] = score
        
        # Get highest scoring intent
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        # Default to question if contains question mark
        if "?" in text:
            return IntentType.QUESTION
        
        return IntentType.UNKNOWN


class DataAssistant:
    """Intelligent assistant for the data platform.
    
    Provides a unified interface for:
    - Natural language Q&A about data and platform
    - Converting questions to data queries
    - Dataset recommendations
    - Trend analysis and insights
    - Platform help and guidance
    
    Example:
        assistant = DataAssistant()
        
        # Ask a question
        response = await assistant.ask(
            "What is the most accessed dataset this month?"
        )
        
        # Query data
        response = await assistant.query_data(
            "Show population by province for 2024"
        )
    """
    
    def __init__(
        self,
        rag_engine: Optional[RAGEngine] = None,
        sql_converter: Optional[NLToSQLConverter] = None,
    ):
        """Initialize the assistant.
        
        Args:
            rag_engine: RAG engine for Q&A.
            sql_converter: NL-to-SQL converter for data queries.
        """
        self._rag = rag_engine or get_rag_engine()
        self._sql = sql_converter or get_nl_to_sql_converter()
        self._classifier = IntentClassifier()
        
        # Conversation history (per session)
        self._history: List[Dict[str, str]] = []
    
    async def ask(
        self,
        question: str,
        context_filter: Optional[Dict[str, Any]] = None,
        auto_route: bool = True
    ) -> AssistantResponse:
        """Ask a question to the assistant.
        
        This is the main entry point. It automatically classifies
        the intent and routes to the appropriate handler.
        
        Args:
            question: User's question or request.
            context_filter: Filter for document retrieval.
            auto_route: Whether to auto-route based on intent.
            
        Returns:
            AssistantResponse with answer and metadata.
        """
        # Classify intent
        intent = self._classifier.classify(question)
        
        # Add to history
        self._history.append({"role": "user", "content": question})
        
        # Route to appropriate handler
        if auto_route:
            if intent == IntentType.DATA_QUERY:
                return await self.query_data(question)
            elif intent == IntentType.RECOMMENDATION:
                return await self._handle_recommendation(question)
            elif intent == IntentType.EXPLANATION:
                return await self._handle_explanation(question, context_filter)
            elif intent == IntentType.COMPARISON:
                return await self._handle_comparison(question, context_filter)
            elif intent == IntentType.TREND_ANALYSIS:
                return await self._handle_trend(question)
            elif intent == IntentType.HELP:
                return self._handle_help(question)
        
        # Default: Use RAG for general questions
        rag_response = await self._rag.query(
            query=question,
            context_filter=context_filter
        )
        
        # Build suggestions based on intent
        suggestions = self._generate_suggestions(question, intent)
        
        response = AssistantResponse(
            message=rag_response.answer,
            intent=intent,
            sources=[
                {
                    "content": s.document.content[:200],
                    "metadata": s.document.metadata,
                    "score": s.score,
                }
                for s in rag_response.sources[:3]
            ],
            suggestions=suggestions,
            confidence=rag_response.confidence,
            metadata=rag_response.metadata,
        )
        
        # Add to history
        self._history.append({"role": "assistant", "content": response.message})
        
        return response
    
    async def query_data(
        self,
        question: str,
        tables: Optional[List[str]] = None,
        execute: bool = False
    ) -> AssistantResponse:
        """Convert question to SQL query.
        
        Args:
            question: Natural language data question.
            tables: Specific tables to query.
            execute: Whether to execute the query (future feature).
            
        Returns:
            AssistantResponse with SQL and metadata.
        """
        # Generate SQL
        sql_result = await self._sql.convert(
            question=question,
            tables=tables
        )
        
        if not sql_result.sql:
            return AssistantResponse(
                message="I couldn't generate a valid SQL query for that question. Could you rephrase it?",
                intent=IntentType.DATA_QUERY,
                confidence=0.0,
                suggestions=[
                    "Try being more specific about which data you need",
                    "Specify the table or dataset name",
                    "Use format like 'Show X from Y where Z'",
                ],
            )
        
        # Build friendly message
        message = (
            f"Here's the SQL query for your question:\n\n"
            f"```sql\n{sql_result.sql}\n```\n\n"
            f"{sql_result.explanation}"
        )
        
        if sql_result.warnings:
            message += f"\n\n⚠️ Warnings: {', '.join(sql_result.warnings)}"
        
        return AssistantResponse(
            message=message,
            intent=IntentType.DATA_QUERY,
            data={
                "tables_used": sql_result.tables_used,
                "is_safe": sql_result.is_safe,
            },
            sql=sql_result.sql,
            suggestions=[
                "Run this query on the database",
                "Modify this query to filter by date",
                "Add aggregations like COUNT or SUM",
            ],
            confidence=sql_result.confidence,
            metadata=sql_result.metadata,
        )
    
    async def recommend_datasets(
        self,
        purpose: str,
        organization: Optional[str] = None,
        category: Optional[str] = None,
        max_results: int = 5
    ) -> AssistantResponse:
        """Recommend datasets for a specific purpose.
        
        Args:
            purpose: What the data will be used for.
            organization: Requesting organization.
            category: Preferred data category.
            max_results: Maximum recommendations.
            
        Returns:
            AssistantResponse with recommendations.
        """
        # Build query from purpose
        query = f"datasets for {purpose}"
        if category:
            query += f" in {category} category"
        
        # Search in knowledge base
        filter_fn = None
        if category:
            filter_fn = lambda doc: doc.metadata.get("category") == category
        
        results = self._rag._vector_store.similarity_search(
            query=query,
            k=max_results,
            filter_fn=filter_fn
        )
        
        if not results:
            message = (
                f"I couldn't find datasets specifically for '{purpose}'. "
                "Here are some suggestions:\n\n"
                "1. Check the data catalog for available datasets\n"
                "2. Contact NISR for custom data requests\n"
                "3. Use the federation feature to discover partner datasets"
            )
            recommendations = []
        else:
            recommendations = [
                {
                    "name": r.document.metadata.get("name", "Unknown"),
                    "description": r.document.content[:200],
                    "relevance_score": r.score,
                    "metadata": r.document.metadata,
                }
                for r in results
            ]
            
            message = f"Based on your purpose '{purpose}', here are my recommendations:\n\n"
            for i, rec in enumerate(recommendations, 1):
                message += f"{i}. **{rec['name']}** (relevance: {rec['relevance_score']:.0%})\n"
                message += f"   {rec['description'][:100]}...\n\n"
        
        return AssistantResponse(
            message=message,
            intent=IntentType.RECOMMENDATION,
            data={"recommendations": recommendations},
            suggestions=[
                "Request access to a recommended dataset",
                "Compare datasets side by side",
                "View dataset schema and samples",
            ],
            confidence=0.8 if results else 0.3,
        )
    
    async def _handle_recommendation(
        self,
        question: str
    ) -> AssistantResponse:
        """Handle recommendation intent."""
        # Extract purpose from question
        purpose = question.lower().replace("recommend", "").replace("suggest", "").strip()
        return await self.recommend_datasets(purpose=purpose)
    
    async def _handle_explanation(
        self,
        question: str,
        context_filter: Optional[Dict[str, Any]] = None
    ) -> AssistantResponse:
        """Handle explanation requests."""
        rag_response = await self._rag.query(
            query=question,
            context_filter=context_filter
        )
        
        return AssistantResponse(
            message=rag_response.answer,
            intent=IntentType.EXPLANATION,
            sources=[
                {
                    "content": s.document.content[:200],
                    "metadata": s.document.metadata,
                    "score": s.score,
                }
                for s in rag_response.sources[:3]
            ],
            suggestions=[
                "Ask for more details",
                "Request practical examples",
                "See related topics",
            ],
            confidence=rag_response.confidence,
        )
    
    async def _handle_comparison(
        self,
        question: str,
        context_filter: Optional[Dict[str, Any]] = None
    ) -> AssistantResponse:
        """Handle comparison requests."""
        # For comparisons, try to generate a SQL query
        sql_result = await self._sql.convert(question)
        
        message = f"To compare the data you mentioned:\n\n"
        
        if sql_result.sql:
            message += f"```sql\n{sql_result.sql}\n```\n\n"
            message += "This query will help you compare the values."
        else:
            message += "I couldn't generate a comparison query. Please specify which metrics to compare."
        
        return AssistantResponse(
            message=message,
            intent=IntentType.COMPARISON,
            sql=sql_result.sql if sql_result.sql else None,
            suggestions=[
                "Specify the comparison criteria",
                "Add time period for comparison",
                "Include percentage change calculation",
            ],
            confidence=sql_result.confidence if sql_result.sql else 0.3,
        )
    
    async def _handle_trend(
        self,
        question: str
    ) -> AssistantResponse:
        """Handle trend analysis requests."""
        # Generate SQL with time series aggregation
        enhanced_question = question
        if "trend" in question.lower() and "order by" not in question.lower():
            enhanced_question += " order by date or year"
        
        sql_result = await self._sql.convert(enhanced_question)
        
        message = "For trend analysis:\n\n"
        
        if sql_result.sql:
            message += f"```sql\n{sql_result.sql}\n```\n\n"
            message += (
                "This query retrieves historical data. "
                "You can visualize this as a line chart to see the trend."
            )
        else:
            message += (
                "To analyze trends, I need to know:\n"
                "1. Which metric to track (e.g., population, GDP)\n"
                "2. The time period (e.g., 2020-2024)\n"
                "3. The granularity (yearly, monthly, daily)"
            )
        
        return AssistantResponse(
            message=message,
            intent=IntentType.TREND_ANALYSIS,
            sql=sql_result.sql if sql_result.sql else None,
            suggestions=[
                "Export data for visualization",
                "Calculate year-over-year growth",
                "Add forecast using ML models",
            ],
            confidence=sql_result.confidence if sql_result.sql else 0.4,
        )
    
    def _handle_help(self, question: str) -> AssistantResponse:
        """Handle help requests."""
        help_content = """
# Nalytiq Data Platform Assistant

I can help you with:

## 📊 Data Discovery
- "What datasets are available about health?"
- "Recommend datasets for economic analysis"

## 🔍 Data Queries
- "Show me population by province"
- "How many datasets were accessed last month?"

## 📖 Explanations
- "What is the X-Road data exchange?"
- "Explain the data quality score"

## 📈 Analysis
- "What's the trend in GDP over the last 5 years?"
- "Compare population growth between provinces"

## 💡 Tips
- Be specific about what data you need
- Mention the time period if relevant
- Specify the organization or category

How can I help you today?
"""
        return AssistantResponse(
            message=help_content,
            intent=IntentType.HELP,
            suggestions=[
                "Show me available datasets",
                "How do I request data access?",
                "Explain the data catalog",
            ],
            confidence=1.0,
        )
    
    def _generate_suggestions(
        self,
        question: str,
        intent: IntentType
    ) -> List[str]:
        """Generate follow-up suggestions."""
        suggestions_map = {
            IntentType.QUESTION: [
                "Ask for more specific data",
                "Request dataset recommendations",
                "Query the actual data",
            ],
            IntentType.DATA_QUERY: [
                "Export query results",
                "Create a report",
                "Schedule regular updates",
            ],
            IntentType.RECOMMENDATION: [
                "View dataset details",
                "Request access",
                "Compare with alternatives",
            ],
            IntentType.EXPLANATION: [
                "See practical examples",
                "Explore related topics",
                "Access documentation",
            ],
            IntentType.UNKNOWN: [
                "Try rephrasing your question",
                "Ask for help",
                "Browse the data catalog",
            ],
        }
        return suggestions_map.get(intent, [])
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self._history = []
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self._history.copy()
    
    async def ingest_knowledge(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        source: str = "manual"
    ) -> int:
        """Add knowledge to the assistant's knowledge base.
        
        Args:
            texts: Text content to add.
            metadatas: Metadata for each text.
            source: Source identifier.
            
        Returns:
            Number of documents added.
        """
        return await self._rag.ingest_texts(texts, metadatas, source)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get assistant statistics."""
        return {
            "rag_stats": self._rag.get_stats(),
            "available_tables": self._sql.get_available_tables(),
            "history_length": len(self._history),
        }


# Module-level singleton
_assistant: Optional[DataAssistant] = None


def get_data_assistant() -> DataAssistant:
    """Get the global data assistant instance."""
    global _assistant
    if _assistant is None:
        _assistant = DataAssistant()
    return _assistant
