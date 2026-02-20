import json
from openai import OpenAI

client = OpenAI()


def extract_entities(user_input: str) -> dict:
    """
    Dynamically extract ALL relevant contract details from natural language.
    Returns a flat dict of whatever fields the LLM finds — no hardcoded schema.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract structured information from a contract request. "
                    "Read the entire input and return a flat JSON object with every relevant detail you find. "
                    "Use clear, descriptive key names (e.g. party_1, party_2, duration, fee_amount, "
                    "payment_schedule, territory, obligations_party_1, obligations_party_2, "
                    "governing_state, effective_date, contract_type, purpose, etc.). "
                    "Only include keys for information actually present in the input. "
                    "Do not invent or assume missing details."
                )
            },
            {"role": "user", "content": user_input}
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )

    entities = json.loads(response.choices[0].message.content)
    print(f"[extractor] Extracted entities: {json.dumps(entities, indent=2)}")
    return entities
