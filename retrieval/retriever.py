"""
Retriever layer for finding relevant document chunks.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from embeddings import EmbeddingGenerator
from vectorstore import ChromaVectorStore
from config import TOP_K


@dataclass
class RetrievalResult:
    """A single retrieved chunk with metadata."""
    text: str
    source_file: str
    chunk_index: int
    distance: float
    metadata: Dict[str, Any]


class Retriever:
    """High-level retriever interface."""

    def __init__(
        self,
        embedder: EmbeddingGenerator | None = None,
    ):
        self.embedding_generator = embedder or EmbeddingGenerator()

    def retrieve(
        self,
        query: str,
        top_k: int = TOP_K,
        filter_source: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks for a query.
        """
        if not query or not query.strip():
            return []

        if not user_id:
            raise ValueError("user_id is required for retrieval in multi-tenant mode")

        query_embedding = self.embedding_generator.embed_text(query)

        filter_metadata = {
            "source_file": filter_source,
        } if filter_source else None

        vector_store = ChromaVectorStore(user_id=str(user_id))
        results = vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )

        retrieval_results = []
        for doc, meta, dist, chunk_id in zip(
            results["documents"],
            results["metadatas"],
            results["distances"],
            results["ids"],
        ):
            result = RetrievalResult(
                text=doc,
                source_file=meta.get("source_file", "unknown"),
                chunk_index=meta.get("chunk_index", -1),
                distance=dist,
                metadata=meta,
            )
            retrieval_results.append(result)

        return retrieval_results

    def retrieve_with_context(
        self,
        query: str,
        top_k: int = TOP_K,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve chunks and format them for LLM context.
        """
        if not query or not query.strip():
            return {
                "query": query or " ",
                "chunks": [],
                "context_text": " ",
                "num_results": 0,
            }

        retrieval_results = self.retrieve(query, top_k, user_id=user_id)

        context_parts = []
        for i, result in enumerate(retrieval_results, 1):
            context_parts.append(
                f"[Source {i}: {result.source_file}, chunk {result.chunk_index}]\n"
                f"{result.text}"
            )

        context_text = "\n\n---\n\n".join(context_parts)
        return {
            "query": query,
            "chunks": retrieval_results,
            "context_text": context_text,
            "num_results": len(retrieval_results),
        }