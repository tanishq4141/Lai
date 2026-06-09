"""
Risk scoring service.
Combines rule-based heuristics with LLM-based analysis to score
each clause and the overall contract for risk.

Risk levels: low (0-25), medium (26-50), high (51-75), critical (76-100)
Risk categories: financial, operational, legal, reputational
"""

import logging
import re
from typing import Any

from app.services import llm

logger = logging.getLogger(__name__)


# --- Rule-based risk patterns ---
# Each pattern has: regex, risk_adjustment, category, description
RISK_PATTERNS = [
    # High risk indicators
    {
        "pattern": r"unlimited\s+liability|no\s+cap\s+on\s+(liability|damages)",
        "adjustment": +30,
        "category": "financial",
        "description": "Uncapped liability exposure",
    },
    {
        "pattern": r"indemnif(y|ies|ication)\s+.*\b(all|any|every)\b.*\b(claims?|losses?|damages?|costs?)\b",
        "adjustment": +20,
        "category": "financial",
        "description": "Broad indemnification obligation",
    },
    {
        "pattern": r"sole\s+(discretion|judgment)|unilateral(ly)?",
        "adjustment": +15,
        "category": "legal",
        "description": "One-sided discretionary power",
    },
    {
        "pattern": r"irrevocable|perpetual|forever|in\s+perpetuity",
        "adjustment": +15,
        "category": "legal",
        "description": "Irrevocable or perpetual obligation",
    },
    {
        "pattern": r"waive[sd]?\s+(any|all)\s+(rights?|claims?|defenses?)",
        "adjustment": +20,
        "category": "legal",
        "description": "Broad waiver of rights",
    },
    {
        "pattern": r"assign\s+all\s+(intellectual\s+property|ip|rights)",
        "adjustment": +20,
        "category": "operational",
        "description": "Full IP assignment",
    },
    {
        "pattern": r"terminat(e|ion)\s+.*without\s+(cause|reason|notice)|immediate\s+termination",
        "adjustment": +20,
        "category": "operational",
        "description": "Termination without cause or notice",
    },
    {
        "pattern": r"liquidated\s+damages|penalty\s+(clause|provision)",
        "adjustment": +15,
        "category": "financial",
        "description": "Liquidated damages or penalty provision",
    },
    {
        "pattern": r"non-compete|non\s*competition|restrictive\s+covenant",
        "adjustment": +10,
        "category": "operational",
        "description": "Non-compete restriction",
    },
    {
        "pattern": r"automatic(ally)?\s+renew|auto-renew|evergreen",
        "adjustment": +10,
        "category": "operational",
        "description": "Auto-renewal provision",
    },

    # Medium risk indicators
    {
        "pattern": r"reasonable\s+efforts?|best\s+efforts?|commercially\s+reasonable",
        "adjustment": +5,
        "category": "legal",
        "description": "Vague effort standard",
    },
    {
        "pattern": r"material\s+adverse\s+(change|effect)|force\s+majeure",
        "adjustment": +5,
        "category": "operational",
        "description": "Material adverse change or force majeure provision",
    },

    # Risk-reducing indicators
    {
        "pattern": r"mutual(ly)?|reciprocal|both\s+parties",
        "adjustment": -10,
        "category": "legal",
        "description": "Mutual/reciprocal obligation (balanced)",
    },
    {
        "pattern": r"cap(ped)?\s+at|maximum\s+(aggregate\s+)?liability|not\s+exceed",
        "adjustment": -10,
        "category": "financial",
        "description": "Liability cap present",
    },
    {
        "pattern": r"(?:30|60|90)\s+days?\s+(?:written\s+)?notice",
        "adjustment": -5,
        "category": "operational",
        "description": "Reasonable notice period",
    },
]

# Risk schema for LLM assessment
RISK_ASSESSMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "risk_score": {
            "type": "number",
            "description": "Risk score from 0 (no risk) to 100 (extreme risk)",
        },
        "risk_level": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"],
        },
        "risk_category": {
            "type": "string",
            "enum": ["financial", "operational", "legal", "reputational"],
            "description": "Primary risk category",
        },
        "market_deviation": {
            "type": "string",
            "enum": ["favourable", "unfavourable", "unusual", "standard"],
        },
        "deviation_explanation": {
            "type": "string",
            "description": "Explanation of how this clause deviates from market standard",
        },
        "plain_english_summary": {
            "type": "string",
            "description": "One to two sentence plain-English explanation of what this clause means",
        },
        "key_risks": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of specific risks identified in this clause",
        },
    },
    "required": [
        "risk_score",
        "risk_level",
        "risk_category",
        "market_deviation",
        "deviation_explanation",
        "plain_english_summary",
    ],
}


def score_clause_rules(clause_text: str) -> dict[str, Any]:
    """Apply rule-based risk scoring to a clause.

    Args:
        clause_text: The text of the clause.

    Returns:
        Dict with: base_score, adjustments (list), category_scores
    """
    base_score = 50  # Neutral starting point
    adjustments = []
    category_scores = {
        "financial": 0,
        "operational": 0,
        "legal": 0,
        "reputational": 0,
    }

    text_lower = clause_text.lower()

    for pattern_def in RISK_PATTERNS:
        if re.search(pattern_def["pattern"], text_lower, re.IGNORECASE):
            adjustments.append({
                "description": pattern_def["description"],
                "adjustment": pattern_def["adjustment"],
                "category": pattern_def["category"],
            })
            category_scores[pattern_def["category"]] += abs(pattern_def["adjustment"])

    total_adjustment = sum(a["adjustment"] for a in adjustments)
    final_score = max(0, min(100, base_score + total_adjustment))

    return {
        "base_score": base_score,
        "rule_score": final_score,
        "adjustments": adjustments,
        "category_scores": category_scores,
    }


