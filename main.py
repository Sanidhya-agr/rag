from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from generation import generate_contract
from contract_scanner import scan_contract
from risk_assessment import assess_risk
import traceback
import json
import io
import logging

# Log to both console AND a file called requests.log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.FileHandler("requests.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

app = FastAPI(title="Legal Contract Generator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ContractRequest(BaseModel):
    description: str


# ── Debug middleware: logs every incoming request ──────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    body = await request.body()
    log.info("========== INCOMING REQUEST ==========")
    log.info(f"METHOD : {request.method}")
    log.info(f"URL    : {request.url}")
    log.info(f"BODY   : {body.decode('utf-8', errors='replace')}")
    response = await call_next(request)
    log.info(f"RESPONSE STATUS: {response.status_code}")
    log.info("======================================")
    return response
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/")
def root():
    return {"message": "Legal Contract Generator API is running. POST to /generate"}


@app.post("/generate")
def generate(request: ContractRequest):
    log.info(f"[generate] description = {request.description!r}")
    if not request.description.strip():
        raise HTTPException(status_code=400, detail="description cannot be empty")
    try:
        # generate_contract is now a generator — stream chunks to the client
        def stream():
            for chunk in generate_contract(request.description):
                yield chunk

        return StreamingResponse(stream(), media_type="text/plain; charset=utf-8")
    except Exception as e:
        log.error(f"[ERROR] {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scan")
async def scan_contract_endpoint(file: UploadFile = File(...)):
    """Upload a contract (PDF or TXT) → extract clauses via CUAD → return structured JSON."""
    log.info(f"[scan] Received file: {file.filename}")

    # ── 1. Read uploaded file ──────────────────────────────────────────────────
    raw_bytes = await file.read()
    filename = (file.filename or "").lower()

    if filename.endswith(".pdf"):
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(raw_bytes))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            log.error(f"[scan] PDF parse error: {e}")
            raise HTTPException(status_code=400, detail=f"Could not parse PDF: {e}")
    elif filename.endswith(".txt"):
        text = raw_bytes.decode("utf-8", errors="replace")
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a .pdf or .txt file."
        )

    if not text.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    log.info(f"[scan] Extracted {len(text)} chars from {file.filename}")

    # ── 2. CUAD clause extraction ──────────────────────────────────────────────
    try:
        extracted = scan_contract(text)
    except Exception as e:
        log.error(f"[scan] CUAD extraction error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Clause extraction failed: {e}")

    log.info(f"[scan] Extracted {sum(1 for v in extracted.values() if v['found'])} clauses")

    # ── 3. LLM risk assessment (structured JSON) ──────────────────────────────
    try:
        risk_report = assess_risk(extracted)
    except Exception as e:
        log.error(f"[scan] Risk assessment error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {e}")

    log.info(f"[scan] Risk assessment complete — overall: {risk_report.get('overallRisk', '?')}")

    return JSONResponse(content={"clauses": extracted, "risk": risk_report})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
