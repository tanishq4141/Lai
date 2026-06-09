"""
Clause comparison service.
Provides side-by-side comparison of the same clause type across multiple
contracts, essential for due-diligence scenarios.
"""

import logging
from typing import Any

from app.services import llm

logger = logging.getLogger(__name__)

COMPARISON_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "Overall comparison summary across all contracts",
        },
        "key_differences": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "aspect": {
                        "type": "string",
                        "description": "The aspect being compared (e.g. liability cap, notice period)",
                    },
                    "differences": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "contract_name": {"type": "string"},
                                "value": {"type": "string"},
                            },
                            "required": ["contract_name", "value"],
                        },
                    },
                    "assessment": {
                        "type": "string",
                        "description": "Which contract's version is most/least favorable",
                    },
                },
                "required": ["aspect", "differences", "assessment"],
            },
        },
        "most_favorable": {
            "type": "string",
            "description": "Which contract has the most favorable version of this clause",
        },
        "most_risky": {
            "type": "string",
            "description": "Which contract has the riskiest version of this clause",
        },
        "recommendation": {
            "type": "string",
            "description": "Recommendation for which contract's clause to use as template",
        },
    },
    "required": ["summary", "key_differences", "most_favorable", "most_risky"],
}


async def compare_clauses(
    clause_pairs: list[dict[str, str]],
    clause_type: str,
) -> dict[str, Any]:
    """Compare the same clause type across multiple contracts.

    Args:
        clause_pairs: List of dicts with 'contract_name' and 'clause_text'.
        clause_type: The type of clause being compared.

    Returns:
        Comparison result dict with differences, assessments, and recommendations.
    """
    if len(clause_pairs) < 2:
        return {
            "summary": "Need at least 2 contracts to compare.",
            "key_differences": [],
            "most_favorable": "",
            "most_risky": "",
        }

    logger.info(
        f"Comparing {clause_type} clause across {len(clause_pairs)} contracts"
    )

    # Build the comparison prompt
    clauses_section = ""
    for i, pair in enumerate(clause_pairs, 1):
        clauses_section += f"""
CONTRACT {i}: {pair['contract_name']}
---
{pair['clause_text']}
---
"""

    prompt = f"""Compare the following {clause_type} clauses from {len(clause_pairs)} different contracts.

{clauses_section}

Analyze:
1. What are the key differences between these clauses?
2. Which version is most favorable (least risky)?
3. Which version is most risky?
4. What specific aspects differ (caps, notice periods, scope, exceptions)?
5. Recommend which contract's version would be the best template.

Be specific about numbers, dates, and scope differences."""

    system_instruction = """You are a legal analyst doing due-diligence clause comparison.
Compare clauses across contracts, identify differences, and assess which
versions are more or less favorable. Be specific and quantitative where possible."""

    result = await llm.generate_json(
        prompt=prompt,
        schema=COMPARISON_SCHEMA,
        system_instruction=system_instruction,
        temperature=0.2,
    )

    return result


async def compare_against_baseline(
    clause_text: str,
    clause_type: str,
    baseline_text: str,
) -> dict[str, Any]:
    """Compare a single clause against a market-standard baseline.

    Args:
        clause_text: The clause text from the contract.
        clause_type: The type of clause.
        baseline_text: The market-standard baseline text.

    Returns:
        Dict with deviation assessment and explanation.
    """
    schema = {
        "type": "object",
        "properties": {
            "deviation": {
                "type": "string",
                "enum": ["favourable", "unfavourable", "unusual", "standard"],
            },
            "deviation_score": {
                "type": "number",
                "description": "How far from standard (0 = identical, 100 = completely different)",
            },
            "explanation": {
                "type": "string",
                "description": "Plain-English explanation of the deviation",
            },
            "specific_differences": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "aspect": {"type": "string"},
                        "standard_value": {"type": "string"},
                        "contract_value": {"type": "string"},
                        "impact": {
                            "type": "string",
                            "enum": ["positive", "negative", "neutral"],
                        },
                    },
                    "required": ["aspect", "standard_value", "contract_value", "impact"],
                },
            },
        },
        "required": ["deviation", "deviation_score", "explanation"],
    }

    prompt = f"""Compare this {clause_type} clause from a contract against the market-standard baseline.

CONTRACT CLAUSE:
---
{clause_text}
---

MARKET-STANDARD BASELINE:
---
{baseline_text}
---

Assess how the contract clause deviates from the standard:
- "favourable" = better than standard (less risk for the reviewing party)
- "unfavourable" = worse than standard (more risk)
- "unusual" = significantly different in an unexpected way
- "standard" = substantially similar to the baseline

List specific differences between the two."""

    return await llm.generate_json(
        prompt=prompt,
        schema=schema,
        temperature=0.2,
    )