async def score_clause_llm(
    clause_text: str,
    clause_type: str,
    baseline_text: str | None = None,
) -> dict[str, Any]:
    """Use Gemini to assess risk for a clause with optional market-standard comparison.

    Args:
        clause_text: The text of the clause.
        clause_type: The type of clause (e.g. 'indemnity').
        baseline_text: Optional market-standard clause to compare against.

    Returns:
        Risk assessment dict matching RISK_ASSESSMENT_SCHEMA.
    """
    comparison_section = ""
    if baseline_text:
        comparison_section = f"""
MARKET-STANDARD BASELINE FOR COMPARISON:
---
{baseline_text}
---
Compare the clause above against this baseline. Note any deviations that increase or decrease risk."""

    prompt = f"""Analyze the following {clause_type} clause from a contract for risk.

CLAUSE TEXT:
---
{clause_text}
---
{comparison_section}

Assess:
1. Overall risk score (0-100)
2. Risk level (low/medium/high/critical)
3. Primary risk category (financial/operational/legal/reputational)
4. Market deviation (favourable/unfavourable/unusual/standard)
5. Explanation of any deviation from market norms
6. Plain-English summary a non-lawyer would understand
7. Specific risks identified"""

    system_instruction = """You are a legal risk analyst. Assess contract clauses for risk.

Scoring guide:
- 0-25 (low): Standard terms, balanced, well-drafted
- 26-50 (medium): Minor deviations from standard, some favorable terms for one party
- 51-75 (high): Significant deviations, one-sided terms, potential exposure
- 76-100 (critical): Extreme risk, unusual provisions, major financial exposure

Always explain in plain English. Avoid legal jargon in the summary."""

    return await llm.generate_json(
        prompt=prompt,
        schema=RISK_ASSESSMENT_SCHEMA,
        system_instruction=system_instruction,
        temperature=0.2,
    )


async def score_clause(
    clause_text: str,
    clause_type: str,
    baseline_text: str | None = None,
) -> dict[str, Any]:
    """Combined risk scoring: rules + LLM.

    The final score blends rule-based heuristics (fast, deterministic)
    with LLM analysis (nuanced, contextual). Rules provide a floor/ceiling
    adjustment, and the LLM provides the primary assessment.

    Args:
        clause_text: The text of the clause.
        clause_type: The type of clause.
        baseline_text: Optional market-standard clause text.

    Returns:
        Combined risk assessment with both rule and LLM insights.
    """
    # Step 1: Rule-based scoring
    rule_result = score_clause_rules(clause_text)

    # Step 2: LLM-based scoring
    llm_result = await score_clause_llm(clause_text, clause_type, baseline_text)

    # Step 3: Blend scores (60% LLM, 40% rules)
    llm_score = llm_result.get("risk_score", 50)
    rule_score = rule_result["rule_score"]
    blended_score = round(0.6 * llm_score + 0.4 * rule_score)
    blended_score = max(0, min(100, blended_score))

    # Determine risk level from blended score
    if blended_score <= 25:
        risk_level = "low"
    elif blended_score <= 50:
        risk_level = "medium"
    elif blended_score <= 75:
        risk_level = "high"
    else:
        risk_level = "critical"

    return {
        "risk_score": blended_score,
        "risk_level": risk_level,
        "risk_category": llm_result.get("risk_category", "legal"),
        "market_deviation": llm_result.get("market_deviation", "standard"),
        "deviation_explanation": llm_result.get("deviation_explanation", ""),
        "plain_english_summary": llm_result.get("plain_english_summary", ""),
        "key_risks": llm_result.get("key_risks", []),
        "rule_adjustments": rule_result["adjustments"],
        "category_scores": rule_result["category_scores"],
    }


def compute_overall_risk(clause_scores: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute overall contract risk from individual clause scores.

    Args:
        clause_scores: List of clause risk assessment results.

    Returns:
        Dict with overall_score, risk_level, and risk_breakdown by category.
    """
    if not clause_scores:
        return {
            "overall_score": 0,
            "risk_level": "low",
            "risk_breakdown": {
                "financial": 0,
                "operational": 0,
                "legal": 0,
                "reputational": 0,
            },
        }

    # Overall score: weighted average with emphasis on highest risks
    scores = [s.get("risk_score", 50) for s in clause_scores]
    avg_score = sum(scores) / len(scores)
    max_score = max(scores)

    # Blend average with max to penalize contracts with even one critical clause
    overall = round(0.6 * avg_score + 0.4 * max_score)

    # Category breakdown: average of category-specific scores
    category_breakdown = {
        "financial": 0.0,
        "operational": 0.0,
        "legal": 0.0,
        "reputational": 0.0,
    }

    category_counts = {k: 0 for k in category_breakdown}
    for clause in clause_scores:
        cat = clause.get("risk_category", "legal")
        if cat in category_breakdown:
            category_breakdown[cat] += clause.get("risk_score", 50)
            category_counts[cat] += 1

    for cat in category_breakdown:
        if category_counts[cat] > 0:
            category_breakdown[cat] = round(
                category_breakdown[cat] / category_counts[cat]
            )

    # Determine risk level
    if overall <= 25:
        risk_level = "low"
    elif overall <= 50:
        risk_level = "medium"
    elif overall <= 75:
        risk_level = "high"
    else:
        risk_level = "critical"

    return {
        "overall_score": overall,
        "risk_level": risk_level,
        "risk_breakdown": category_breakdown,
    }
