"""AI Assistant API Endpoints.

RESTful API for the intelligent data assistant featuring:
- General Q&A with RAG
- Natural language to SQL conversion
- Dataset recommendations
- Knowledge base management

Follows Google API design guidelines for consistency and usability.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/assistant", tags=["AI Assistant"])


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class AskRequest(BaseModel):
    """Request model for general Q&A."""
    question: str = Field(..., description="User's question", min_length=1, max_length=2000)
    context_filter: Optional[Dict[str, Any]] = Field(
        None, description="Filter for document retrieval"
    )
    auto_route: bool = Field(
        True, description="Automatically route based on detected intent"
    )


class QueryDataRequest(BaseModel):
    """Request model for NL-to-SQL conversion."""
    question: str = Field(..., description="Natural language data query")
    tables: Optional[List[str]] = Field(None, description="Specific tables to consider")
    validate: bool = Field(True, description="Validate generated SQL for safety")


class RecommendRequest(BaseModel):
    """Request model for dataset recommendations."""
    purpose: str = Field(..., description="What the data will be used for")
    organization: Optional[str] = Field(None, description="Requesting organization")
    category: Optional[str] = Field(None, description="Preferred data category")
    max_results: int = Field(5, ge=1, le=20)


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    """Request model for multi-turn chat."""
    messages: List[ChatMessage]
    context_filter: Optional[Dict[str, Any]] = None


class IngestTextRequest(BaseModel):
    """Request model for ingesting text to knowledge base."""
    texts: List[str] = Field(..., min_items=1, max_items=100)
    metadatas: Optional[List[Dict[str, Any]]] = None
    source: str = Field("api", description="Source identifier")


class IngestDocumentRequest(BaseModel):
    """Request model for ingesting documents."""
    content: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    """Request model for vector search."""
    query: str = Field(..., min_length=1)
    k: int = Field(5, ge=1, le=50)
    filter: Optional[Dict[str, Any]] = None
    score_threshold: Optional[float] = Field(None, ge=0, le=1)


# ============================================
# Q&A ENDPOINTS
# ============================================

@router.post("/ask")
async def ask_question(request: AskRequest):
    """Ask a question to the AI assistant.
    
    The assistant automatically detects the intent and routes to the
    appropriate handler (Q&A, data query, recommendation, etc.)
    
    Returns:
        AssistantResponse with answer, sources, and suggestions.
    """
    from ai_assistant import get_data_assistant
    
    assistant = get_data_assistant()
    response = await assistant.ask(
        question=request.question,
        context_filter=request.context_filter,
        auto_route=request.auto_route
    )
    
    return response.to_dict()


@router.post("/chat")
async def chat_conversation(request: ChatRequest):
    """Multi-turn chat with the assistant.
    
    Maintains conversation context for follow-up questions.
    
    Returns:
        Response to the latest message with full context.
    """
    from ai_assistant import get_data_assistant, RAGEngine
    
    assistant = get_data_assistant()
    
    # Get RAG engine for chat
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    rag_response = await assistant._rag.chat(
        messages=messages,
        context_filter=request.context_filter
    )
    
    return rag_response.to_dict()


@router.get("/help")
async def get_help():
    """Get help information about the assistant.
    
    Returns:
        Help content with examples and tips.
    """
    from ai_assistant import get_data_assistant
    
    assistant = get_data_assistant()
    response = assistant._handle_help("help")
    
    return response.to_dict()


# ============================================
# DATA QUERY ENDPOINTS
# ============================================

@router.post("/query")
async def query_data(request: QueryDataRequest):
    """Convert natural language to SQL query.
    
    Generates a read-only SQL query from the user's question.
    
    Returns:
        SQL query, explanation, and safety information.
    """
    from ai_assistant import get_data_assistant
    
    assistant = get_data_assistant()
    response = await assistant.query_data(
        question=request.question,
        tables=request.tables
    )
    
    return response.to_dict()


@router.get("/query/tables")
async def get_available_tables():
    """Get list of tables available for querying.
    
    Returns:
        List of table names and their schemas.
    """
    from ai_assistant import get_nl_to_sql_converter
    
    converter = get_nl_to_sql_converter()
    
    tables = []
    for schema in converter._schema_registry.get_all():
        tables.append({
            "name": schema.table_name,
            "description": schema.description,
            "columns": [
                {"name": c["name"], "type": c["type"], "description": c.get("description", "")}
                for c in schema.columns
            ]
        })
    
    return {"tables": tables}


@router.post("/query/validate")
async def validate_sql(sql: str = Query(..., description="SQL query to validate")):
    """Validate an SQL query for safety.
    
    Checks for dangerous operations and SQL injection patterns.
    
    Returns:
        Validation result with warnings.
    """
    from ai_assistant.nl_to_sql import SQLValidator
    
    is_safe, warnings = SQLValidator.validate(sql)
    tables = SQLValidator.extract_tables(sql)
    
    return {
        "sql": sql,
        "is_safe": is_safe,
        "warnings": warnings,
        "tables_used": tables
    }


# ============================================
# RECOMMENDATION ENDPOINTS
# ============================================

@router.post("/recommend")
async def recommend_datasets(request: RecommendRequest):
    """Get dataset recommendations for a specific purpose.
    
    Uses semantic search to find relevant datasets.
    
    Returns:
        List of recommended datasets with relevance scores.
    """
    from ai_assistant import get_data_assistant
    
    assistant = get_data_assistant()
    response = await assistant.recommend_datasets(
        purpose=request.purpose,
        organization=request.organization,
        category=request.category,
        max_results=request.max_results
    )
    
    return response.to_dict()


# ============================================
# KNOWLEDGE BASE ENDPOINTS
# ============================================

@router.post("/knowledge/ingest")
async def ingest_texts(request: IngestTextRequest, background_tasks: BackgroundTasks):
    """Ingest texts into the knowledge base.
    
    Adds documents to the vector store for RAG retrieval.
    
    Returns:
        Number of documents ingested.
    """
    from ai_assistant import get_data_assistant
    
    assistant = get_data_assistant()
    
    count = await assistant.ingest_knowledge(
        texts=request.texts,
        metadatas=request.metadatas,
        source=request.source
    )
    
    return {
        "ingested": count,
        "source": request.source,
        "message": f"Successfully ingested {count} document chunks"
    }


@router.post("/knowledge/document")
async def ingest_document(request: IngestDocumentRequest):
    """Ingest a single document into the knowledge base.
    
    The document will be chunked and embedded automatically.
    
    Returns:
        Document ID and ingestion status.
    """
    from ai_assistant import get_rag_engine
    from ai_assistant.vector_store import Document
    
    engine = get_rag_engine()
    
    doc = Document(
        content=request.content,
        metadata=request.metadata
    )
    
    count = await engine.ingest_documents([doc])
    
    return {
        "document_id": doc.doc_id,
        "chunks_created": count,
        "message": "Document ingested successfully"
    }


@router.post("/knowledge/search")
async def search_knowledge(request: SearchRequest):
    """Search the knowledge base.
    
    Performs semantic similarity search.
    
    Returns:
        List of matching documents with scores.
    """
    from ai_assistant import get_vector_store
    
    store = get_vector_store()
    
    # Build filter function if provided
    filter_fn = None
    if request.filter:
        def filter_fn(doc):
            for key, value in request.filter.items():
                if doc.metadata.get(key) != value:
                    return False
            return True
    
    results = store.similarity_search(
        query=request.query,
        k=request.k,
        filter_fn=filter_fn,
        score_threshold=request.score_threshold
    )
    
    return {
        "query": request.query,
        "results": [
            {
                "doc_id": r.document.doc_id,
                "content": r.document.content[:500],
                "metadata": r.document.metadata,
                "score": r.score,
                "rank": r.rank
            }
            for r in results
        ],
        "count": len(results)
    }


@router.get("/knowledge/stats")
async def get_knowledge_stats():
    """Get statistics about the knowledge base.
    
    Returns:
        Document count, embedding info, and storage details.
    """
    from ai_assistant import get_vector_store
    
    store = get_vector_store()
    return store.get_stats()


@router.delete("/knowledge/clear")
async def clear_knowledge():
    """Clear all documents from the knowledge base.
    
    ⚠️ This operation cannot be undone.
    
    Returns:
        Confirmation message.
    """
    from ai_assistant import get_vector_store
    
    store = get_vector_store()
    store.clear()
    
    return {"message": "Knowledge base cleared", "status": "success"}


@router.delete("/knowledge/document/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a specific document from the knowledge base.
    
    Returns:
        Deletion status.
    """
    from ai_assistant import get_vector_store
    
    store = get_vector_store()
    deleted = store.delete([doc_id])
    
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"deleted": deleted, "doc_id": doc_id}


