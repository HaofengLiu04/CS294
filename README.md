# CS294 - AI Agents Course Projects

**Team A10**: Mingxi Tang, Yufeng Yan, Haofeng Liu, Meixin Ma

## Overview

This repository contains a multi-agent evaluation framework built for UC Berkeley's **CS294 AI Agents** (Fall 2025).

The main deliverable is an **AgentBeats (A2A) trading competition** where:
- A **Green Agent** orchestrates a backtest competition and produces evaluation artifacts.
- Two **White Agents** (currently: **Conservative** and **Aggressive**) generate **structured trading decisions + reasoning** using an LLM.
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

### `agentbeats-tutorial/`
AgentBeats local runner (A2A-based) + scenarios.

You will run the trading competition via:
- `agentbeats-tutorial/scenarios/trading/scenario.toml`

Key scenario code:
- `agentbeats-tutorial/scenarios/trading/trading_green.py`: Green agent (wraps `TradingEvaluator`)
- `agentbeats-tutorial/scenarios/trading/trading_white.py`: White agent (LLM-backed, returns JSON)

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

## Quick Start (Run Trading Competition via AgentBeats)

Prerequisites:
- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv)
- A `.env` file in `agentbeats-tutorial/` containing your API key(s) (do **not** commit keys)
  - **Required**: `DEEPSEEK_API_KEY` - Your DeepSeek API key for LLM-based agents
- **VPN Required**: If you're in the US, you need a VPN to access Binance data (Binance US does not allow access to Binance.com data)

One-time install (install everything in this workspace first):
```bash
cd .
uv pip install -r requirements.txt
```

Then install the AgentBeats runner package:
```bash
cd agentbeats-tutorial
uv pip install -e .
```

Run the trading scenario (starts 3 servers → runs assessment → prints artifacts → shuts down):
```bash
cd agentbeats-tutorial
uv run agentbeats-run scenarios/trading/scenario.toml
```

### Current Scenario Config (Fast Demo Defaults)
To make iteration fast, the current `agentbeats-tutorial/scenarios/trading/scenario.toml` is configured to run:
- **Only 3 cycles** (`total_decision_cycles = 3`)
- A short backtest window:
  - `start_date = "2025-12-10"`
  - `end_date   = "2025-12-14"`
  - `decision_interval = "4h"`

You can increase realism by:
- Removing `total_decision_cycles` (or setting it larger)
- Extending `start_date/end_date`
- Adding more participants back (Conservative/Balanced/Aggressive/Momentum/MeanReversion)

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