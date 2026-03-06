"""
Retriever layer for finding relevant documents chunks
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from embeddings import EmbeddingGenerator
from vectorstore import ChromaVectorStore
from config import TOP_K

@dataclass
class RetrievalResult:
    """A single retrieved chunk with metada"""
    text: str
    source_file: str
    chunk_index: int
    distance: float
    metadata: Dict[str, Any]


class Retriever:
    """High level retriever interface"""
    def __init__(
        self,
        vector_store: ChromaVectorStore = None,
        embedding_generator: EmbeddingGenerator = None,
    ):
        """"
        Initialize retriever.
        Args:
            vector_series: Vector store instance (creates new if none)
            embedding_generator: Embedding generator instance(creates new if none)
        """
        self.vector_store = vector_store or ChromaVectorStore()
        self.embedding_generator = embedding_generator or EmbeddingGenerator()

    def retrieve(
        self,
        query:str,
        top_k:int=TOP_K,
        filter_source:Optional[str]=None,
        user_id:Optional[str]=None,

    ) -> List[RetrievalResult]:
        """Retrieve relevant chunks for a query.
        Args:
            query: Natural language query
            top_k: Number of chunks to return (default: TOP_K)
            filter_source: Optional source file filter
        Returns:
            List of RetrievalResults objects, sorted by relevance
        """

        if not query or not query.strip():
            return []
        query_embedding = self.embedding_generator.embed_text(query)

        # Build metadata filter if needed
        filter_metadata = {
            "source_file": filter_source,
        } if filter_source else None

        # Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata,
            user_id=user_id,
        )

        retrieval_results = []
        # Convert to RetrievalResult objects
        for doc,meta,dist,chunk_id in zip(
            results["documents"],
            results["metadatas"],
            results["distances"],
            results["ids"],
        ):
            result = RetrievalResult(
                text=doc,
                source_file=meta.get("source_file", "unknown"),
                chunk_index=meta.get("chunk_index",-1),
                distance=dist,
                metadata=meta,
            )
            retrieval_results.append(result)
        
        return retrieval_results
    def retrieve_with_context(
        self,
        query:str,
        top_k:int=TOP_K,
        user_id:Optional[str]=None,
    ) -> Dict[str, Any]:
        """
        Retrieve chunks and format them for LLM context.
        Args:
            query: Natural language query
            top_k: Number of chunks to return (default: TOP_K)
        Returns:
            Dictionary with context sections
        """
        if not query or not query.strip():
            return {
                "query": query or " ",
                "chunks": [],
                "context_text": " ",
                "num_results": 0,
            }
        retrieval_results = self.retrieve(query, top_k, user_id=user_id)

        # Format context for LLM
        context_parts = []
        for i, result in enumerate(retrieval_results,1):
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