def build_prompt(user_input, template_chunks, law_chunks):
    template_text = "\n\n".join(template_chunks) if template_chunks else "No template provided. Please draft from scratch using standard legal practices."
    law_text = "\n\n".join(law_chunks) if law_chunks else "No specific legal provisions retrieved."

    prompt = f"""You are an expert legal assistant. Your task is to complete the provided contract template based on the user's description.

User description:
{user_input}

Template (from a trusted source):
{template_text}

Relevant legal provisions (for reference):
{law_text}

Instructions:
1. First, extract all details from the User description:
   - Party names (Party 1 / Party A / Company / Partner / Disclosing Party / Receiving Party)
   - Duration / term (e.g. "2 years")
   - Purpose of the agreement
   - Governing state or country
   - Any other named values (dates, amounts, locations)

2. Reproduce the ENTIRE template in full — every section, clause, and subsection. Do NOT skip or omit any part.

3. Replace EVERY bracketed placeholder in the template using the extracted details above.
   Examples:
   - [official company name] → replace with the Party 1 name from the description
   - [Fill in state] → replace with state/country if mentioned, else leave placeholder
   - [# year(s)] → replace with the duration from the description
   - "PARTY 1", "PARTY 2" headings → replace with the actual party names from the description

4. Where the Relevant Legal Provisions mention specific obligations (e.g., data protection, IP ownership), add or strengthen the corresponding clause. Mark added clauses with "(Added per applicable law)".

5. Do NOT add, remove, or reorder any other sections.

Contract:"""
    return prompt