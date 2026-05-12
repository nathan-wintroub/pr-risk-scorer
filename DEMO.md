# Demo: Catching a Real Production Incident

## The Bug
On May 9, 2026, Sentry's Logs Dashboard started returning 500 errors 
for all users globally. Engineers had to manually diagnose the issue 
across services before identifying a Snuba query timeout as the cause.
See: [Issue #113931](https://github.com/getsentry/sentry/issues/113931)

## The Fix That Was Proposed
A developer submitted PR #115171 — a one-line change bumping the Snuba 
connection timeout from 30 to 45 seconds. It looks completely harmless.

## What My Tool Said
When I ran this PR through the risk scorer, it flagged it as **MEDIUM risk** 
and produced this warning:

> "While increasing the timeout might prevent some errors, it could also 
> mask underlying Snuba performance issues or lead to longer page load 
> times for users. Monitor Snuba query latency and success rates closely 
> after this change."

## Why This Matters
This is exactly the insight a senior engineer would give — and it was 
generated automatically in under 2 seconds by searching a knowledge base 
of 100 past production incidents and reasoning over them with an LLM.

The tool didn't just say "this looks risky." It explained *why*, cited 
specific past incidents, and gave an actionable recommendation. That's 
the difference between a linter and a production-aware reviewer.

## How It Works
1. When a PR is opened, a GitHub Actions workflow triggers automatically
2. The diff is embedded and searched against a vector database of past incidents
3. The most similar incidents are retrieved and passed to an LLM alongside the diff
4. The LLM reasons over both and posts a structured risk assessment as a PR comment