import os
import json
import chromadb
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI

# 1. Setup Embedding Function
# Ensure you have 'pip install openai' and 'OPENAI_API_KEY' set in your environment
openai_client = OpenAI()
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-ada-002"
)

# 2. Initialize ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="legal_docs",
    embedding_function=openai_ef,
    metadata={"hnsw:space": "cosine"}
)

# 3. Configure Text Splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", ".", " ", ""]
)

def index_documents(folder_path="data"):
    """Reads .txt files, chunks them, and upserts them into ChromaDB."""
    if not os.path.exists(folder_path):
        print(f"Directory '{folder_path}' not found.")
        return

    doc_count = 0
    exclude_files = {"mutual-nda.txt"}
    for filename in os.listdir(folder_path):
        if not filename.endswith(".txt"):
            continue
        if filename.lower() in exclude_files:
            print(f"Skipped {filename} (excluded).")
            continue

        filepath = os.path.join(folder_path, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        # Metadata tagging: 'law' keyword takes priority over template keywords
        file_lower = filename.lower()
        law_keys      = ["law", "regulation", "statute", "act", "code", "rule"]
        template_keys = ["nda", "contractor", "saas", "partnership", "services", "agreement"]
        if any(k in file_lower for k in law_keys):
            source = "law"
        elif any(k in file_lower for k in template_keys):
            source = "template"
        else:
            source = "law"  # default to law if unclear

        # Split text into manageable chunks
        chunks = text_splitter.split_text(text)

        # Prepare data for batch insertion
        documents = []
        metadatas = []
        ids = []

        for i, chunk in enumerate(chunks):
            uid = f"{source}_{filename}_{i}"
            documents.append(chunk)
            metadatas.append({"source": source, "file": filename, "chunk_index": i})
            ids.append(uid)

        # Use upsert to avoid "ID already exists" errors on re-runs
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        doc_count += len(chunks)
        print(f"Indexed {filename}: {len(chunks)} chunks.")

    print(f"--- Finished. Total chunks in session: {doc_count} ---")

def retrieve(query, n_results=3, where=None):
    """Queries the collection and returns documents, metadatas, distances."""
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"]
    )
    
    # Extracting results for cleaner access
    docs = results.get('documents', [[]])[0]
    metas = results.get('metadatas', [[]])[0]
    distances = results.get('distances', [[]])[0]
    
    return docs, metas, distances

def guess_filter(query):
    q = query.lower()
    if "nda" in q or "nondisclosure" in q or "confidential" in q:
        return {"source": "template"}
    return None

def classify_intent_llm(query, model="gpt-4o-mini"):
    intents = ["nda_template", "contractor_termination", "general_legal_question", "other"]
    
    # OpenAI Tool Definition
    tools = [{
        "type": "function",
        "function": {
            "name": "classify_intent",
            "description": "Classify the user query into one of the supported intents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "intent": {"type": "string", "enum": intents},
                    "confidence": {"type": "number"}
                },
                "required": ["intent", "confidence"],
                "additionalProperties": False
            },
            "strict": True
        }
    }]

    # Correct OpenAI SDK Call
    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Classify the user query into a single intent."},
            {"role": "user", "content": query}
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "classify_intent"}}
    )

    # Parsing the response
    tool_call = response.choices[0].message.tool_calls[0]
    data = json.loads(tool_call.function.arguments)
    return data["intent"], float(data["confidence"])

def route_filter_from_intent(intent):
    if intent == "nda_template":
        return {"source": "template"}
    return None

# --- Example Usage ---
if __name__ == "__main__":
    # 1. Index your data (ensure the 'data' folder exists with .txt files)
    # index_documents("data")

    # 2. Run test queries
    queries = [
        "I need a nondisclosure agreement for a business partnership"
    ]
    use_intent_classifier = True
    for q in queries:
        if use_intent_classifier:
            intent, conf = classify_intent_llm(q)
            where = route_filter_from_intent(intent)
            print(f"\nQuery: {q} (intent={intent}, confidence={conf:.2f}, filter={where})")
        else:
            where = guess_filter(q)
            print(f"\nQuery: {q} (filter={where})")

        docs, metas, dists = retrieve(q, n_results=2, where=where)
        for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists), 1):
            source = meta.get("source", "unknown") if isinstance(meta, dict) else "unknown"
            file = meta.get("file", "unknown") if isinstance(meta, dict) else "unknown"

            print(f"Result {i} (distance={dist:.4f}) ({source} - {file}):")
            print(f"{doc[:200]}...")
