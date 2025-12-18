# GitHub Push Guide (Local)

This repo contains **two major components**:
- `defi_agent_eval/`: trading + DeFi evaluation framework (backtest engine lives here)
- `agentbeats-tutorial/`: AgentBeats (A2A) scenario runner + trading green/white agents

This file explains how to push the whole repository to GitHub from your machine.

## 1) Safety check (do NOT commit secrets)

Before you push, ensure you are **not** committing any secrets:
- `.env` is ignored by `.gitignore` (good)
- `.venv/`, `__pycache__/`, `cache/` are ignored (good)

Double-check:
```bash
git status
git diff
```

## 2) Initialize git (if this folder is not yet a repo)

From the repo root (this folder):
```bash
cd "/Users/tangmingxi/Desktop/green agent/CS294"
git init
git add .
git commit -m "Initial commit: AgentBeats trading scenario + defi_agent_eval"
```

If you already have git history, skip `git init`.

## 3) Create a GitHub repository

On GitHub, create a new repo (e.g. `cs294-green-agent`).
Copy the SSH or HTTPS remote URL.

## 4) Add remote + push

```bash
git remote add origin <YOUR_GITHUB_REPO_URL>
git branch -M main
git push -u origin main
```

## 5) After pushing

Recommended:
- Add a short description + topics on GitHub
- Enable “Issues” (for bug tracking)
- Consider adding a GitHub Actions workflow later (lint/test/build)


