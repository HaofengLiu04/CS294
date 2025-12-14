# Backtest System - Complete Guide

## What You Got

A complete backtesting system for testing your trading agent on historical data before risking real money.

## Files Created

```
trading_agent/
├── backtest_account.py      # Simulated trading account
├── backtest_runner.py        # Backtest execution engine
├── demo_backtest.py          # Ready-to-run example
└── test_backtest_account.py  # Unit tests
```

## Quick Start

### 1. Run the Demo

```bash
cd /Users/xxxxx/Desktop/CS294/defi_agent_eval/white_agent
python -m trading_agent.demo_backtest
```

This will:
- Load last 7 days of BTC & ETH historical data
- Simulate your AI trading every 4 hours
- Show complete performance metrics
- Save results to a text file

### 2. Customize Your Backtest

```python
from trading_agent import RealWorldTradingAgent, BacktestRunner
from datetime import datetime, timedelta

# Initialize your agent
agent = RealWorldTradingAgent(
    exchange='hyperliquid',
    private_key='your_key',
    wallet_address='your_address',
    testnet=False,  # Need mainnet for historical data
    llm_model='deepseek-chat',
    llm_api_key='your_api_key'
)

# Set up backtest
runner = BacktestRunner(
    agent=agent,
    symbols=['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
    start_time=int((datetime.now() - timedelta(days=30)).timestamp()),
    end_time=int(datetime.now().timestamp()),
    initial_balance=1000.0,
    decision_interval='4h'
)

# Run it
metrics, equity_history, trades = runner.run(verbose=True)

# Analyze results
print(f"Return: {metrics.total_return_pct:.2f}%")
print(f"Sharpe: {metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: {metrics.max_drawdown_pct:.2f}%")
```

## How It Works

### Realistic Exchange Simulation

The backtest account mimics real exchange behavior:

**Fees:**
- Maker: 0.02% (2 bps)
- Taker: 0.05% (5 bps)

**Slippage:**
- 0.02% (2 bps) price movement on execution

**Leverage:**
- Up to 20x supported
- Automatic liquidation if price hits liquidation level

**Position Types:**
- Long positions (buy low, sell high)
- Short positions (sell high, buy low)
- Both with margin and leverage

### Historical Data

Uses REAL mainnet data:
```python
# Automatically loads from your exchange
klines = agent.get_klines(
    symbol='BTCUSDT',
    interval='4h',
    limit=1000
)
```

Each kline contains:
- `open`: Opening price
- `high`: Highest price in interval
- `close`: Closing price
- `low`: Lowest price in interval
- `volume`: Trading volume
- `timestamp`: Unix timestamp

### Backtest Execution Flow

```
1. Load Historical Data
   └─> Fetch klines for all symbols from exchange
   
2. Time-Step Simulation
   └─> For each decision interval:
       ├─> Get market data at current timestamp
       ├─> Check for liquidations
       ├─> Get AI decision from agent
       ├─> Execute trades with fees/slippage
       ├─> Update positions
       └─> Record equity point
       
3. Calculate Metrics
   └─> Total return, Sharpe ratio, max drawdown, etc.
```

### Performance Metrics

**Overall:**
- `total_return_pct`: Total profit/loss percentage
- `sharpe_ratio`: Risk-adjusted return (higher is better)
- `max_drawdown_pct`: Largest peak-to-trough decline
- `profit_factor`: Gross profit / gross loss
- `win_rate`: Percentage of winning trades

**Per Symbol:**
- Individual return for each trading pair
- Number of trades per symbol
- Win rate per symbol

**Trade Statistics:**
- Total number of trades
- Average win amount
- Average loss amount
- Largest win/loss

## Code Structure

### BacktestAccount (`backtest_account.py`)

Simulates a trading account with realistic exchange behavior.

**Key Methods:**

