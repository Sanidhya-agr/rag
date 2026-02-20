def build_prompt(user_input, template_chunks, law_chunks, entities=None, today=None):
    template_text = "\n\n".join(template_chunks) if template_chunks else "No template provided. Please draft from scratch using standard legal practices."
    law_text = "\n\n".join(law_chunks) if law_chunks else "No specific legal provisions retrieved."

    # Dynamically render every extracted field — no hardcoded field names
    if entities:
        lines = [f"  - {key.replace('_', ' ').title()}: {value}"
                 for key, value in entities.items() if value]
        extracted_block = "Extracted details from user description:\n" + "\n".join(lines) if lines else ""
    else:
        extracted_block = ""

    # Always include today's date
    date_line = f"  - Today's Date: {today}" if today else ""
    if date_line:
        extracted_block = (extracted_block + "\n" + date_line) if extracted_block else f"Extracted details from user description:\n{date_line}"

    prompt = f"""You are an expert legal assistant completing a contract template based on the user's description.

User description:
{user_input}

{extracted_block}

Template (from a trusted source):
{template_text}

Relevant legal provisions (for reference):
{law_text}

Instructions:
1. Reproduce the ENTIRE template in full — every section, clause, and subsection. Do NOT skip or omit any part.

2. Replace EVERY placeholder using the Extracted details above. Match by meaning:
   - Party 1 name → replaces PARTY 1 headings, [Company name], [Disclosing Party], first-party signature fields
   - Party 2 name → replaces PARTY 2 headings, [Partner name], [Receiving Party], second-party signature fields
   - Duration      → replaces duration/term/end-date placeholders
   - Fee Amount    → replaces payment amount blanks [____]
   - Payment Schedule → replaces [Fill in payment schedule]
   - Territory     → replaces [fill in specific geographic areas]
   - Governing State → replaces [fill in state and/or country]
   - TODAY'S DATE  → replaces [Today's Date], [Effective Date], and any date placeholders

3. Signature blocks: In every signature block, fill the "Print Name:" line with the correct party's name. Place the name directly after "Print Name:" on the same line.

4. For checkbox fields `[    ]`:
   - Mark `[ x ]` on any line that matches the extracted details.
   - Fill in `[____]` on checked lines with the relevant extracted value.
   - Leave unchecked `[    ]` on lines not applicable to this agreement.

5. Formatting: Preserve paragraph spacing throughout — keep a blank line between each numbered clause in the Standard Terms. Do not merge paragraphs together.

6. Where the Relevant Legal Provisions mention specific obligations, strengthen or add the clause. Mark added clauses with "(Added per applicable law)".

7. Do NOT add, remove, or reorder sections beyond what is instructed above.

Contract:"""
    return prompt