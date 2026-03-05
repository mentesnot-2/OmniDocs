"""
LLM-based answer generation with context grounding."""

from typing import Optional
from dataclasses import dataclass
from openai import OpenAI
from config import OPENAI_API_KEY, LLM_MODEL

@dataclass
class GenerationResult:
    """Result of answer generation with context grounding."""
    answer:str
    source_used:list
    refused:bool


SYSTEM_PROMPT = """You are a helpful assistant that answers questions based ONLY on the provided context.

RULES:
- Answer ONLY using information from the context below.
- If the context does not contain enough information to answer, say: "I cannot answer based on the provided documents."
- Do not make up or infer information not in the context.
- Be concise and factual.
- If possible, mention the source (e.g., "According to README.md...")."""

USER_PROMPT = """Context from documents:
{context}

---

Question: {query}
Answer (based only on the context above):"""

class AnswerGenerator:
    """Generate answers from retrieved context using an LLM."""
    def __init__(
        self,
        api_key:str=None,
        model:str=LLM_MODEL,

    ):
        """
        Initialize the answer generator.
        Args:
            api_key: OpenAI API key (use config if None)
            model: LLM model name
        """
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model

        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        self.client = OpenAI(api_key=self.api_key)
    
    def generate(
        self,
        query:str,
        context_text:str,
        source_files:list[str],
    ) -> GenerationResult:
        """
        Generate an answer to a question based on the provided context.
        Args:
            query: Natural language question
            context_text: Context text from documents
            source_files: List of source files used
        Returns:
            GenerationResult object containing the answer and source information
        """

        source_files = source_files or []

        # Reject if context is empty
        if not context_text or not context_text.strip():
            return GenerationResult(
                answer="I cannot answer because no relevant documents were found.",
                source_used=[],
                refused=True,
            )
        user_prompt = USER_PROMPT.format(
            context=context_text,
            query=query,
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content":SYSTEM_PROMPT},
                    {"role": "user", "content":user_prompt},
                ],
                temperature=0.1,
            )
            answer = response.choices[0].message.content.strip()

            # Heurstic: check if LLM refused
            refused = (
                "cannot answer" in answer.lower() or
                "provided documents" in answer.lower()
            )
            return GenerationResult(
                answer=answer,
                source_used=source_files,
                refused=refused,
            )
        except Exception as e:
            return GenerationResult(
                answer=f"An error occurred: {str(e)}",
                source_used=[],
                refused=True,
            )

  

