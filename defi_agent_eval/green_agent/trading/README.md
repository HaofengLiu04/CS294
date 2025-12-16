# Trading Green Agent (Backtest Evaluator)

Implements the Green Agent described in `green_white_logic.md` using the
existing `white_agent.trading_agent` backtest primitives.

## Highlights
- Fetches Binance 4h + 3m klines (public HTTP, no API key) and computes EMA/MACD/RSI/ATR.
- Builds rich market prompts per agent (positions, candidates, intraday slices, disclosure intel).
- Executes structured decisions (`open_long/close_long/open_short/close_short/hold`) inside isolated `BacktestAccount`s.
- Supports disclosure rounds (`cycles 42/84/126` by default) and leaderboard snapshots.
- Produces simple performance metrics and scores (Sharpe-driven).

## Usage

```python
from defi_agent_eval.green_agent.trading import TradingEvaluator, TradingDecision, TradingAction

# Define how to talk to each White Agent (callable gets prompt, returns TradingDecision)
def dummy_agent(prompt: str) -> TradingDecision:
    return TradingDecision(summary="hold", reasoning="stub", actions=[])

agent_names = ["Conservative", "Balanced", "Aggressive", "Momentum", "MeanReversion"]
agent_clients = {name: dummy_agent for name in agent_names}

evaluator = TradingEvaluator(agent_names=agent_names, agent_clients=agent_clients)
results = evaluator.run_competition()

for name, perf in results.items():
    print(name, perf.total_return_pct, perf.sharpe_ratio, perf.total_score)
```

## Files
```
trading/
├── __init__.py
├── data.py               # Binance HTTP fetch + indicators
├── models.py             # Dataclasses for actions/decisions/disclosures
└── trading_evaluator.py  # Competition driver
```

## Notes
- Data download uses the public Binance REST endpoint; ensure network access.
- The evaluator is synchronous and lightweight; plug your own White Agent callables for real A2A.
- Default config matches the 4h/3m, 30-day, 180-cycle plan in the logic doc.

