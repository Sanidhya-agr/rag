"""
contract_scanner.py
───────────────────
Uses the CUAD-fine-tuned RoBERTa model (Rakib/roberta-base-on-cuad) to
extract key legal clauses from contract text via extractive QA.
"""

import textwrap
from transformers import pipeline

# ── Model (lazy-loaded on first call) ──────────────────────────────────────────
_qa_pipeline = None
MODEL_NAME = "Rakib/roberta-base-on-cuad"


def _get_pipeline():
    """Lazy-load the QA pipeline so the model is only downloaded once."""
    global _qa_pipeline
    if _qa_pipeline is None:
        print(f"[contract_scanner] Loading CUAD model ({MODEL_NAME}) …")
        _qa_pipeline = pipeline(
            "question-answering",
            model=MODEL_NAME,
            tokenizer=MODEL_NAME,
            device=-1,           # CPU  (set to 0 for GPU)
            handle_long_inputs="stride",
        )
        print("[contract_scanner] Model loaded ✓")
    return _qa_pipeline


# ── 15 high-risk CUAD clause categories ───────────────────────────────────────
# Each entry is (category_label, question) — the questions mirror CUAD training.
CUAD_QUESTIONS: list[tuple[str, str]] = [
    (
        "Document Name",
        'Highlight the parts (if any) of this contract related to '
        '"Document Name" that should be reviewed by a lawyer. '
        'Details: The name of the contract.',
    ),
    (
        "Parties",
        'Highlight the parts (if any) of this contract related to '
        '"Parties" that should be reviewed by a lawyer. '
        'Details: The two or more parties who signed the contract.',
    ),
    (
        "Agreement Date",
        'Highlight the parts (if any) of this contract related to '
        '"Agreement Date" that should be reviewed by a lawyer. '
        'Details: The date of the contract.',
    ),
    (
        "Termination For Convenience",
        'Highlight the parts (if any) of this contract related to '
        '"Termination For Convenience" that should be reviewed by a lawyer. '
        'Details: Can a party terminate this contract without cause?',
    ),
    (
        "Renewal Term",
        'Highlight the parts (if any) of this contract related to '
        '"Renewal Term" that should be reviewed by a lawyer. '
        'Details: What is the renewal term after the initial term expires?',
    ),
    (
        "Non-Compete",
        'Highlight the parts (if any) of this contract related to '
        '"Non-Compete" that should be reviewed by a lawyer. '
        'Details: Is there a restriction on the ability of a party to compete '
        'with the counterparty?',
    ),
    (
        "Exclusivity",
        'Highlight the parts (if any) of this contract related to '
        '"Exclusivity" that should be reviewed by a lawyer. '
        'Details: Is there an exclusive dealing commitment with the '
        'counterparty?',
    ),
    (
        "Governing Law",
        'Highlight the parts (if any) of this contract related to '
        '"Governing Law" that should be reviewed by a lawyer. '
        'Details: Which state/country\'s law governs the contract?',
    ),
    (
        "Limitation Of Liability",
        'Highlight the parts (if any) of this contract related to '
        '"Limitation Of Liability" that should be reviewed by a lawyer. '
        'Details: Is there a cap on liability upon the breach of a party\'s '
        'obligations?',
    ),
    (
        "Indemnification",
        'Highlight the parts (if any) of this contract related to '
        '"Indemnification" that should be reviewed by a lawyer. '
        'Details: Is there a requirement for a party to indemnify the '
        'counterparty?',
    ),
    (
        "Confidentiality",
        'Highlight the parts (if any) of this contract related to '
        '"Confidentiality" that should be reviewed by a lawyer. '
        'Details: Is there a requirement for a party to keep certain '
        'information confidential?',
    ),
    (
        "IP Ownership Assignment",
        'Highlight the parts (if any) of this contract related to '
        '"IP Ownership Assignment" that should be reviewed by a lawyer. '
        'Details: Does intellectual property created by one party become the '
        'property of the counterparty?',
    ),
    (
        "Non-Solicitation",
        'Highlight the parts (if any) of this contract related to '
        '"Non-Solicitation" that should be reviewed by a lawyer. '
        'Details: Is a party restricted from contracting or soliciting '
        'customers or employees of the counterparty?',
    ),
    (
        "Uncapped Liability",
        'Highlight the parts (if any) of this contract related to '
        '"Uncapped Liability" that should be reviewed by a lawyer. '
        'Details: Is a party\'s liability uncapped upon breach?',
    ),
    (
        "Liquidated Damages",
        'Highlight the parts (if any) of this contract related to '
        '"Liquidated Damages" that should be reviewed by a lawyer. '
        'Details: Does the contract contain a specification of damages or '
        'other remedies for breach?',
    ),
]

# Minimum confidence score to consider an answer valid
CONFIDENCE_THRESHOLD = 0.05


# ── Chunking helper (RoBERTa max ≈ 512 tokens ≈ ~2 000 chars) ─────────────────
def _chunk_text(text: str, chunk_size: int = 1800, overlap: int = 200) -> list[str]:
    """Split text into overlapping character windows."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def scan_contract(text: str) -> dict:
    """
    Run the CUAD extractive-QA model across all clause categories.

    Returns
    -------
    dict  –  {
        "category_name": {
            "answer": str,     # extracted text span (or empty string)
            "score": float,    # model confidence 0-1
            "found": bool      # whether answer exceeded threshold
        },
        ...
    }
    """
    qa = _get_pipeline()
    chunks = _chunk_text(text)
    results: dict = {}

    for category, question in CUAD_QUESTIONS:
        best_answer = ""
        best_score = 0.0

        for chunk in chunks:
            try:
                out = qa(question=question, context=chunk)
                if out["score"] > best_score:
                    best_score = out["score"]
                    best_answer = out["answer"]
            except Exception:
                continue  # skip problematic chunks

        found = best_score >= CONFIDENCE_THRESHOLD and len(best_answer.strip()) > 0
        results[category] = {
            "answer": best_answer.strip() if found else "",
            "score": round(best_score, 4),
            "found": found,
        }

    return results
