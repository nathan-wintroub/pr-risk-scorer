# PR Risk Scorer

A GitHub bot that automatically reviews pull requests using a knowledge 
base of real production incidents — not generic best-practice rules.

When a PR is opened, the bot:
1. Fetches the diff
2. Searches a vector database of past production bugs for similar patterns
3. Sends both to an AI model for reasoning
4. Posts a structured risk assessment directly on the PR

---

## Demo

**Real bug:** In May 2026, Sentry's Logs Dashboard started returning 500 
errors globally. The root cause was a Snuba query timeout.

**The fix that was proposed** (PR #115171) was a one-line change:
```python
- SENTRY_SNUBA_TIMEOUT = 30
+ SENTRY_SNUBA_TIMEOUT = 45
```

**What the bot said:**

> 🟡 Risk Level: MEDIUM
>
> Increasing the timeout may prevent some errors but could mask underlying 
> Snuba performance issues or lead to longer page load times. Monitor 
> Snuba query latency closely after this change.

That warning was generated automatically in under 2 seconds by matching 
the diff against 100 past Sentry production incidents.

---

## Why This Is Different

Most AI code review tools reason from static best practices — rules baked 
into the model at training time. This tool reasons from your actual 
production history.

The core insight: **a model trained on GitHub commits has no signal about 
which code patterns lead to production incidents.** This tool closes that 
loop by building a searchable knowledge base of real incidents and 
retrieving relevant ones at review time.

---

## How It Works
PR opened
↓
Fetch diff via GitHub API
↓
Embed diff → search ChromaDB incident knowledge base
↓
Retrieve top 3 similar past incidents
↓
Send diff + incidents to AI model
↓
Post structured risk comment on PR

---

## Stack

- **ChromaDB** — local vector database for semantic incident search
- **GitHub Actions** — triggers automatically on every PR
- **GitHub API** — fetches diffs, posts comments
- **Gemini 2.5 Flash** — reasons over diff + retrieved incidents
- **Python** — glue

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/nathan-wintroub/pr-risk-scorer.git
cd pr-risk-scorer
python3 -m venv venv
source venv/bin/activate
pip install chromadb openai PyGithub python-dotenv requests
```

### 2. Set environment variables
Create a `.env` file:
GITHUB_TOKEN=your_github_token
ZEABUR_API_KEY=your_ai_api_key
ZEABUR_BASE_URL=your_ai_base_url

### 3. Seed the knowledge base
```bash
python3 seed.py
```

### 4. Add secrets to GitHub Actions
In your repo settings → Secrets → Actions, add:
- `ZEABUR_API_KEY`
- `ZEABUR_BASE_URL`

### 5. Open a PR
The bot triggers automatically on every pull request.

---

## Results

Tested against real historical PRs from the Sentry codebase. The bot 
correctly identified timeout and integration risks that led to production 
incidents, citing specific past issues by number rather than generic warnings.

---

*Built in 2 days as a demonstration of retrieval-augmented code review —*
