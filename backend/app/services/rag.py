import time
from functools import lru_cache
from typing import Any

from groq import Groq

from app.config import get_settings
from app.services.vector_store import get_vector_store


def log_timing(label: str, seconds: float) -> None:
    if get_settings().debug_timing:
        print(f"[timing] {label}: {seconds:.3f}s")


def clean_history(chat_history: list[Any], max_messages: int = 6) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []

    for item in chat_history[-max_messages:]:
        role = item.role if hasattr(item, "role") else item.get("role", "")
        content = item.content if hasattr(item, "content") else item.get("content", "")

        role = str(role).lower().strip()
        content = str(content).strip()

        if role not in {"user", "assistant"}:
            continue

        if content:
            cleaned.append({"role": role, "content": content[:1200]})

    return cleaned


def format_history(chat_history: list[dict[str, str]]) -> str:
    if not chat_history:
        return "No previous conversation."

    lines = []

    for item in chat_history:
        role = "User" if item["role"] == "user" else "Assistant"
        lines.append(f"{role}: {item['content']}")

    return "\n".join(lines)


def build_retrieval_question(question: str, chat_history: list[dict[str, str]]) -> str:
    recent_user_turns = [item["content"] for item in chat_history if item["role"] == "user"][-3:]

    if not recent_user_turns:
        return question

    return "\n".join(recent_user_turns + [question])


class RAGService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.vector_store = get_vector_store()
        self.client = Groq(api_key=self.settings.groq_api_key)

    def answer(
        self,
        collection_name: str,
        question: str,
        top_k: int = 5,
        persona: str = "student",
        chat_history: list[Any] | None = None,
    ) -> dict:
        total_start = time.perf_counter()

        history = clean_history(chat_history or [])
        retrieval_question = build_retrieval_question(question, history)
        history_text = format_history(history)

        t0 = time.perf_counter()
        retrieved = self.vector_store.query(collection_name, retrieval_question, top_k)
        log_timing("retrieval total", time.perf_counter() - t0)

        if not retrieved:
            return {
                "answer": "I could not find relevant context in this collection. Add sources to the collection or ask a more specific question.",
                "sources": [],
            }

        context_blocks = []

        for i, item in enumerate(retrieved, start=1):
            meta = item["metadata"]
            source = meta.get("source_name", "unknown")
            source_type = meta.get("source_type", "unknown")
            chunk_index = meta.get("chunk_index", -1)
            score = item.get("score")

            context_blocks.append(
                f"[Source {i}] type={source_type}; name={source}; chunk={chunk_index}; score={score}\n{item['text']}"
            )

        context = "\n\n".join(context_blocks)

        system_prompt = (
            "You are a precise grounded RAG assistant. Use the retrieved context as the primary source of truth. "
            "Use the conversation history only to understand follow-up questions and references. "
            "Do not treat conversation history as factual source material unless it is supported by retrieved context. "
            "You may synthesize across multiple retrieved chunks. "
            "Do not invent unsupported facts. "
            "Do not add an 'Uncertainty' section by default. "
            "Only say the sources are insufficient if the retrieved context clearly cannot answer the question."
        )

        user_prompt = f"""
User persona: {persona}

Conversation history:
{history_text}

Current question:
{question}

Retrieved context:
{context}

Answer rules:
- Start with the direct answer.
- Use conversation history to understand follow-up references like "it", "this", "that algorithm", or "previous topic".
- Use retrieved context as the factual grounding.
- Use concise bullets when useful.
- Prefer practical interview-style explanation when persona is student or interviewer.
- Do not say 'the provided sources do not contain enough information' unless the answer truly cannot be derived from retrieved context.
- Do not create a separate uncertainty section unless absolutely necessary.
""".strip()

        t1 = time.perf_counter()

        completion = self.client.chat.completions.create(
            model=self.settings.groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=350,
        )

        log_timing("groq llm", time.perf_counter() - t1)
        log_timing("query full total", time.perf_counter() - total_start)

        answer = completion.choices[0].message.content or ""

        return {
            "answer": answer,
            "sources": retrieved,
        }


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    return RAGService()