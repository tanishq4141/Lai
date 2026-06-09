"""
Executive summary generator.
Produces a 1-page plain-English executive summary of a contract,
covering: what it covers, who carries the risk, key commercial terms,
and top 3 issues to negotiate.
"""

import logging
from typing import Any

from app.services import llm

logger = logging.getLogger(__name__)

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "A plain-English executive summary (3 to 5 paragraphs)",
        },
        "contract_type": {
            "type": "string",
            "description": "The type of contract (e.g. NDA, SaaS Agreement, Employment Contract)",
        },
        "parties": {
            "type": "array",
            "items": {"type": "string"},
            "description": "The parties to the contract",
        },
        "effective_date": {
            "type": "string",
            "description": "The effective date if mentioned, otherwise 'Not specified'",
        },
        "term_duration": {
            "type": "string",
            "description": "The duration or term of the contract",
        },
        "risk_carrier": {
            "type": "string",
            "description": "Which party carries the most risk and why",
        },
        "key_commercial_terms": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of key commercial terms (pricing, payment, deliverables, etc.)",
        },
        "top_issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "issue": {"type": "string"},
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                    },
                    "recommendation": {"type": "string"},
                },
                "required": ["issue", "severity", "recommendation"],
            },
            "description": "Top 3 to 5 issues that should be negotiated or reviewed by a lawyer",
        },
        "obligations_summary": {
            "type": "object",
            "properties": {
                "party_a": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key obligations of the first party",
                },
                "party_b": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key obligations of the second party",
                },
            },
        },
    },
    "required": [
        "summary",
        "contract_type",
        "parties",
        "risk_carrier",
        "key_commercial_terms",
        "top_issues",
    ],
}

SYSTEM_INSTRUCTION = """You are a senior legal analyst writing an executive summary for a business executive.

Rules:
- Write in plain English, no legal jargon
- Be specific about numbers, dates, and obligations
- Focus on what matters commercially
- Identify the TOP 3 to 5 issues that need negotiation or legal review
- Explain who carries the most risk and why
- Keep the summary concise but complete (aim for 300 to 500 words)
- Use bullet points for key terms and issues
- Be honest about risks, do not downplay serious issues"""


async def generate_executive_summary(
    contract_text: str,
    clauses: list[dict[str, Any]] | None = None,
    risk_scores: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generate a plain-English executive summary of a contract.

    Args:
        contract_text: The full contract text (markdown from Docling).
        clauses: Optional list of extracted clauses with metadata.
        risk_scores: Optional list of risk scores for each clause.

    Returns:
        Executive summary dict matching SUMMARY_SCHEMA.
    """
    logger.info("Generating executive summary")

    # Build context from extracted clauses and risk scores if available
    clause_context = ""
    if clauses and risk_scores:
        clause_context = "\n\nEXTRACTED CLAUSES AND RISK ANALYSIS:\n"
        for clause, risk in zip(clauses, risk_scores):
            clause_context += f"""
--- {clause.get('clause_type', 'unknown')} (Section {clause.get('section_number', 'N/A')}) ---
Risk Score: {risk.get('risk_score', 'N/A')}/100 ({risk.get('risk_level', 'N/A')})
Market Deviation: {risk.get('market_deviation', 'N/A')}
Summary: {risk.get('plain_english_summary', 'N/A')}
"""

    prompt = f"""Generate a comprehensive executive summary for the following contract.

CONTRACT TEXT:
---
{contract_text[:100000]}
---
{clause_context}

Produce a summary covering:
1. What this contract is about and who the parties are
2. Key commercial terms (pricing, payment, deliverables, timelines)
3. Who carries the most risk and why
4. Top 3 to 5 issues that need negotiation or review by a lawyer
5. Key obligations for each party

Write for a business executive who is not a lawyer."""

    result = await llm.generate_json(
        prompt=prompt,
        schema=SUMMARY_SCHEMA,
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.3,
    )

    logger.info("Executive summary generated")
    return result


def format_summary_text(summary_data: dict[str, Any]) -> str:
    """Format the structured summary into readable text.

    Args:
        summary_data: The structured summary from generate_executive_summary.

    Returns:
        Formatted plain-text summary.
    """
    parts = []

    # Title
    contract_type = summary_data.get("contract_type", "Contract")
    parties = summary_data.get("parties", [])
    parties_str = " and ".join(parties) if parties else "Unknown Parties"
    parts.append(f"EXECUTIVE SUMMARY: {contract_type}")
    parts.append(f"Parties: {parties_str}")

    if summary_data.get("effective_date"):
        parts.append(f"Effective Date: {summary_data['effective_date']}")
    if summary_data.get("term_duration"):
        parts.append(f"Term: {summary_data['term_duration']}")

    parts.append("")

    # Main summary
    parts.append(summary_data.get("summary", ""))
    parts.append("")

    # Risk carrier
    parts.append(f"RISK: {summary_data.get('risk_carrier', 'Not assessed')}")
    parts.append("")

    # Key commercial terms
    terms = summary_data.get("key_commercial_terms", [])
    if terms:
        parts.append("KEY COMMERCIAL TERMS:")
        for term in terms:
            parts.append(f"  - {term}")
        parts.append("")

    # Top issues
    issues = summary_data.get("top_issues", [])
    if issues:
        parts.append("TOP ISSUES TO NEGOTIATE:")
        for i, issue in enumerate(issues, 1):
            severity = issue.get("severity", "medium").upper()
            parts.append(f"  {i}. [{severity}] {issue.get('issue', '')}")
            if issue.get("recommendation"):
                parts.append(f"     Recommendation: {issue['recommendation']}")
        parts.append("")

    return "\n".join(parts)
