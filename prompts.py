def build_prompt(user_input, template_chunks, law_chunks, entities=None):
    template_text = "\n\n".join(template_chunks) if template_chunks else "No template provided. Please draft from scratch using standard legal practices."
    law_text = "\n\n".join(law_chunks) if law_chunks else "No specific legal provisions retrieved."

    # Build a clean extracted-details block from the entities dict
    if entities:
        details_lines = []
        if entities.get("party_1"):
            details_lines.append(f"  - Party 1 (first party / Company / Disclosing Party): {entities['party_1']}")
        if entities.get("party_2"):
            details_lines.append(f"  - Party 2 (second party / Partner / Receiving Party): {entities['party_2']}")
        if entities.get("duration"):
            details_lines.append(f"  - Duration / Term: {entities['duration']}")
        if entities.get("purpose"):
            details_lines.append(f"  - Purpose: {entities['purpose']}")
        if entities.get("governing_state"):
            details_lines.append(f"  - Governing State/Country: {entities['governing_state']}")
        if entities.get("effective_date"):
            details_lines.append(f"  - Effective Date: {entities['effective_date']}")
        extracted_block = "Extracted details from user description:\n" + "\n".join(details_lines) if details_lines else ""
    else:
        extracted_block = ""

    prompt = f"""You are an expert legal assistant. Your task is to complete the provided contract template based on the user's description.

User description:
{user_input}

{extracted_block}

Template (from a trusted source):
{template_text}

Relevant legal provisions (for reference):
{law_text}

Instructions:
1. Reproduce the ENTIRE template in full — every section, clause, and subsection. Do NOT skip or omit any part.

2. Replace EVERY bracketed placeholder using the Extracted details above. Use these substitutions:
   - Placeholders for Party 1 (e.g. [official company name], PARTY 1, [Disclosing Party name]) → use Party 1 name
   - Placeholders for Party 2 (e.g. PARTY 2, [Receiving Party name], Partner) → use Party 2 name
   - Duration placeholders (e.g. [1 year(s)], [# year(s)]) → use Duration value
   - State/jurisdiction placeholders (e.g. [Fill in state]) → use Governing State if provided
   - Effective date placeholders → use Effective Date if provided
   - If a value is not provided, leave the placeholder as-is.

3. Where the Relevant Legal Provisions mention specific obligations (e.g., data protection, IP ownership), strengthen or add the corresponding clause. Mark any added clause with "(Added per applicable law)".

4. Do NOT add, remove, or reorder any other sections.

Contract:"""
    return prompt