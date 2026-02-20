import os
import openai
from openai import OpenAI
from retrieval import retrieve
from prompts import build_prompt

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
    # Retrieve relevant chunks (more results = more law context for the LLM)
    docs, metas, distances = retrieve(user_input, n_results=10)

    # Separate templates and laws
    template_chunks = [d for d, m in zip(docs, metas) if m['source'] == 'template']
    law_chunks = [d for d, m in zip(docs, metas) if m['source'] == 'law']

    # Send the full template (all terms) to the LLM whenever a file is retrieved
    template_file = _first_template_file(metas) or _first_file_any(metas)
    # Fallback: if no template found but query is clearly NDA-related, force nda.txt
    q_lower = user_input.lower()
    if not template_file and ("nda" in q_lower or "non-disclosure" in q_lower or "nondisclosure" in q_lower or "confidential" in q_lower):
        template_file = "nda.txt"
    if template_file:
        full_template = _load_full_template(os.path.join("data", template_file))
        if full_template:
            template_chunks = [full_template]

    # Build the prompt
    prompt = build_prompt(user_input, template_chunks, law_chunks)

    # Debug: always log prompt and metadata for transparency
    # _maybe_log_prompt(
    #     prompt,
    #     template_file=template_file,
    #     template_len=len(template_chunks[0]) if template_chunks else 0,
    #     law_len=sum(len(c) for c in law_chunks) if law_chunks else 0,
    # )

    # Call OpenAI using the new client syntax
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You must reproduce the ENTIRE template verbatim. Do NOT skip, summarize, or reference external URLs for the Standard Terms section — copy it in full."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=16000,
        )
    

    # Access the response content using dot notation (also new)
    return response.choices[0].message.content
