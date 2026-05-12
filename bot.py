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

def main():
    # Get PR details from environment (GitHub Actions sets these)
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_number = int(os.getenv("PR_NUMBER", 0))
    
    if not repo_name or not pr_number:
        print("Not running in GitHub Actions context")
        return

    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    # Get the diff
    diff_text = ""
    for file in pr.get_files():
        diff_text += f"File: {file.filename}\n"
        if file.patch:
            diff_text += file.patch + "\n\n"
    
    if not diff_text:
        print("No diff found")
        return

    print(f"Analyzing PR #{pr_number}...")
    result = score_pr_risk(diff_text)
    
    # Post comment on the PR
    comment = f"""## 🤖 PR Risk Analysis

{result['analysis']}

---
**Similar Past Incidents:**
"""
    for incident in result["incidents"]:
        meta = incident["metadata"]
        comment += f"- Issue #{meta['issue_number']}: [{meta['title']}]({meta['url']})\n"

    pr.create_issue_comment(comment)
    print("Comment posted!")

if __name__ == "__main__":
    main()