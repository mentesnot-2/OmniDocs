"""
LLM-based answer generation with context grounding.
Supports Gemini (default) and OpenAI.
"""

from typing import Optional
from dataclasses import dataclass
from config import GEMINI_API_KEY, LLM_MODEL, LLM_PROVIDER, OPENAI_API_KEY


@dataclass
class GenerationResult:
    """Result of answer generation with context grounding."""
    answer: str
    source_used: list
    refused: bool


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
    """Generate answers from retrieved context using an LLM (Gemini or OpenAI)."""
    def __init__(
        self,
        api_key: str = None,
        model: str = LLM_MODEL,
        provider: str = LLM_PROVIDER,
    ):
        self.provider = (provider or "gemini").lower()
        self.model = model
        self.api_key = api_key

        if self.provider == "gemini":
            self.api_key = api_key or GEMINI_API_KEY
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY is required. Get one at https://aistudio.google.com/apikey")
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        elif self.provider == "openai":
            self.api_key = api_key or OPENAI_API_KEY
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY is required")
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def generate(
        self,
        query: str,
        context_text: str,
        source_files: list[str],
        message_history: list | None = None,
    ) -> GenerationResult:
        source_files = source_files or []

        if not context_text or not context_text.strip():
            return GenerationResult(
                answer="I cannot answer because no relevant documents were found.",
                source_used=[],
                refused=True,
            )

        if message_history and len(message_history) > 0:
            history_parts = []
            for item in message_history:
                q = item.get("question", "")
                a = item.get("answer", "")
                if q or a:
                    history_parts.append(f"Q: {q}\nA: {a}")
            if history_parts:
                effective_query = (
                    "Previous Q&A:\n"
                    + "\n\n".join(history_parts)
                    + "\n\nCurrent question: "
                    + query
                )
            else:
                effective_query = query
        else:
            effective_query = query

        user_prompt = USER_PROMPT.format(
            context=context_text,
            query=effective_query,
        )
        full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"

        try:
            if self.provider == "gemini":
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=full_prompt,
                    config={"temperature": 0.1},
                )
                answer = (response.text or "").strip()
            else:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,
                )
                answer = response.choices[0].message.content.strip()

            refused = (
                "cannot answer" in answer.lower()
                or "provided documents" in answer.lower()
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