# ============================================
# CONFIGURATION ENDPOINTS
# ============================================

@router.get("/config")
async def get_assistant_config():
    """Get current assistant configuration.
    
    Returns:
        RAG config, LLM settings, and available features.
    """
    from ai_assistant import get_data_assistant
    
    assistant = get_data_assistant()
    stats = assistant.get_stats()
    
    return {
        "config": stats,
        "features": {
            "rag_enabled": True,
            "nl_to_sql_enabled": True,
            "recommendations_enabled": True,
            "multi_turn_chat": True
        },
        "supported_intents": [
            "question", "data_query", "recommendation",
            "explanation", "comparison", "trend", "help"
        ]
    }


@router.post("/config/llm")
async def configure_llm(
    provider: str = Query(..., pattern="^(openai|anthropic|google|local)$"),
    model: Optional[str] = None
):
    """Configure the LLM provider.
    
    Note: Requires API key for non-local providers.
    
    Returns:
        Updated configuration.
    """
    from ai_assistant.rag_engine import RAGConfig, LLMProvider, RAGEngine, get_rag_engine
    
    provider_enum = LLMProvider(provider)
    
    # Create new config
    config = RAGConfig(
        llm_provider=provider_enum,
        llm_model=model or get_default_model(provider_enum)
    )
    
    # Update global engine (in production, use proper dependency injection)
    global _rag_engine
    from ai_assistant import rag_engine
    rag_engine._rag_engine = RAGEngine(config=config)
    
    return {
        "provider": provider,
        "model": config.llm_model,
        "message": "LLM configuration updated"
    }


def get_default_model(provider: str) -> str:
    """Get default model for provider."""
    defaults = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-sonnet-20240229",
        "google": "gemini-1.5-flash",
        "local": "local"
    }
    return defaults.get(provider, "gpt-4o-mini")


# ============================================
# HISTORY ENDPOINTS
# ============================================

@router.get("/history")
async def get_chat_history():
    """Get current conversation history.
    
    Returns:
        List of messages in the current session.
    """
    from ai_assistant import get_data_assistant
    
    assistant = get_data_assistant()
    return {"history": assistant.get_history()}


@router.delete("/history")
async def clear_chat_history():
    """Clear conversation history.
    
    Returns:
        Confirmation message.
    """
    from ai_assistant import get_data_assistant
    
    assistant = get_data_assistant()
    assistant.clear_history()
    
    return {"message": "Conversation history cleared"}
