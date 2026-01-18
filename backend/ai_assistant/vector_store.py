"""Vector Store Manager for RAG.

This module provides a clean, production-ready interface for managing
vector embeddings and similarity search. Follows Google Python style guide.

Example usage:
    store = get_vector_store()
    store.add_documents(documents, metadata_list)
    results = store.similarity_search(query, k=5)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Document:
    """Immutable document for vector storage.
    
    Attributes:
        content: The text content of the document.
        metadata: Additional information about the document.
        doc_id: Unique identifier, auto-generated if not provided.
    """
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    doc_id: str = field(default="")
    
    def __post_init__(self) -> None:
        if not self.doc_id:
            # Generate deterministic ID from content
            content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]
            object.__setattr__(self, "doc_id", f"doc_{content_hash}")


@dataclass
class SearchResult:
    """Result from similarity search.
    
    Attributes:
        document: The matched document.
        score: Similarity score (higher is more similar).
        rank: Position in result set (1-indexed).
    """
    document: Document
    score: float
    rank: int


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers.
    
    Subclass this to implement custom embedding backends.
    """
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Embed a batch of documents.
        
        Args:
            texts: List of text strings to embed.
            
        Returns:
            2D numpy array of shape (len(texts), embedding_dim).
        """
        pass
    
    @abstractmethod
    def embed_query(self, text: str) -> np.ndarray:
        """Embed a single query.
        
        Args:
            text: Query text to embed.
            
        Returns:
            1D numpy array of shape (embedding_dim,).
        """
        pass
    
    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """Return the embedding dimension."""
        pass


class SimpleEmbedding(EmbeddingProvider):
    """Simple TF-IDF based embedding for environments without GPU.
    
    This is a fallback when OpenAI or other providers are unavailable.
    For production, use OpenAIEmbedding or HuggingFaceEmbedding.
    """
    
    def __init__(self, dim: int = 384):
        self._dim = dim
        self._vocabulary: Dict[str, int] = {}
        self._idf: Dict[str, float] = {}
        self._fitted = False
    
    @property
    def embedding_dim(self) -> int:
        return self._dim
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple whitespace tokenization with lowercasing."""
        return text.lower().split()
    
    def _hash_token(self, token: str) -> int:
        """Hash token to fixed dimension index."""
        return int(hashlib.md5(token.encode()).hexdigest(), 16) % self._dim
    
    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Create TF-IDF inspired embeddings."""
        embeddings = np.zeros((len(texts), self._dim), dtype=np.float32)
        
        for i, text in enumerate(texts):
            tokens = self._tokenize(text)
            if not tokens:
                continue
                
            # Count term frequencies
            tf: Dict[int, float] = {}
            for token in tokens:
                idx = self._hash_token(token)
                tf[idx] = tf.get(idx, 0) + 1
            
            # Normalize and populate embedding
            max_tf = max(tf.values()) if tf else 1
            for idx, count in tf.items():
                embeddings[i, idx] = count / max_tf
            
            # L2 normalize
            norm = np.linalg.norm(embeddings[i])
            if norm > 0:
                embeddings[i] /= norm
        
        return embeddings
    
    def embed_query(self, text: str) -> np.ndarray:
        """Embed query using same method as documents."""
        return self.embed_documents([text])[0]


class OpenAIEmbedding(EmbeddingProvider):
    """OpenAI embedding provider using text-embedding-3-small.
    
    Requires OPENAI_API_KEY environment variable.
    """
    
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None
    ):
        self._model = model
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._client: Any = None
        
        # Model dimensions
        self._dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
    
    @property
    def embedding_dim(self) -> int:
        return self._dimensions.get(self._model, 1536)
    
    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self._api_key)
            except ImportError:
                raise ImportError("openai package required. Install with: pip install openai")
        return self._client
    
    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Embed documents using OpenAI API."""
        if not texts:
            return np.array([])
        
        client = self._get_client()
        
        # Batch requests (max 2048 per request for most models)
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = client.embeddings.create(
                model=self._model,
                input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        
        return np.array(all_embeddings, dtype=np.float32)
    
    def embed_query(self, text: str) -> np.ndarray:
        """Embed a single query."""
        return self.embed_documents([text])[0]


class HuggingFaceEmbedding(EmbeddingProvider):
    """HuggingFace Sentence Transformers embedding.
    
    Uses sentence-transformers for local inference.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model: Any = None
        self._dim: Optional[int] = None
    
    @property
    def embedding_dim(self) -> int:
        if self._dim is None:
            self._load_model()
        return self._dim or 384
    
    def _load_model(self) -> None:
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self._model_name)
                self._dim = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise ImportError(
                    "sentence-transformers required. "
                    "Install with: pip install sentence-transformers"
                )
    
    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Embed documents using local model."""
        self._load_model()
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.astype(np.float32)
    
    def embed_query(self, text: str) -> np.ndarray:
        """Embed query."""
        return self.embed_documents([text])[0]


class VectorIndex:
    """In-memory vector index with cosine similarity search.
    
    For production at scale, consider using FAISS or Pinecone.
    """
    
    def __init__(self):
        self._vectors: Optional[np.ndarray] = None
        self._doc_ids: List[str] = []
    
    def add(self, vectors: np.ndarray, doc_ids: List[str]) -> None:
        """Add vectors to the index.
        
        Args:
            vectors: 2D array of shape (n_docs, embedding_dim).
            doc_ids: Corresponding document IDs.
        """
        if len(vectors) != len(doc_ids):
            raise ValueError("Vectors and doc_ids must have same length")
        
        if self._vectors is None:
            self._vectors = vectors
            self._doc_ids = list(doc_ids)
        else:
            self._vectors = np.vstack([self._vectors, vectors])
            self._doc_ids.extend(doc_ids)
    
    def search(
        self,
        query_vector: np.ndarray,
        k: int = 5
    ) -> List[Tuple[str, float]]:
        """Find k most similar vectors.
        
        Args:
            query_vector: Query embedding.
            k: Number of results to return.
            
        Returns:
            List of (doc_id, similarity_score) tuples.
        """
        if self._vectors is None or len(self._vectors) == 0:
            return []
        
        # Cosine similarity
        query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-10)
        vectors_norm = self._vectors / (
            np.linalg.norm(self._vectors, axis=1, keepdims=True) + 1e-10
        )
        similarities = np.dot(vectors_norm, query_norm)
        
        # Get top k
        k = min(k, len(similarities))
        top_indices = np.argsort(similarities)[-k:][::-1]
        
        return [
            (self._doc_ids[idx], float(similarities[idx]))
            for idx in top_indices
        ]
    
    def remove(self, doc_ids: List[str]) -> int:
        """Remove documents by ID.
        
        Returns:
            Number of documents removed.
        """
        if self._vectors is None:
            return 0
        
        ids_to_remove = set(doc_ids)
        keep_mask = [
            doc_id not in ids_to_remove 
            for doc_id in self._doc_ids
        ]
        
        removed_count = len(self._doc_ids) - sum(keep_mask)
        
        self._vectors = self._vectors[keep_mask]
        self._doc_ids = [
            doc_id for doc_id, keep in zip(self._doc_ids, keep_mask) 
            if keep
        ]
        
        return removed_count
    
    def __len__(self) -> int:
        return len(self._doc_ids)


