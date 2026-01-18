"""RAG Engine for Retrieval-Augmented Generation.

Production-ready RAG implementation following Google design principles:
- Clean separation of concerns
- Dependency injection
- Configurable components
- Comprehensive error handling
- Observable and testable

Example usage:
    engine = get_rag_engine()
    response = await engine.query(
        "What is the population of Rwanda?",
        context_filter={"source": "census"}
    )
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from .vector_store import (
    VectorStoreManager,
    Document,
    SearchResult,
    get_vector_store,
)

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"


@dataclass
class RAGConfig:
    """Configuration for RAG engine.
    
    Attributes:
        llm_provider: Which LLM to use for generation.
        llm_model: Specific model name.
        max_tokens: Maximum tokens in response.
        temperature: Sampling temperature.
        top_k_retrieval: Number of documents to retrieve.
        score_threshold: Minimum similarity score.
        system_prompt: System message for the LLM.
        chunk_size: Size of document chunks.
        chunk_overlap: Overlap between chunks.
    """
    llm_provider: LLMProvider = LLMProvider.OPENAI
    llm_model: str = "gpt-4o-mini"
    max_tokens: int = 1024
    temperature: float = 0.1
    top_k_retrieval: int = 5
    score_threshold: float = 0.3
    system_prompt: str = ""
    chunk_size: int = 1000
    chunk_overlap: int = 200


@dataclass
class RAGResponse:
    """Response from RAG query.
    
    Attributes:
        answer: The generated answer.
        sources: Documents used for generation.
        query: Original query.
        confidence: Confidence score (0-1).
        metadata: Additional response metadata.
    """
    answer: str
    sources: List[SearchResult]
    query: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "answer": self.answer,
            "query": self.query,
            "confidence": self.confidence,
            "sources": [
                {
                    "content": s.document.content[:500] + "..." 
                        if len(s.document.content) > 500 
                        else s.document.content,
                    "metadata": s.document.metadata,
                    "score": s.score,
                    "rank": s.rank,
                }
                for s in self.sources
            ],
            "metadata": self.metadata,
        }


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.1
    ) -> str:
        """Generate text from prompt."""
        pass


class OpenAIClient(LLMClient):
    """OpenAI API client."""
    
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self._model = model
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._client: Any = None
    
    def _get_client(self):
        """Lazy initialization of async client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self._api_key)
            except ImportError:
                raise ImportError("openai required. Install with: pip install openai")
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.1
    ) -> str:
        """Generate using OpenAI API."""
        client = self._get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content or ""


class AnthropicClient(LLMClient):
    """Anthropic Claude API client."""
    
    def __init__(self, model: str = "claude-3-sonnet-20240229", api_key: Optional[str] = None):
        self._model = model
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client: Any = None
    
    def _get_client(self):
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self._api_key)
            except ImportError:
                raise ImportError("anthropic required. Install with: pip install anthropic")
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.1
    ) -> str:
        """Generate using Anthropic API."""
        client = self._get_client()
        
        response = await client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text


class GoogleClient(LLMClient):
    """Google Gemini API client."""
    
    def __init__(self, model: str = "gemini-1.5-flash", api_key: Optional[str] = None):
        self._model = model
        self._api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self._client: Any = None
    
    def _get_client(self):
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self._api_key)
                self._client = genai.GenerativeModel(self._model)
            except ImportError:
                raise ImportError(
                    "google-generativeai required. "
                    "Install with: pip install google-generativeai"
                )
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.1
    ) -> str:
        """Generate using Google Gemini API."""
        client = self._get_client()
        
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        response = await client.generate_content_async(
            full_prompt,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": temperature
            }
        )
        
        return response.text


class LocalClient(LLMClient):
    """Local/fallback client for testing without API keys."""
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.1
    ) -> str:
        """Generate a simple response based on context extraction."""
        # Extract the context if present in the prompt
        if "Context:" in prompt:
            context_start = prompt.find("Context:") + len("Context:")
            question_start = prompt.find("Question:")
            if question_start > context_start:
                context = prompt[context_start:question_start].strip()
                # Return first 500 chars of context as "answer"
                if context:
                    return f"Based on the provided context: {context[:500]}..."
        
        return "I don't have enough information to answer this question. Please provide more context or documents."


