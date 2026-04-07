from functools import lru_cache


from embeddings import EmbeddingGenerator
from retrieval import Retriever
from generation import AnswerGenerator


@lru_cache(maxsize=1)
def get_embedding_generator() -> EmbeddingGenerator:
    return EmbeddingGenerator()

@lru_cache(maxsize=1)
def get_retriever() -> Retriever:
    return Retriever()

@lru_cache(maxsize=1)
def get_answer_generator() -> AnswerGenerator:
    return AnswerGenerator()