```python
account = BacktestAccount(
    initial_balance=1000.0,
    fee_rate=0.0005,      # 5 bps
    slippage_rate=0.0002  # 2 bps
)

# Open a position
account.open(
    symbol='BTCUSDT',
    side='long',
    quantity=0.1,
    leverage=5,
    price=50000.0,
    timestamp=1234567890
)

# Close a position (returns realized PnL)
pnl = account.close(
    symbol='BTCUSDT',
    side='long',
    quantity=0.1,
    price=51000.0
)

# Get total equity (including unrealized PnL)
equity = account.total_equity({
    'BTCUSDT': 51500.0,
    'ETHUSDT': 3200.0
})

# Check for liquidations
liq_note = account.check_liquidations({
    'BTCUSDT': 45000.0  # Price dropped
})
```

**How PnL Works:**

Long position:
```
Entry: Buy 0.1 BTC @ $50,000 with 5x leverage
Margin: $50,000 * 0.1 / 5 = $1,000
Fee: $50,000 * 0.1 * 0.0005 = $2.50

Exit: Sell 0.1 BTC @ $51,000
Profit: ($51,000 - $50,000) * 0.1 = $100
Fee: $51,000 * 0.1 * 0.0005 = $2.55

Realized PnL: $100 - $2.50 - $2.55 = $94.95
```

Short position:
```
Entry: Sell 0.1 BTC @ $50,000 with 5x leverage
Margin: $1,000
Fee: $2.50

Exit: Buy 0.1 BTC @ $49,000
Profit: ($50,000 - $49,000) * 0.1 = $100
Fee: $49,000 * 0.1 * 0.0005 = $2.45

Realized PnL: $100 - $2.50 - $2.45 = $95.05
```

### BacktestRunner (`backtest_runner.py`)

Orchestrates the backtest simulation.

**Key Methods:**

```python
runner = BacktestRunner(
    agent=agent,
    symbols=['BTCUSDT', 'ETHUSDT'],
    start_time=start_ts,
    end_time=end_ts,
    initial_balance=1000.0,
    decision_interval='4h'
)

# Run the backtest
metrics, equity_history, trades = runner.run(verbose=True)

# Metrics is a BacktestMetrics dataclass with all stats
print(f"Return: {metrics.total_return_pct:.2f}%")
print(f"Sharpe: {metrics.sharpe_ratio:.2f}")
print(f"Trades: {metrics.trades}")

# Equity history shows account value over time
for point in equity_history:
    print(f"{point.timestamp}: ${point.equity:.2f}")

# Trade events show every action taken
for trade in trades:
    print(f"{trade.symbol} {trade.action} @ ${trade.price:.2f}")
```

**Decision Integration:**

The runner calls your agent's `get_decision()` method:

```python
# Your agent must implement this
def get_decision(self, symbol: str) -> Dict[str, Any]:
    """
    Returns a decision dict like:
    {
        'action': 'open_long',  # or 'close_long', 'open_short', 'close_short', 'hold'
        'quantity': 0.1,
        'leverage': 5,
        'symbol': 'BTCUSDT'
    }
    """
    # Your AI logic here
    pass
```

### Demo Script (`demo_backtest.py`)

Ready-to-run example showing best practices.

**Features:**
- Loads 7 days of historical data
- Tests on BTC and ETH
- Displays comprehensive results
- Saves results to text file
- Shows recent trades
- Shows best/worst performing symbols

## Testing

Run the unit tests:

```bash
python -m trading_agent.test_backtest_account
```

Tests verify:
- Long position profitability
- Short position profitability  
- Liquidation price calculation
- Fee and slippage application
- PnL calculation accuracy

## Advanced Usage

### Multiple Symbols

```python
runner = BacktestRunner(
    agent=agent,
    symbols=['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT'],
    start_time=start_ts,
    end_time=end_ts,
    initial_balance=10000.0
)
```

### Different Time Intervals

Supported intervals: `'1m'`, `'5m'`, `'15m'`, `'30m'`, `'1h'`, `'4h'`, `'1d'`

