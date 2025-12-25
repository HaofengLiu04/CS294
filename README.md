# CS294 - DeFi Agent Evaluation Framework

**Team A10**: Mingxi Tang, Yufeng Yan, Haofeng Liu, Meixin Ma

## Overview

This repository contains a multi-agent evaluation framework built for UC Berkeley's **CS294 AI Agents** (Fall 2025).

The main deliverable is an **AgentBeats (A2A) trading competition** where:
- A **Green Agent** orchestrates a backtest competition and produces evaluation artifacts.
- Two **White Agents** (Alice & Bob) generate **structured trading decisions + reasoning** using an LLM (OpenAI, DeepSeek, or Gemini).
- A backtest engine executes trades on historical market data, computes performance metrics, and the green agent produces a final score + winner.

The design and intent are documented in `green_white_logic.md` (English, long-form spec).

## What This Project Means (Core Logic)

### Green Agent vs White Agent
- **Green Agent (Evaluator/Orchestrator)**:
  - Loads market data and indicators.
  - Builds per-agent prompts containing market context + account state.
  - Calls each white agent via A2A.
  - Executes decisions in isolated backtest accounts (one account per agent).
  - Computes performance metrics and produces a final evaluation artifact.
- **White Agent (Participant/Trader)**:
  - Reads the market prompt.
  - Outputs **valid JSON** with `summary`, **non-empty `reasoning`**, and `actions[]`.
  - Uses `position_size_usd` (notional, includes leverage) so sizing is deterministic and balance-aware.

### Market Data + Decision Cadence
- **Decision cadence**: every **4 hours** (decision_interval = `4h`)
- **Intraday context**: **3-minute candles** over a short lookback window (intraday_interval = `3m`)
- Data source: Binance public klines (no auth required)

### Backtest Execution Model
- Each agent has its own virtual account (cash, positions, fees, slippage, liquidation checks).
- The evaluator converts `position_size_usd → quantity` using the current price and enforces balance-aware sizing.

### Scoring & Winner Selection
We combine:
- **Normalized quantitative performance (70%)** across agents:
  - return, Sharpe, drawdown (inverted), win-rate, profit factor, CAGR, volatility (inverted)
- **LLM reasoning score (30%)**:
  - Green agent judge consumes **all-round reasoning logs** + execution summary and produces `reasoning_score ∈ [0,1]`.

Final score:
\[
total\_score = 0.7 \times normalized\_trading\_score + 0.3 \times reasoning\_score
\]

## Repository Layout (Folders)

### `agentbeats-integration/`
Contains the AgentBeats runner and scenario configurations. This folder name is inherited from the base framework but contains our custom implementation.

You will run the trading competition via:
- `agentbeats-integration/scenarios/trading/scenario.toml`

Key scenario code:
- `agentbeats-integration/scenarios/trading/trading_green.py`: Green agent (wraps `TradingEvaluator`)
- `agentbeats-integration/scenarios/trading/trading_white_custom.py`: White agent (Custom wrapper supporting OpenAI/DeepSeek)

### `defi_agent_eval/`
Evaluation engines and primitives:
- **Trading evaluator** (the backtest competition engine):
  - `defi_agent_eval/green_agent/trading/trading_evaluator.py`
  - Market data + indicators: `defi_agent_eval/green_agent/trading/data.py`
  - Models: `defi_agent_eval/green_agent/trading/models.py`
  - Backtest account primitives: `defi_agent_eval/white_agent/trading_agent/backtest_account.py`
  - Backtest runner/events: `defi_agent_eval/white_agent/trading_agent/backtest_runner.py`
- **DeFi (on-chain) evaluation** framework (separate from trading; see `defi_agent_eval/README.md`).

### `cache/`
Local caches (ignored by git). Safe to delete if you want a clean run.

## Quick Start (Run Trading Competition)

Prerequisites:
- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv)
- A `.env` file in `agentbeats-integration/` containing your API key(s) (do **not** commit keys)

### 1. Setup Environment
Create a `.env` file in `agentbeats-integration/` with your API keys:

```bash
# For OpenAI models (Default)
OPENAI_API_KEY=sk-...
TRADING_JUDGE_MODEL=gpt-4o-mini

# OR for DeepSeek (via OpenAI-compatible endpoint)
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.deepseek.com
TRADING_JUDGE_MODEL=deepseek-chat
```

### 2. Install Dependencies
```bash
cd agentbeats-integration
uv sync
```

### 3. Run the Competition
Run the trading scenario (starts 3 servers → runs assessment → prints artifacts → shuts down):
```bash
uv run agentbeats-run scenarios/trading/scenario.toml
```

### Current Scenario Config
The current `agentbeats-integration/scenarios/trading/scenario.toml` is configured for a **12-cycle evaluation** (approx. 2 days of simulated trading):
- `start_date = "2024-12-01"`
- `end_date = "2024-12-03"`
- `decision_interval = "4h"`
- `total_decision_cycles = 12`

You can increase realism by:
- Removing `total_decision_cycles` (or setting it larger)
- Extending `start_date/end_date`

## Debug Tips
- **Use the correct environment**: run with `uv run ...` to avoid “missing uvicorn” and other venv issues.
- **Progress visibility**: green agent streams cycle + per-agent stage updates during runs.
- **SSE noise**: if you see streaming shutdown warnings, you can use polling:
```bash
export A2A_CLIENT_TRANSPORT=polling
uv run agentbeats-run scenarios/trading/scenario.toml
```

## References
- Project spec: `green_white_logic.md`

## Course Information
- **Course**: CS294 - AI Agents
- **Institution**: UC Berkeley
- **Semester**: Fall 2025