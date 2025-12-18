# CS294 - AI Agents Course Projects

**Team A10**: Mingxi Tang, Yufeng Yan, Haofeng Liu, Meixin Ma

## Overview

This repository contains implementations for evaluating AI agents in blockchain and DeFi environments, developed for UC Berkeley's CS294 AI Agents course (Fall 2025).

In addition to the original DeFi evaluation framework, this repo now includes an **AgentBeats (A2A) trading competition scenario**:
- A **Green Agent** orchestrates a multi-round trading evaluation.
- Two **White Agents** (Conservative vs Aggressive) produce decisions + reasoning.
- A backtest engine executes trades on historical Binance candles (4h + 3m), computes performance metrics, and the green agent produces a final, reproducible evaluation artifact.

## Project Structure

### `defi_agent_eval/`
Advanced DeFi agent evaluation framework with real blockchain integration.

**Key Features:**
- LLM-powered white agents using OpenAI GPT-4o
- Real blockchain execution via Anvil (local Ethereum testnet)
- ERC20 token operations with actual on-chain transactions
- Natural language instruction processing
- Comprehensive test scenarios and evaluation metrics

**Quick Start:**
```bash
cd defi_agent_eval
# See defi_agent_eval/README.md for setup instructions
```

### `agentbeats-tutorial/` (AgentBeats / A2A runner + scenarios)
This folder is a lightweight AgentBeats tutorial runner (A2A-based). We added a **trading** scenario that wires the AgentBeats green/white servers to the `defi_agent_eval` trading evaluator.

Key files:
- `agentbeats-tutorial/scenarios/trading/scenario.toml`: scenario configuration (agents + ports + evaluator config)
- `agentbeats-tutorial/scenarios/trading/trading_green.py`: A2A green agent wrapper around `TradingEvaluator`
- `agentbeats-tutorial/scenarios/trading/trading_white.py`: A2A white agent that calls DeepSeek to produce structured JSON decisions (with reasoning)
- `defi_agent_eval/green_agent/trading/trading_evaluator.py`: backtest engine + scoring (normalized metrics + 70/30 weighting)

## Trading Scenario: Core Logic (What It Means)

### Roles
- **Green Agent**: orchestrator + evaluator. It builds market prompts, calls each white agent, executes trades in isolated accounts, computes metrics, and emits artifacts.
- **White Agent**: participant. It reads the market prompt and returns a JSON decision with:
  - `summary`
  - `reasoning` (required)
  - `actions[]` (e.g., `open_long`, `close_long`, etc.)
  - `position_size_usd` (notional, includes leverage)

### Execution & Backtest
- Market data: Binance public klines (4h decision cadence + 3m intraday window for timing).
- Each white agent has its own simulated account (cash, positions, fees, slippage, liquidation checks).
- The evaluator converts `position_size_usd` → quantity and enforces balance-aware sizing.

### Scoring
- **Quantitative performance** (normalized across agents): return, Sharpe, drawdown, win-rate, profit factor, CAGR, volatility (inverted where “lower is better”).
- **Reasoning score**: green agent LLM-judge scores white agents using all-round reasoning logs + execution summary.
- Final: \( total\_score = 0.7 \times normalized\_trading\_score + 0.3 \times reasoning\_score \)

## How to Run (AgentBeats one-command)

Prereqs:
- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv)
- A DeepSeek API key in `agentbeats-tutorial/.env` (do **not** commit keys)

Install (one-time):
```bash
cd agentbeats-tutorial
uv pip install -e .
```

Run the trading scenario:
```bash
cd agentbeats-tutorial
uv run agentbeats-run scenarios/trading/scenario.toml
```

Notes:
- If you see “missing uvicorn”, you are running the wrong Python. Always run through `uv run ...` (or `./.venv/bin/python ...`).
- The runner is **one-shot**: it starts agents, runs the assessment, emits artifacts, then shuts down.
- If you want fewer cycles, set `total_decision_cycles` in `scenarios/trading/scenario.toml`.

## Common Debug Tips

- **Progress visibility**: the green agent streams cycle/agent-stage updates during the run.
- **SSE noise**: if you see SSE shutdown warnings, you can use polling transport:
```bash
export A2A_CLIENT_TRANSPORT=polling
uv run agentbeats-run scenarios/trading/scenario.toml
```
- **Cache**: decisions can be cached in `cache/` (ignored by git). Delete cache files to force fresh calls.

## Project Goals

**Primary Task**: Evaluate AI agents operating in DeFi environments

**Evaluation Dimensions:**
- Correctness: Goal achievement and parameter validation
- Safety: Risk detection and mitigation strategies
- Efficiency: Gas optimization and routing analysis

**Safety Classifications**: SAFE | MODERATE_RISK | HIGH_RISK | DANGEROUS

## Repository Information

**Course**: CS294 - AI Agents  
**Institution**: UC Berkeley  
**Semester**: Fall 2025

## Documentation

Detailed documentation is available in each project directory:
- `green_agent_demo/README.md` - Demo implementation guide
- `defi_agent_eval/README.md` - Advanced framework documentation
