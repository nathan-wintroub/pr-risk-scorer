import os
from dotenv import load_dotenv
import chromadb
from openai import OpenAI

load_dotenv()

# Connect to ChromaDB
chroma_client = chromadb.PersistentClient(path="./incident_db")
collection = chroma_client.get_or_create_collection("incidents")

# Connect to Zeabur
ai_client = OpenAI(
    api_key=os.getenv("ZEABUR_API_KEY"),
    base_url=os.getenv("ZEABUR_BASE_URL")
)

def find_similar_incidents(diff_text, n_results=3):
    """Given a PR diff, find the most similar past incidents."""
    results = collection.query(
        query_texts=[diff_text],
        n_results=n_results
    )
    
    incidents = []
    for i in range(len(results["documents"][0])):
        incidents.append({
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })
    
    return incidents

def score_pr_risk(diff_text):
    """Use Claude to score the risk of a PR diff based on similar incidents."""
    
    # First find similar incidents
    incidents = find_similar_incidents(diff_text)
    
    # Format incidents for the prompt
    incidents_text = ""
    for i, incident in enumerate(incidents):
        meta = incident["metadata"]
        incidents_text += f"""
Incident {i+1} (Issue #{meta['issue_number']}):
Title: {meta['title']}
URL: {meta['url']}
Similarity distance: {incident['distance']:.3f}
Description: {incident['document'][:300]}
---
"""

    prompt = f"""You are a code review assistant that identifies production risks in PR diffs.

You have been given a PR diff and a set of similar past production incidents.

PR DIFF:
{diff_text}

SIMILAR PAST INCIDENTS:
{incidents_text}

Based on the diff and the similar incidents, provide:
1. A risk score: LOW, MEDIUM, or HIGH
2. Which past incident this most resembles and why
3. A specific recommendation to make this code safer

Be concise. Cite incidents by their issue number."""

    response = ai_client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )
    
    return {
        "analysis": response.choices[0].message.content,
        "incidents": incidents
    }


# Test it with a fake diff
test_diff = """
diff --git a/payments/processor.py b/payments/processor.py
@@ -52,6 +52,8 @@ class PaymentProcessor:
+    def process_payment(self, order_id: str):
+        response = requests.get(PAYMENT_API_URL)
+        return response.json()
"""

print("Analyzing PR diff...\n")
result = score_pr_risk(test_diff)
print("=== RISK ANALYSIS ===")
print(result["analysis"])
print("\n=== SIMILAR INCIDENTS ===")
for incident in result["incidents"]:
    meta = incident["metadata"]
    print(f"Issue #{meta['issue_number']}: {meta['title']}")
    print(f"URL: {meta['url']}\n")