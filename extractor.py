import json
from openai import OpenAI

client = OpenAI()

# Schema for structured entity extraction via function calling
_EXTRACT_TOOL = [{
    "type": "function",
    "function": {
        "name": "extract_contract_entities",
        "description": "Extract structured details from a user's contract request.",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_type": {
                    "type": "string",
                    "enum": ["nda", "partnership", "services", "other"],
                    "description": "The type of contract requested."
                },
                "party_1": {
                    "type": "string",
                    "description": "Full name of the first party (Party A / Disclosing Party / Company). Empty string if not mentioned."
                },
                "party_2": {
                    "type": "string",
                    "description": "Full name of the second party (Party B / Receiving Party / Partner). Empty string if not mentioned."
                },
                "duration": {
                    "type": "string",
                    "description": "Duration or term of the agreement, e.g. '2 years', '6 months'. Empty string if not mentioned."
                },
                "purpose": {
                    "type": "string",
                    "description": "Purpose or reason for the agreement. Empty string if not mentioned."
                },
                "governing_state": {
                    "type": "string",
                    "description": "Governing state or country, e.g. 'California', 'India'. Empty string if not mentioned."
                },
                "effective_date": {
                    "type": "string",
                    "description": "Effective date if explicitly mentioned, e.g. 'January 1, 2025'. Empty string if not mentioned."
                }
            },
            "required": [
                "contract_type", "party_1", "party_2",
                "duration", "purpose", "governing_state", "effective_date"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
}]


def extract_entities(user_input: str) -> dict:
    """
    Extract structured contract entities from a natural language description.
    Returns a dict with keys: contract_type, party_1, party_2, duration,
    purpose, governing_state, effective_date.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract structured information from contract requests. "
                    "Return empty string for any field not clearly mentioned."
                )
            },
            {"role": "user", "content": user_input}
        ],
        tools=_EXTRACT_TOOL,
        tool_choice={"type": "function", "function": {"name": "extract_contract_entities"}},
        temperature=0.0,
    )

    tool_call = response.choices[0].message.tool_calls[0]
    entities = json.loads(tool_call.function.arguments)
    print(f"[extractor] Extracted entities: {entities}")
    return entities