```python
# Fast trading (more decisions)
runner = BacktestRunner(
    agent=agent,
    symbols=['BTCUSDT'],
    decision_interval='15m',  # Decide every 15 minutes
    ...
)

# Slow trading (fewer decisions)
runner = BacktestRunner(
    agent=agent,
    symbols=['BTCUSDT'],
    decision_interval='1d',  # Decide once per day
    ...
)
```

### Export Results

```python
metrics, equity_history, trades = runner.run()

# Save to JSON
import json

results = {
    'metrics': {
        'return': metrics.total_return_pct,
        'sharpe': metrics.sharpe_ratio,
        'max_drawdown': metrics.max_drawdown_pct,
        'trades': metrics.trades,
        'win_rate': metrics.win_rate
    },
    'equity': [
        {'timestamp': p.timestamp, 'equity': p.equity, 'cash': p.cash}
        for p in equity_history
    ],
    'trades': [
        {
            'timestamp': t.timestamp,
            'symbol': t.symbol,
            'action': t.action,
            'price': t.price,
            'quantity': t.quantity,
            'pnl': t.realized_pnl
        }
        for t in trades
    ]
}

with open('backtest_results.json', 'w') as f:
    json.dump(results, f, indent=2)
```

## Tips

### 1. Start Small

Test with short time periods first:
```python
# Test on 3 days instead of 30
start_time = int((datetime.now() - timedelta(days=3)).timestamp())
```

### 2. Use Verbose Mode

See what's happening in real-time:
```python
metrics, _, _ = runner.run(verbose=True)
```

### 3. Check for Liquidations

```python
if metrics.liquidated:
    print("Agent got liquidated! Reduce leverage or improve strategy.")
```

### 4. Compare Strategies

Run multiple backtests with different agent configurations:
```python
# Conservative agent
agent1 = RealWorldTradingAgent(...)
agent1.max_leverage = 3
metrics1, _, _ = BacktestRunner(agent=agent1, ...).run()

# Aggressive agent  
agent2 = RealWorldTradingAgent(...)
agent2.max_leverage = 10
metrics2, _, _ = BacktestRunner(agent=agent2, ...).run()

print(f"Conservative: {metrics1.total_return_pct:.2f}%")
print(f"Aggressive: {metrics2.total_return_pct:.2f}%")
```

### 5. Analyze Per-Symbol Performance

```python
for symbol, stats in metrics.symbol_stats.items():
    print(f"{symbol}:")
    print(f"  Return: {stats['return_pct']:.2f}%")
    print(f"  Trades: {stats['trades']}")
    print(f"  Win Rate: {stats['win_rate']:.1f}%")
```

## Troubleshooting

### "No historical data loaded"

**Problem:** Agent is using testnet
**Solution:** Set `testnet=False` when creating agent

```python
agent = RealWorldTradingAgent(
    exchange='hyperliquid',
    testnet=False,  # Need mainnet for historical data
    ...
)
```

### "Account liquidated immediately"

**Problem:** Leverage too high or bad first trade
**Solution:** Reduce leverage or improve decision logic

```python
# In your agent's get_decision():
return {
    'action': 'open_long',
    'quantity': 0.01,
    'leverage': 3  # Lower leverage = safer
}
```

### "Very low Sharpe ratio"

**Problem:** High volatility, inconsistent returns
**Solution:** 
- Reduce position sizes
- Add stop-loss logic
- Trade less frequently

### "Not enough trades"

**Problem:** Agent mostly returns 'hold'
**Solution:** Adjust decision logic to be more active

## What's Next?

1. **Run the demo** to see it in action
2. **Customize your agent's decision logic** to improve performance
3. **Test different strategies** by changing system prompts or parameters
4. **Compare results** across different market conditions
5. **Optimize** based on metrics (Sharpe, drawdown, win rate)

The backtest system is ready to use - just run `demo_backtest.py` to get started!
