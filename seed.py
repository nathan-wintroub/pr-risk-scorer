import os
from dotenv import load_dotenv
from github import Github
import chromadb

load_dotenv()

# Connect to GitHub
g = Github(os.getenv("GITHUB_TOKEN"))

# Connect to ChromaDB
client = chromadb.PersistentClient(path="./incident_db")
collection = client.get_or_create_collection("incidents")

# Pull closed bug issues from Sentry (public repo, rich history)
repo = g.get_repo("getsentry/sentry")

print("Fetching closed issues...")

issues = repo.get_issues(state="closed", labels=["Bug"], sort="updated")

documents = []
metadatas = []
ids = []

for i, issue in enumerate(issues):
    if i >= 100:
        break
    if issue.body is None:
        continue

    text = f"Title: {issue.title}\n\nDescription: {issue.body[:500]}"
    documents.append(text)
    metadatas.append({
        "issue_number": issue.number,
        "title": issue.title,
        "url": issue.html_url
    })
    ids.append(f"issue_{issue.number}")

    if i % 10 == 0:
        print(f"  Loaded {i} issues...")

print(f"Storing {len(documents)} issues in ChromaDB...")
collection.add(documents=documents, metadatas=metadatas, ids=ids)
print("Done! Knowledge base seeded.")