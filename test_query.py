import chromadb

client = chromadb.PersistentClient(path="./incident_db")
collection = client.get_or_create_collection("incidents")

results = collection.query(
    query_texts=["memory leak causes timeout on high traffic"],
    n_results=3
)

for i, doc in enumerate(results["documents"][0]):
    meta = results["metadatas"][0][i]
    print(f"\n--- Match {i+1} ---")
    print(f"Issue #{meta['issue_number']}: {meta['title']}")
    print(f"URL: {meta['url']}")