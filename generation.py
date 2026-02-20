import os
import openai
from datetime import date
from openai import OpenAI
from retrieval import retrieve
from prompts import build_prompt
from extractor import extract_entities

client = OpenAI()



def _load_full_template(template_path):
    if not os.path.exists(template_path):
        return None
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

def _first_template_file(metas):
    for meta in metas:
        if isinstance(meta, dict) and meta.get("source") == "template":
            return meta.get("file")
    return None

def _first_file_any(metas):
    for meta in metas:
        if isinstance(meta, dict) and meta.get("file"):
            return meta.get("file")
    return None

def _maybe_log_prompt(prompt, template_file, template_len, law_len):
    # Always log the prompt and metadata for transparency.
    print("\n--- LLM INPUT DEBUG START ---")
    print("PROMPT:\n")
    print(prompt)
    print("\n--- LLM INPUT SUMMARY ---")
    if template_file:
        print(f"TEMPLATE FILE:  {template_file}")
    print(f"TEMPLATE CHARS: {template_len}   ({'OK - full file loaded' if template_len > 500 else 'WARNING: very short!'})")
    print(f"LAW CHARS:      {law_len}   ({'OK' if law_len > 0 else 'None retrieved'})")
    print(f"TOTAL PROMPT:   {len(prompt)} chars")
    print("--- LLM INPUT DEBUG END ---\n")

def generate_contract(user_input):
    # Step 1: Extract structured entities from the user's natural language
    entities = extract_entities(user_input)

    # Step 2: Retrieve relevant chunks (more results = more law context)
    docs, metas, distances = retrieve(user_input, n_results=10)

    # Separate templates and laws
    template_chunks = [d for d, m in zip(docs, metas) if m['source'] == 'template']
    law_chunks = [d for d, m in zip(docs, metas) if m['source'] == 'law']

    # Step 3: Load the full template file based on retrieval or contract_type
    template_file = _first_template_file(metas) or _first_file_any(metas)
    contract_type = entities.get("contract_type", "")
    q_lower = user_input.lower()
    if not template_file and (contract_type == "nda" or "nda" in q_lower or "non-disclosure" in q_lower or "confidential" in q_lower):
        template_file = "nda.txt"
    elif not template_file and (contract_type == "partnership" or "partnership" in q_lower):
        template_file = "PartnershipAgreement.txt"
    elif not template_file and (contract_type == "services" or "service" in q_lower):
        template_file = "ProfessionalServicesAgreement.txt"
    if template_file:
        full_template = _load_full_template(os.path.join("data", template_file))
        if full_template:
            template_chunks = [full_template]

    # Step 4: Build the prompt with entities for reliable placeholder substitution
    today = date.today().strftime("%B %d, %Y")  # e.g. "February 21, 2026"
    prompt = build_prompt(user_input, template_chunks, law_chunks, entities=entities, today=today)

    # Debug: log full prompt to terminal
    # _maybe_log_prompt(
    #     prompt,
    #     template_file=template_file,
    #     template_len=len(template_chunks[0]) if template_chunks else 0,
    #     law_len=sum(len(c) for c in law_chunks) if law_chunks else 0,
    # )

    # Call OpenAI with streaming enabled
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                "You are completing a legal contract template. "
                "You MUST replace ALL placeholders with the extracted details provided. "
                "This includes section headings — 'PARTY 1' must be replaced with the actual Party 1 name, "
                "'PARTY 2' with the actual Party 2 name. "
                "Reproduce the entire template verbatim otherwise. Do not skip any section."
            )},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=16000,
        stream=True,
    )

    # Yield each text chunk as it arrives from OpenAI
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
