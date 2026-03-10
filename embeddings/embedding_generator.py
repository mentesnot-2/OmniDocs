"""
Embedding generation using sentence-transformers, OpenAI, or Gemini.
"""

from typing import List
import numpy as np
from config import EMBEDDING_PROVIDER, EMBEDDING_MODEL, OPENAI_API_KEY, GEMINI_API_KEY


class EmbeddingGenerator:
    """
    Generate embeddings using sentence-transformers, OpenAI, or Gemini.
    """
    def __init__(self, provider: str = EMBEDDING_PROVIDER, model: str = EMBEDDING_MODEL):
        """
        Initialize the embedding generator.

        Args:
            provider: The embedding provider to use. One of:
                      "sentence-transformers", "openai", "gemini", "google"
            model: The embedding model to use.
        """
        self.provider = (provider or "").lower()
        self.model_name = model
        self.model = None
        self.dimension = None
        self._initialize_model()

    def _initialize_model(self):
        """
        Load the embedding model based on provider.
        """
        # Local, no API key required
        if self.provider == "sentence-transformers":
            from sentence_transformers import SentenceTransformer
            print(f"Loading sentence-transformers model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()

        # OpenAI embeddings (optional)
        elif self.provider == "openai":
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set in the environment variables")
            from openai import OpenAI

            self.client = OpenAI(api_key=OPENAI_API_KEY)
            # Example: text-embedding-3-small is 1536 dims
            self.dimension = 1536
            print(f"Using OpenAI embedding model: {self.model_name or 'text-embedding-3-small'}")

        # Gemini embeddings (treat 'google' or 'gemini' as Gemini provider)
        elif self.provider in ("gemini", "google"):
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is not set in the environment variables")

            from google import genai
            self.genai_client = genai.Client(api_key=GEMINI_API_KEY)
            
            if not self.model_name:
                self.model_name = "text-embedding-004"
            
            # text-embedding-004 is 1536 dims
            self.dimension = 1536

            print(f"Using Gemini embedding model: {self.model_name}")

        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for a single text.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding.
        """
        if not text or not text.strip():
            return [0.0] * self.dimension

        if self.provider == "sentence-transformers":
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()

        elif self.provider == "openai":
            response = self.client.embeddings.create(
                input=text,
                model=self.model_name,
            )
            return response.data[0].embedding

        elif self.provider in ("gemini", "google"):
            # Gemini embedding API
            response = self.genai_client.models.embed_content(
                model=self.model_name,
                contents=text,
            )
            return response.embeddings[0].values

        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (more efficient for batch processing).

        Args:
            texts: A list of texts to embed.

        Returns:
            A list of lists of floats representing the embeddings.
        """
        if not texts:
            return []

        if self.provider == "sentence-transformers":
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()

        elif self.provider == "openai":
            response = self.client.embeddings.create(
                input=texts,
                model=self.model_name,
            )
            return [item.embedding for item in response.data]

        elif self.provider in ("gemini", "google"):
            # Simple loop; you can optimize later with a batch API if needed
            response = self.genai_client.models.embed_content(
                model=self.model_name,
                contents=texts,
            )
            return [embedding.values for embedding in response.embeddings]

        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

    def get_dimension(self) -> int:
        """
        Return embedding dimension.
        """
        return self.dimension