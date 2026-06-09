"""
Contract chat service.
Provides a RAG-style Q&A interface for asking questions about
a specific contract, with citations to relevant clauses.
"""

import logging
from typing import Any

from app.services import llm

logger = logging.getLogger(__name__)

CHAT_SCHEMA = {
    "type": "object",
    "properties": {
        "response": {
            "type": "string",
            "description": "The answer to the user's question in plain English",
        },
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "section_number": {
                        "type": "string",
                        "description": "The section or clause number referenced",
                    },
                    "snippet": {
                        "type": "string",
                        "description": "A short quote from the relevant clause (max 200 chars)",
                    },
                    "clause_type": {
                        "type": "string",
                        "description": "The type of clause if applicable",
                    },
                },
                "required": ["section_number", "snippet"],
            },
        },
        "confidence": {
            "type": "string",
            "enum": ["high", "medium", "low"],
            "description": "How confident you are in the answer based on the contract text",
        },
    },
    "required": ["response", "citations", "confidence"],
}

SYSTEM_INSTRUCTION = """You are a legal contract analyst answering questions about a specific contract.

Rules:
- Answer in plain English, avoid unnecessary legal jargon
- Always cite specific sections or clauses from the contract
- If the contract does not address the question, say so clearly
- Do not make assumptions or add information not in the contract
- If a question is ambiguous, note the ambiguity and provide the best answer
- Include relevant quotes as citations
- Rate your confidence: high (clearly stated), medium (implied or needs interpretation), low (not clearly addressed)"""


async def chat_with_contract(
    question: str,
    contract_text: str,
    clauses: list[dict[str, Any]] | None = None,
    chat_history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Answer a question about a contract with citations.

    Uses the full contract text (within Gemini's 1M context window)
    plus extracted clause metadata for better answers.

    Args:
        question: The user's question.
        contract_text: The full contract text (markdown).
        clauses: Optional extracted clauses for context.
        chat_history: Optional previous messages for context.

    Returns:
        Dict with response, citations, and confidence.
    """
    logger.info(f"Chat question: {question[:100]}")

    # Build clause context if available
    clause_context = ""
    if clauses:
        clause_context = "\n\nEXTRACTED CLAUSES:\n"
        for c in clauses:
            clause_context += (
                f"- [{c.get('clause_type', 'other')}] "
                f"Section {c.get('section_number', 'N/A')}: "
                f"{c.get('title', 'Untitled')}\n"
            )

    # Build chat history context
    history_context = ""
    if chat_history:
        history_context = "\n\nPREVIOUS CONVERSATION:\n"
        for msg in chat_history[-5:]:  # Last 5 messages for context
            role = msg.get("role", "user").upper()
            history_context += f"{role}: {msg.get('content', '')}\n"

    prompt = f"""Answer the following question about this contract.

CONTRACT TEXT:
---
{contract_text[:200000]}
---
{clause_context}
{history_context}

QUESTION: {question}

Provide a clear, plain-English answer with citations to specific sections."""

    result = await llm.generate_json(
        prompt=prompt,
        schema=CHAT_SCHEMA,
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.3,
    )

    return result