class VectorStoreManager:
    """Manages document storage, embedding, and retrieval.
    
    This is the main interface for the vector store. It handles:
    - Document chunking and storage
    - Embedding generation
    - Similarity search with filtering
    - Persistence to disk
    
    Example:
        store = VectorStoreManager()
        store.add_documents([
            Document("Rwanda population data...", {"source": "census"}),
            Document("Economic indicators...", {"source": "finance"}),
        ])
        results = store.similarity_search("population growth", k=5)
    """
    
    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProvider] = None,
        persist_directory: str = "./data/vector_store"
    ):
        """Initialize the vector store.
        
        Args:
            embedding_provider: Provider for generating embeddings.
                Defaults to SimpleEmbedding if not specified.
            persist_directory: Directory for storing index and documents.
        """
        self._embedding = embedding_provider or self._create_default_embedding()
        self._persist_dir = Path(persist_directory)
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        
        self._index = VectorIndex()
        self._documents: Dict[str, Document] = {}
        
        self._load()
    
    def _create_default_embedding(self) -> EmbeddingProvider:
        """Create default embedding provider based on available resources."""
        # Try OpenAI first
        if os.environ.get("OPENAI_API_KEY"):
            try:
                return OpenAIEmbedding()
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI embedding: {e}")
        
        # Try HuggingFace
        try:
            return HuggingFaceEmbedding()
        except ImportError:
            pass
        
        # Fallback to simple embedding
        logger.info("Using simple TF-IDF based embedding")
        return SimpleEmbedding()
    
    def _load(self) -> None:
        """Load persisted data from disk."""
        index_path = self._persist_dir / "index.pkl"
        docs_path = self._persist_dir / "documents.json"
        
        if index_path.exists() and docs_path.exists():
            try:
                with open(index_path, "rb") as f:
                    self._index = pickle.load(f)
                
                with open(docs_path, "r", encoding="utf-8") as f:
                    docs_data = json.load(f)
                    self._documents = {
                        doc_id: Document(**data)
                        for doc_id, data in docs_data.items()
                    }
                
                logger.info(f"Loaded {len(self._documents)} documents from disk")
            except Exception as e:
                logger.warning(f"Failed to load vector store: {e}")
    
    def _save(self) -> None:
        """Persist data to disk."""
        try:
            index_path = self._persist_dir / "index.pkl"
            docs_path = self._persist_dir / "documents.json"
            
            with open(index_path, "wb") as f:
                pickle.dump(self._index, f)
            
            docs_data = {
                doc_id: {
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "doc_id": doc.doc_id,
                }
                for doc_id, doc in self._documents.items()
            }
            
            with open(docs_path, "w", encoding="utf-8") as f:
                json.dump(docs_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")
    
    def add_documents(
        self,
        documents: Sequence[Document],
        batch_size: int = 100
    ) -> List[str]:
        """Add documents to the store.
        
        Args:
            documents: Documents to add.
            batch_size: Number of documents to embed at once.
            
        Returns:
            List of document IDs that were added.
        """
        if not documents:
            return []
        
        added_ids: List[str] = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Filter out duplicates
            new_docs = [
                doc for doc in batch 
                if doc.doc_id not in self._documents
            ]
            
            if not new_docs:
                continue
            
            # Generate embeddings
            texts = [doc.content for doc in new_docs]
            embeddings = self._embedding.embed_documents(texts)
            
            # Add to index and document store
            doc_ids = [doc.doc_id for doc in new_docs]
            self._index.add(embeddings, doc_ids)
            
            for doc in new_docs:
                self._documents[doc.doc_id] = doc
                added_ids.append(doc.doc_id)
        
        self._save()
        logger.info(f"Added {len(added_ids)} documents to vector store")
        
        return added_ids
    
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Convenience method to add plain texts.
        
        Args:
            texts: List of text strings.
            metadatas: Optional list of metadata dicts.
            
        Returns:
            List of generated document IDs.
        """
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        documents = [
            Document(content=text, metadata=meta)
            for text, meta in zip(texts, metadatas)
        ]
        
        return self.add_documents(documents)
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_fn: Optional[Callable[[Document], bool]] = None,
        score_threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """Search for similar documents.
        
        Args:
            query: Query text.
            k: Maximum number of results.
            filter_fn: Optional function to filter results by metadata.
            score_threshold: Minimum similarity score.
            
        Returns:
            List of SearchResult objects.
        """
        if not self._documents:
            return []
        
        # Embed query
        query_embedding = self._embedding.embed_query(query)
        
        # Search index (get more than k to allow for filtering)
        search_k = k * 3 if filter_fn else k
        raw_results = self._index.search(query_embedding, k=search_k)
        
        # Build results with filtering
        results: List[SearchResult] = []
        
        for doc_id, score in raw_results:
            if score_threshold and score < score_threshold:
                continue
            
            doc = self._documents.get(doc_id)
            if doc is None:
                continue
            
            if filter_fn and not filter_fn(doc):
                continue
            
            results.append(SearchResult(
                document=doc,
                score=score,
                rank=len(results) + 1
            ))
            
            if len(results) >= k:
                break
        
        return results
    
    def delete(self, doc_ids: List[str]) -> int:
        """Delete documents by ID.
        
        Returns:
            Number of documents deleted.
        """
        removed = self._index.remove(doc_ids)
        
        for doc_id in doc_ids:
            self._documents.pop(doc_id, None)
        
        self._save()
        return removed
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Retrieve a document by ID."""
        return self._documents.get(doc_id)
    
    def list_documents(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Document]:
        """List all documents with pagination."""
        all_docs = list(self._documents.values())
        return all_docs[offset:offset + limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        return {
            "total_documents": len(self._documents),
            "index_size": len(self._index),
            "embedding_provider": type(self._embedding).__name__,
            "embedding_dim": self._embedding.embedding_dim,
            "persist_directory": str(self._persist_dir),
        }
    
    def clear(self) -> None:
        """Remove all documents from the store."""
        self._index = VectorIndex()
        self._documents = {}
        self._save()


# Module-level singleton
_vector_store: Optional[VectorStoreManager] = None


def get_vector_store() -> VectorStoreManager:
    """Get the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreManager()
    return _vector_store
