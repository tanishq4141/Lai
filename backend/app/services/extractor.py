"""
Clause extraction service.
Uses Gemini 3.5 Flash with structured JSON output to identify and extract
named clauses from parsed contract text.
"""

import logging
from typing import Any

from app.services import llm

logger = logging.getLogger(__name__)

# The 7 target clause types from the assignment
CLAUSE_TYPES = [
    "indemnity",
    "limitation_of_liability",
    "governing_law",
    "termination",
    "ip_ownership",
    "payment_terms",
    "confidentiality",
]

# JSON schema for Gemini structured output
CLAUSE_EXTRACTION_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "clause_type": {
                "type": "string",
                "enum": [
                    "indemnity",
                    "limitation_of_liability",
                    "governing_law",
                    "termination",
                    "ip_ownership",
                    "payment_terms",
                    "confidentiality",
                    "other",
                ],
            },
            "section_number": {
                "type": "string",
                "description": "The section or clause number (e.g. 7.2, 12, Schedule A)",
            },
            "title": {
                "type": "string",
                "description": "The heading or title of this clause/section",
            },
            "original_text": {
                "type": "string",
                "description": "The full verbatim text of the clause",
            },
            "sub_clauses": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Any sub-clauses or sub-sections within this clause",
            },
            "cross_references": {
                "type": "array",
                "items": {"type": "string"},
                "description": "References to other sections (e.g. 'Section 5.1', 'Clause 12')",
            },
            "key_terms": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Important defined terms used in this clause",
            },
        },
        "required": ["clause_type", "title", "original_text"],
    },
}

SYSTEM_INSTRUCTION = """You are a legal contract analyst specializing in clause extraction.

Your task is to identify and extract all significant clauses from a contract.
Focus on these clause types:
1. Indemnity - clauses about compensation for losses, hold harmless provisions
2. Limitation of Liability - caps on damages, exclusions of certain damage types
3. Governing Law - jurisdiction, applicable law, dispute resolution
4. Termination - conditions for ending the contract, notice periods, consequences
5. IP Ownership - intellectual property rights, assignments, licenses
6. Payment Terms - pricing, payment schedules, late fees, penalties
7. Confidentiality - non-disclosure obligations, exceptions, duration

Also extract any other significant clauses that affect rights, obligations, or risk.
Label those as "other".

For each clause:
- Include the FULL verbatim text, not a summary
- Note the section number if present
- List any cross-references to other sections
- Identify key defined terms used

Be thorough. Do not skip or merge clauses. Each distinct clause should be a separate entry."""


async def extract_clauses(contract_text: str) -> list[dict[str, Any]]:
    """Extract named clauses from contract text using Gemini structured output.

    Sends the entire contract to Gemini 3.5 Flash (which supports 1M tokens)
    and gets back a structured JSON array of extracted clauses.

    Args:
        contract_text: The full contract text (markdown format from Docling).

    Returns:
        List of clause dictionaries matching the CLAUSE_EXTRACTION_SCHEMA.
    """
    logger.info(f"Extracting clauses from contract ({len(contract_text)} chars)")

    prompt = f"""Analyze the following contract and extract all significant clauses.
Return a JSON array of clause objects.

CONTRACT TEXT:
---
{contract_text}
---

Extract all clauses following the instructions. Be thorough and include the full text of each clause."""

    result = await llm.generate_json(
        prompt=prompt,
        schema=CLAUSE_EXTRACTION_SCHEMA,
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.1,  # Low temperature for consistent extraction
    )

    if isinstance(result, list):
        clauses = result
    elif isinstance(result, dict) and "clauses" in result:
        clauses = result["clauses"]
    else:
        clauses = [result] if result else []

    logger.info(f"Extracted {len(clauses)} clauses")

    # Add position indices
    for i, clause in enumerate(clauses):
        clause["position"] = i

    return clauses


async def classify_clause(clause_text: str) -> str:
    """Classify a single clause into one of the named types.

    Useful for re-classification or validation of extracted clauses.

    Args:
        clause_text: The text of a single clause.

    Returns:
        The clause type string.
    """
    schema = {
        "type": "object",
        "properties": {
            "clause_type": {
                "type": "string",
                "enum": CLAUSE_TYPES + ["other"],
            },
            "confidence": {
                "type": "number",
                "description": "Confidence score from 0 to 1",
            },
        },
        "required": ["clause_type", "confidence"],
    }

    prompt = f"""Classify the following contract clause into one of these types:
- indemnity
- limitation_of_liability
- governing_law
- termination
- ip_ownership
- payment_terms
- confidentiality
- other

CLAUSE TEXT:
{clause_text}"""

    result = await llm.generate_json(
        prompt=prompt,
        schema=schema,
        temperature=0.1,
    )

    return result.get("clause_type", "other")
