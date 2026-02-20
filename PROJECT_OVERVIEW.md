# Legal Contract Generator — Project Overview

---

## 1. Complexity

The system combines **three AI components** working in a pipeline:

1. **Intent & Entity Extractor** — a fast LLM call that converts free-form text into structured data
2. **RAG Retrieval** — ChromaDB vector search that fetches the right template and relevant legal clauses
3. **Contract Generation** — a second LLM call that fills the template with extracted data and legal context

This is a **multi-step agentic pipeline**, not a simple single-prompt system. Each component has a focused responsibility, which makes the system more reliable and easier to debug than a single mega-prompt.

---

## 2. Architecture

```
User Input (natural language)
        │
        ▼
┌─────────────────────┐
│   extractor.py      │  ← OpenAI JSON mode, no hardcoded schema
│   extract_entities()│    Extracts: party names, duration, fees,
│                     │    obligations, territory, governing law, etc.
└────────┬────────────┘
         │ entities dict
         ▼
┌─────────────────────┐
│   retrieval.py      │  ← ChromaDB + sentence-transformers
│   retrieve()        │    Searches indexed .txt files in /data
│                     │    Tags: "template" vs "law" by filename
└────────┬────────────┘
         │ template chunks + law chunks
         ▼
┌─────────────────────┐
│   prompts.py        │  ← Assembles the final LLM prompt
│   build_prompt()    │    Injects extracted entities, today's date,
│                     │    template text, and legal provisions
└────────┬────────────┘
         │ prompt string
         ▼
┌─────────────────────┐
│   generation.py     │  ← OpenAI gpt-4o-mini (max_tokens=16000)
│   generate_contract │    Fills placeholders, checks boxes,
│                     │    adds law-compliant clauses
└────────┬────────────┘
         │ completed contract text
         ▼
┌─────────────────────┐
│   main.py (FastAPI) │  ← POST /generate
│   /generate endpoint│    Returns JSON: { "contract": "..." }
└─────────────────────┘
```

**File responsibilities:**

| File | Role |
|------|------|
| `extractor.py` | Dynamic entity extraction (zero hardcoded fields) |
| `retrieval.py` | Document indexing + vector search (ChromaDB) |
| `prompts.py` | Prompt engineering — assembles context for the LLM |
| `generation.py` | Orchestrates the full pipeline |
| `main.py` | FastAPI server, CORS, request/response models, logging |
| `data/*.txt` | Contract templates + law reference files |

---

## 3. Laws / Legal Data

The system uses a **retrieval-augmented** approach — legal knowledge is stored as `.txt` files in `/data/`:

- **`nda_law.txt`** — Digital Personal Data Protection Act 2023 (DPDP), Gig Economy recognition, IP ownership trends, NDA enforceability
- **`nda.txt`** — Common Paper Mutual NDA v1.0 template (full standard terms inline)
- **`PartnershipAgreement.txt`** — Common Paper Partnership Agreement v1.1 template
- **`ProfessionalServicesAgreement.txt`** — Professional Services Agreement template

**Tagging logic** (`retrieval.py`):
- Files with "law", "regulation", "act", "statute" → tagged as `"law"` source
- Files with "nda", "agreement", "partnership", "services" → tagged as `"template"` source
- Law keyword takes priority (so `nda_law.txt` → law, not template)

Law chunks are passed to the LLM as context, and the prompt instructs it to **add or strengthen clauses** based on retrieved legal provisions, marking them with `"(Added per applicable law)"`.

---

## 4. Logic / Approach

### Entity Extraction (Dynamic)
Rather than defining a rigid schema, `extractor.py` uses **OpenAI JSON mode** and asks the model to extract whatever fields are present. This works for any contract type without code changes.

### Template Selection
`generation.py` uses a priority order:
1. ChromaDB retrieval result (most accurate)
2. `contract_type` from extractor (e.g., `"partnership"` → `PartnershipAgreement.txt`)
3. Keyword fallback in the raw user text

### Checkbox Filling
The prompt explicitly instructs the LLM to:
- `[ x ]` check boxes that match the user's description
- Fill `[____]` blanks on checked lines with extracted values

### Date Injection
`generation.py` calls `date.today()` and passes it as `today` to `build_prompt()`. The prompt maps it to `[Today's Date]` and all effective date placeholders.

### Signature Blocks
The prompt instructs the LLM to place party names on the `Print Name:` line directly, not above or below it.

---

## 5. Code Quality

- **Separation of concerns** — each module does exactly one thing
- **No hardcoded field names** in extractor or prompt renderer — fully extensible
- **Dynamic prompt rendering** — `prompts.py` iterates over whatever entities dict is passed
- **Structured logging** — `requests.log` captures every incoming request method, URL, and body
- **CORS enabled** — API accessible from any frontend (`allow_origins=["*"]`)
- **Error handling** — FastAPI returns 400 for empty input, 500 with error detail for failures
- **Re-indexing safe** — ChromaDB uses `upsert` so re-running `index_documents()` is idempotent

---

## 6. Potential Improvements

| Area | Suggestion |
|------|------------|
| State placeholder | Ask user for governing state if not provided |
| Streaming | Use OpenAI streaming for faster perceived response |
| Auth | Add API key authentication before production |
| CORS | Restrict `allow_origins` to known frontend URLs |
| More templates | Add Employment, Lease, SaaS Agreement templates |
| Frontend | Build a proper form UI instead of raw text input |
| Tests | Add unit tests for extractor, retrieval, and prompt builder |
