"""
Vectore store implementation using chromaDB.
"""

from typing import List,Dict,Any
from pathlib import Path
import chromadb
from chromadb.config import Settings
from config import VECTOR_STORE_PATH,COLLECTION_NAME

class ChromaVectorStore:
    """
    Wrapper for chromaDB vector store operations.
    """

    def __init__(
        self,
        persist_directory:str = VECTOR_STORE_PATH,
        collection_name:str = COLLECTION_NAME,
    ):
        """
        Initialize the ChromaDB client and collection.
        Args:
            persist_directory: The directory to persist the database.
            collection_name: The name of the collection to use.
        """
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        
        # Create persist directory if needed
        self.persist_directory.mkdir(parents=True,exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path = str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name = self.collection_name,
            metadata = {
                "hnsw:space": "cosine"}
        )

        print(f"Initialized ChromaDB client and collection: {self.collection_name}")
        print(f"Collection: {self.collection_name}")
        print(f"Current document count: {self.collection.count()}")

    def add_chunks(
        self,
        texts:List[str],
        embeddings:List[List[float]],
        metadatas:List[Dict[str,Any]],
        ids:List[str] = None,
    ):
        """
        Add chunks with embeddings to the vector store.

        Args:
            texts: List of text chunks.
            embeddings: List of embeddings for each text chunk.
            metadatas: List of metadata dictionaries for each text chunk.
            ids: List of unique identifiers for each text chunk.
        """
        if not texts:
            return
        if ids is None:
            current_count = self.collection.count()
            ids = [f"chunk_{current_count + i}" for i in range(len(texts))]
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        print(f"Added {len(texts)} chunks to the vector store")
    def search(
        self,
        query_embedding:List[float],
        top_k:int = 5,
        filter_metadata:Dict[str,Any] = None,
        user_id:str = None,
    ):
        """
        Search for similar chunks.
        Args:
            query_embedding: The embedding of the query.
            top_k: The number of results to return.
            filter_metadata: A dictionary of metadata filters to apply.
        Returns:
            A list of results.
        """
        # Build where clause  - ChromaDbB requires user_id filter for multi-tenant
        where_filter = None
        if user_id is not None:
            where_filter = {"user_id":user_id}
            if filter_metadata:
                where_filter = {"$and":[where_filter,filter_metadata]}
        else:
            where_filter = filter_metadata
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
        )

        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "ids": results["ids"][0] if results["ids"] else [],
        }
    def delete_by_source(self,source_file:str,user_id:str = None):
        """Delete all chunks from a specific source file"""
        where_clause = None
        if user_id is not None:
            where_clause = {"$and":[{"source_file":source_file},{"user_id":str(user_id)}]}
        else:
            where_clause = {"source_file":source_file}
        self.collection.delete(where=where_clause)
        print(f"Deleted all chunks from {source_file}")
    def clear(self):
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={
                "hnsw:space": "cosine"}
            )
        print(f"Cleared collection: {self.collection_name}")
    def get_stats(self):
        """Get statistics about the vector store."""
        count = self.collection.count()
        return {
            "collection_name":self.collection_name,
            "document_count":count,
            "persist_directory":str(self.persist_directory),
        }