"""
risk_assessment.py
──────────────────
Takes CUAD-extracted clause data and returns a structured JSON risk-assessment
from GPT-4o-mini.
"""

import json
from openai import OpenAI

client = OpenAI()

RISK_SCHEMA_EXAMPLE = """{
  "overallRisk": "Red | Yellow | Green",
  "summary": "2-3 line explanation of the overall risk profile",
  "risks": [
    {
      "severity": "High | Medium | Low",
      "title": "Short title of the risk (e.g., Unlimited Liability)",
      "issue": "Plain English explanation of what is wrong",
      "suggestion": "Short counter suggestion or mitigation strategy"
    }
  ]
}"""


def _build_risk_prompt(extracted_clauses: dict) -> str:
    """Build the risk-assessment prompt from extracted CUAD clauses."""

    found = {k: v for k, v in extracted_clauses.items() if v["found"]}
    missing = [k for k, v in extracted_clauses.items() if not v["found"]]

    lines = []
    for cat, info in found.items():
        lines.append(f"- {cat} (confidence {info['score']:.0%}): {info['answer']}")

    extracted_block = "\n".join(lines) if lines else "No clauses were extracted."
    missing_block = ", ".join(missing) if missing else "None"

    return f"""Analyze the following contract clauses for legal risks.
Respond ONLY in valid JSON.
Do not include markdown.
Do not include explanation outside JSON.
Do not wrap in triple backticks.

The output must follow this strict schema:
{RISK_SCHEMA_EXAMPLE}

## Extracted Clauses
{extracted_block}

## Missing Clause Categories
{missing_block}

Consider both the extracted clauses AND the missing categories when assessing risk.
Missing critical clauses (like Limitation of Liability, Indemnification, Confidentiality) should be flagged as risks."""


def assess_risk(extracted_clauses: dict) -> dict:
    """
    Produce a structured risk-assessment for the given CUAD extractions.

    Returns
    -------
    dict — parsed JSON with keys: overallRisk, summary, risks
    """
    prompt = _build_risk_prompt(extracted_clauses)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior legal risk analyst. Produce structured, "
                    "actionable contract risk assessments. Respond ONLY in valid JSON "
                    "matching the schema provided. No markdown, no extra text."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=4000,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if the model wraps them anyway
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3].strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: wrap the raw text so callers always get a valid structure
        result = {
            "overallRisk": "Yellow",
            "summary": "Could not parse structured response from LLM.",
            "risks": [
                {
                    "severity": "Medium",
                    "title": "Parse Error",
                    "issue": raw[:500],
                    "suggestion": "Re-run the analysis or review the raw output.",
                }
            ],
        }

    return result
