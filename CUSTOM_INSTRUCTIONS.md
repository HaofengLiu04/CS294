The agent supports **two modes**:

### 1. Autonomous Mode (Default)
Agent decides everything on its own based on market data.

```python
# No custom instruction - fully autonomous
result = agent.run_cycle()
```

### 2. Guided Mode (With Custom Instructions)
You provide specific instructions/prompts to guide the AI's decision.

```python
# With custom instruction - you guide the AI
result = agent.run_cycle(
    custom_instruction="Only trade Bitcoin. Use maximum 3x leverage."
)
```

---

## How It Works

When you provide a custom instruction, it gets added to the prompt like this:

### Without Custom Instruction:
```
CYCLE #5

ACCOUNT STATUS:
  Total Equity: $1,250.50
  Available: $950.00

MARKET DATA:
  - BTCUSDT: $42,350 (24h: +2.5%)
  - ETHUSDT: $2,235 (24h: -0.8%)

What is your trading decision?
```

### With Custom Instruction:
```
CYCLE #5

ACCOUNT STATUS:
  Total Equity: $1,250.50
  Available: $950.00

MARKET DATA:
  - BTCUSDT: $42,350 (24h: +2.5%)
  - ETHUSDT: $2,235 (24h: -0.8%)

CUSTOM INSTRUCTION FROM USER:
Only trade Bitcoin. Use maximum 3x leverage.

Please follow this instruction while making your trading decision.

What is your trading decision?
```

The AI then makes its decision **following your instruction**.

---

## Quick Examples

### Example 1: Focus on Specific Coin
```python
result = agent.run_cycle(
    symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
    custom_instruction="Only consider trading Bitcoin (BTCUSDT). Ignore other coins."
)
```

### Example 2: Close All Positions
```python
result = agent.run_cycle(
    custom_instruction="Close all open positions immediately. Do not open new trades."
)
```

### Example 3: Conservative Trading
```python
result = agent.run_cycle(
    custom_instruction="""
    Be extremely conservative:
    - Never use more than 2x leverage
    - Only trade if confidence > 80%
    - Position size max 1% of account
    """
)
```

### Example 4: Specific Strategy
```python
result = agent.run_cycle(
    symbols=["BTCUSDT"],
    custom_instruction="""
    Strategy: Buy the dip
    - Only open long if BTC is down >3% in 24h
    - Use 3x leverage
    - Position size: $200
    """
)
```

### Example 5: Risk Management
```python
result = agent.run_cycle(
    custom_instruction="Maximum 5% of account per trade. Always use stop losses."
)
```

### Example 6: Time-Based
```python
result = agent.run_cycle(
    custom_instruction="It's Friday evening - close all positions before the weekend."
)
```

---

## Full Code Example

```python
from white_agent.trading_agent import RealWorldTradingAgent
import os

# Initialize agent
agent = RealWorldTradingAgent(
    exchange="binance",
    api_key=os.getenv("BINANCE_API_KEY"),
    api_secret=os.getenv("BINANCE_API_SECRET"),
    testnet=True
)

# Option 1: Autonomous (no instruction)
result = agent.run_cycle()

# Option 2: With your custom instruction
result = agent.run_cycle(
    symbols=["BTCUSDT", "ETHUSDT"],
    custom_instruction="Only buy BTC if it's down more than 5% today."
)

# Check the result
print(f"AI Decision: {result['decision']['action']}")
print(f"AI Reasoning: {result['decision']['reasoning']}")
```

---

## Types of Instructions You Can Give

### Trading Restrictions
- "Only trade Bitcoin"
- "Do not open new positions"
- "Maximum 2 positions at once"
- "Never short, only long positions"

### Risk Management
- "Maximum 3x leverage"
- "Position size: 2% of account"
- "Always use stop loss at 2%"
- "Never risk more than $100 per trade"

### Strategy Specific
- "Only buy when RSI < 30"
- "Trend following: only trade with 4h trend"
- "DCA: buy $100 BTC every cycle"
- "Scalping: 1% take profit, 0.5% stop loss"

### Time-Based
- "It's the weekend, no trading"
- "End of month, take profits"
- "Close positions before major news"
- "Only trade during US market hours"

### Account Management
- "If down 10%, stop trading"
- "Take profits at +5%"
- "After 3 losses, reduce position size"
- "If win rate < 40%, hold only"

### Market Conditions
- "High volatility: reduce size by 50%"
- "Choppy market: stay in cash"
- "Bear market: prefer shorts"
- "During trending markets, use trailing stops"

---

## Comparison

| Mode | Who Decides | Flexibility | Use Case |
|------|-------------|-------------|----------|
| **Autonomous** | AI decides everything | High (AI adapts) | Continuous trading, backtesting |
| **Guided** | You guide AI | Custom control | Specific scenarios, testing strategies |

---

## Run the Demo

```bash
python demo_custom_instructions.py
```

This shows:
1. How to use custom instructions
2. Different types of instructions
3. How the AI responds to your guidance

---

## Key Points

**You CAN provide custom prompts** - Just use `custom_instruction` parameter
**AI still uses Chain of Thought** - Reasons through your instruction
**Flexible instructions** - Can be simple or complex
**Combines with market data** - Your instruction + real market state
**Optional parameter** - Leave empty for fully autonomous mode

---

## Summary

**Autonomous Mode:**
```python
agent.run_cycle()  # AI decides everything
```

**Guided Mode:**
```python
agent.run_cycle(
    custom_instruction="Your specific instruction here"
)
```

Both modes:
- Fetch real market data
- Use AI reasoning (Chain of Thought)
- Execute on real exchange
- Record decisions for analysis

The difference: **Guided mode follows YOUR instructions**