class DocumentChunker:
    """Split documents into smaller chunks for embedding.
    
    Uses a sliding window approach with configurable size and overlap.
    """
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self._chunk_size = chunk_size
        self._overlap = overlap
    
    def chunk_document(self, document: Document) -> List[Document]:
        """Split a document into chunks.
        
        Args:
            document: Document to split.
            
        Returns:
            List of chunk documents with updated metadata.
        """
        text = document.content
        
        if len(text) <= self._chunk_size:
            return [document]
        
        chunks = []
        start = 0
        chunk_idx = 0
        
        while start < len(text):
            end = min(start + self._chunk_size, len(text))
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = text.rfind(".", start, end)
                last_newline = text.rfind("\n", start, end)
                break_point = max(last_period, last_newline)
                if break_point > start + self._chunk_size // 2:
                    end = break_point + 1
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk_meta = {
                    **document.metadata,
                    "chunk_index": chunk_idx,
                    "parent_doc_id": document.doc_id,
                    "char_start": start,
                    "char_end": end,
                }
                chunks.append(Document(
                    content=chunk_text,
                    metadata=chunk_meta
                ))
                chunk_idx += 1
            
            start = end - self._overlap if end < len(text) else end
        
        return chunks


class RAGEngine:
    """Retrieval-Augmented Generation engine.
    
    Orchestrates the retrieval and generation pipeline:
    1. Receive user query
    2. Retrieve relevant documents from vector store
    3. Construct prompt with context
    4. Generate answer using LLM
    5. Return response with sources
    
    Example:
        engine = RAGEngine()
        await engine.ingest_documents([doc1, doc2])
        response = await engine.query("What is the GDP of Rwanda?")
        print(response.answer)
    """
    
    # Default system prompt for data platform context
    DEFAULT_SYSTEM_PROMPT = """You are an AI assistant for the Nalytiq Data Platform, 
a national data exchange and analytics platform for Rwanda. 

Your role is to:
- Help users understand and query statistical datasets
- Answer questions about data, policies, and procedures
- Provide accurate information based only on the provided context
- Cite sources when answering

Guidelines:
- Be precise and factual
- If the context doesn't contain the answer, say so honestly
- Use data and statistics when available
- Format responses clearly with bullet points or tables when helpful
"""
    
    def __init__(
        self,
        config: Optional[RAGConfig] = None,
        vector_store: Optional[VectorStoreManager] = None,
        llm_client: Optional[LLMClient] = None
    ):
        """Initialize RAG engine.
        
        Args:
            config: RAG configuration.
            vector_store: Vector store for document retrieval.
            llm_client: LLM client for generation.
        """
        self._config = config or RAGConfig()
        self._vector_store = vector_store or get_vector_store()
        self._llm_client = llm_client or self._create_llm_client()
        self._chunker = DocumentChunker(
            chunk_size=self._config.chunk_size,
            overlap=self._config.chunk_overlap
        )
    
    def _create_llm_client(self) -> LLMClient:
        """Create LLM client based on configuration."""
        provider = self._config.llm_provider
        model = self._config.llm_model
        
        if provider == LLMProvider.OPENAI:
            if os.environ.get("OPENAI_API_KEY"):
                return OpenAIClient(model=model)
        elif provider == LLMProvider.ANTHROPIC:
            if os.environ.get("ANTHROPIC_API_KEY"):
                return AnthropicClient(model=model)
        elif provider == LLMProvider.GOOGLE:
            if os.environ.get("GOOGLE_API_KEY"):
                return GoogleClient(model=model)
        
        # Fallback to local
        logger.warning(f"No API key found for {provider}, using local client")
        return LocalClient()
    
    async def ingest_documents(
        self,
        documents: List[Document],
        chunk: bool = True
    ) -> int:
        """Ingest documents into the knowledge base.
        
        Args:
            documents: Documents to ingest.
            chunk: Whether to chunk documents.
            
        Returns:
            Number of document chunks added.
        """
        if chunk:
            all_chunks = []
            for doc in documents:
                chunks = self._chunker.chunk_document(doc)
                all_chunks.extend(chunks)
            documents = all_chunks
        
        added_ids = self._vector_store.add_documents(documents)
        logger.info(f"Ingested {len(added_ids)} document chunks")
        return len(added_ids)
    
    async def ingest_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        source: str = "manual"
    ) -> int:
        """Convenience method to ingest plain texts.
        
        Args:
            texts: List of text strings.
            metadatas: Optional metadata for each text.
            source: Source identifier.
            
        Returns:
            Number of chunks added.
        """
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        documents = [
            Document(
                content=text,
                metadata={**meta, "source": source, "ingested_at": datetime.utcnow().isoformat()}
            )
            for text, meta in zip(texts, metadatas)
        ]
        
        return await self.ingest_documents(documents)
    
    def _build_prompt(
        self,
        query: str,
        context_docs: List[SearchResult]
    ) -> str:
        """Build the generation prompt with retrieved context."""
        context_parts = []
        
        for i, result in enumerate(context_docs, 1):
            doc = result.document
            source_info = doc.metadata.get("source", "Unknown")
            context_parts.append(
                f"[Source {i}: {source_info}]\n{doc.content}"
            )
        
        context = "\n\n---\n\n".join(context_parts)
        
        prompt = f"""Context:
{context}

---

Question: {query}

Please answer the question based on the context provided above. If the context doesn't contain enough information to answer fully, say so and explain what information is missing."""
        
        return prompt
    
    async def query(
        self,
        query: str,
        context_filter: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None,
        include_sources: bool = True
    ) -> RAGResponse:
        """Query the RAG system.
        
        Args:
            query: User question.
            context_filter: Filter for document metadata.
            top_k: Override default number of documents to retrieve.
            include_sources: Whether to include source documents.
            
        Returns:
            RAGResponse with answer and sources.
        """
        k = top_k or self._config.top_k_retrieval
        
        # Create filter function if context_filter provided
        filter_fn = None
        if context_filter:
            def filter_fn(doc: Document) -> bool:
                for key, value in context_filter.items():
                    if doc.metadata.get(key) != value:
                        return False
                return True
        
        # Retrieve relevant documents
        search_results = self._vector_store.similarity_search(
            query=query,
            k=k,
            filter_fn=filter_fn,
            score_threshold=self._config.score_threshold
        )
        
        if not search_results:
            return RAGResponse(
                answer="I couldn't find any relevant information in the knowledge base to answer your question. Please try rephrasing or ensure the relevant documents have been indexed.",
                sources=[],
                query=query,
                confidence=0.0,
                metadata={"retrieval_count": 0}
            )
        
        # Build prompt with context
        prompt = self._build_prompt(query, search_results)
        
        # Generate answer
        system_prompt = self._config.system_prompt or self.DEFAULT_SYSTEM_PROMPT
        
        try:
            answer = await self._llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=self._config.max_tokens,
                temperature=self._config.temperature
            )
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            answer = f"Error generating response: {str(e)}"
        
        # Calculate confidence based on retrieval scores
        avg_score = sum(r.score for r in search_results) / len(search_results)
        confidence = min(1.0, avg_score)
        
        return RAGResponse(
            answer=answer,
            sources=search_results if include_sources else [],
            query=query,
            confidence=confidence,
            metadata={
                "retrieval_count": len(search_results),
                "avg_similarity": avg_score,
                "llm_provider": self._config.llm_provider.value,
                "llm_model": self._config.llm_model,
            }
        )
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        context_filter: Optional[Dict[str, Any]] = None
    ) -> RAGResponse:
        """Multi-turn chat with RAG.
        
        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}.
            context_filter: Filter for document metadata.
            
        Returns:
            RAGResponse for the last user message.
        """
        # Extract conversation context
        conversation = []
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation.append(f"{role}: {msg['content']}")
        
        # Use last message as query, but include conversation
        last_user_msg = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"),
            ""
        )
        
        # Retrieve based on full conversation context
        full_context = " ".join([m["content"] for m in messages if m["role"] == "user"])
        
        return await self.query(
            query=last_user_msg,
            context_filter=context_filter
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG engine statistics."""
        store_stats = self._vector_store.get_stats()
        
        return {
            "config": {
                "llm_provider": self._config.llm_provider.value,
                "llm_model": self._config.llm_model,
                "top_k_retrieval": self._config.top_k_retrieval,
                "score_threshold": self._config.score_threshold,
                "chunk_size": self._config.chunk_size,
            },
            "vector_store": store_stats,
        }


# Module-level singleton
_rag_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """Get the global RAG engine instance."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine
