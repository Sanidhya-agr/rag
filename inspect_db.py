from retrieval import collection

# Get all chunks (limit to 10 for inspection)
results = collection.get(limit=10)

for i, (doc, meta, idx) in enumerate(zip(results['documents'], results['metadatas'], results['ids'])):
    print(f"\n--- Chunk {i} ---")
    print(f"ID: {idx}")
    print(f"Metadata: {meta}")
    print(f"Preview: {doc[:1500]}...")