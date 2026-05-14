"""
Vector store implementation using ChromaDB.
"""

from typing import List, Dict, Any
from pathlib import Path
import hashlib

import chromadb
from chromadb.config import Settings

from config import VECTOR_STORE_PATH, COLLECTION_NAME


class ChromaVectorStore:
    """
    Wrapper for ChromaDB vector store operations.

    Each tenant gets a dedicated collection:
    - omnidocs__1
    - omnidocs__2
    - omnidocs__cli
    """

    def __init__(
        self,
        user_id: str,
        persist_directory: str = VECTOR_STORE_PATH,
        base_collection_name: str = COLLECTION_NAME,
    ):
        if not user_id:
            raise ValueError("user_id is required for tenant-scoped vector store")

        self.user_id = str(user_id)
        self.persist_directory = Path(persist_directory)
        self.base_collection_name = base_collection_name
        self.collection_name = f"{base_collection_name}__{self.user_id}"

        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        print(f"Initialized ChromaDB collection: {self.collection_name}")
        print(f"Current document count: {self.collection.count()}")

    def _generate_chunk_ids(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate deterministic chunk IDs scoped to this tenant collection."""
        ids: List[str] = []
        for index, (text, metadata) in enumerate(zip(texts, metadatas)):
            source_file = str(metadata.get("source_file", "unknown"))
            chunk_index = str(metadata.get("chunk_index", index))
            digest = hashlib.sha256(
                f"{self.user_id}|{source_file}|{chunk_index}|{text}".encode("utf-8")
            ).hexdigest()
            ids.append(f"chunk_{digest}")
        return ids

    def add_chunks(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str] | None = None,
    ):
        """
        Add chunks with embeddings to the tenant-scoped collection.
        """
        if not texts:
            return

        if len(texts) != len(embeddings) or len(texts) != len(metadatas):
            raise ValueError("texts, embeddings, and metadatas must have the same length")

        if ids is None:
            ids = self._generate_chunk_ids(texts, metadatas)

        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        print(f"Added {len(texts)} chunks to {self.collection_name}")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Dict[str, Any] | None = None,
    ):
        """
        Search only inside this tenant's collection.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
        )

        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "ids": results["ids"][0] if results["ids"] else [],
        }

    def delete_by_source(self, source_file: str):
        """Delete all chunks for one source file inside this tenant's collection."""
        self.collection.delete(where={"source_file": source_file})
        print(f"Deleted all chunks from {source_file} in {self.collection_name}")

    def clear(self):
        """Clear only this tenant's collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        print(f"Cleared collection: {self.collection_name}")

    def get_stats(self):
        """Get statistics about this tenant collection."""
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "document_count": count,
            "persist_directory": str(self.persist_directory),
            "user_id": self.user_id,
        }