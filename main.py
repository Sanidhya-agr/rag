from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from generation import generate_contract
import traceback
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


class ContractResponse(BaseModel):
    contract: str


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


@app.post("/generate", response_model=ContractResponse)
def generate(request: ContractRequest):
    log.info(f"[generate] description = {request.description!r}")
    if not request.description.strip():
        raise HTTPException(status_code=400, detail="description cannot be empty")
    try:
        result = generate_contract(request.description)
        return ContractResponse(contract=result)
    except Exception as e:
        log.error(f"[ERROR] {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
