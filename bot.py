import os
from dotenv import load_dotenv
from github import Github, Auth
import chromadb
from openai import OpenAI

load_dotenv()

# Connect to GitHub
g = Github(auth=Auth.Token(os.getenv("GITHUB_TOKEN")))

# Connect to ChromaDB
chroma_client = chromadb.PersistentClient(path="./incident_db")
collection = chroma_client.get_or_create_collection("incidents")

# Connect to Zeabur
ai_client = OpenAI(
    api_key=os.getenv("ZEABUR_API_KEY"),
    base_url=os.getenv("ZEABUR_BASE_URL")
)

def find_similar_incidents(diff_text, n_results=3):
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
    incidents = find_similar_incidents(diff_text)
    incidents_text = ""
    for i, incident in enumerate(incidents):
        meta = incident["metadata"]
        incidents_text += f"""
Incident {i+1} (Issue #{meta['issue_number']}):
Title: {meta['title']}
URL: {meta['url']}
Description: {incident['document'][:300]}
---
"""
    prompt = f"""You are a code review assistant that identifies production risks in PR diffs.

You have been given a PR diff and a set of similar past production incidents.

PR DIFF:
{diff_text}

SIMILAR PAST INCIDENTS:
{incidents_text}

Respond in exactly this format with no deviation:

RISK_LEVEL: [HIGH or MEDIUM or LOW]

WHY_RISKY:
[2-3 sentences explaining the specifi