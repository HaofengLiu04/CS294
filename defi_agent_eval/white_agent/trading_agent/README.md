# Real-World Trading Agent

AI-powered cryptocurrency trading agent that connects to live exchanges.

## Features

- **Real Exchange Integration**: Connects to Binance, Hyperliquid, and other exchanges
- **Live Market Data**: Fetches real-time prices and market data from the internet
- **AI Decision Making**: Uses LLM (GPT-4, DeepSeek, etc.) for autonomous trading decisions
- **Risk Management**: Built-in position sizing and risk controls
- **Testnet Support**: Safe testing environment before live trading

## Supported Exchanges

### Centralized Exchanges (CEX)
- **Binance Futures**: API Key + Secret authentication
  - Testnet: https://testnet.binancefuture.com
  - Mainnet: https://fapi.binance.com

### Decentralized Exchanges (DEX)
- **Hyperliquid**: Private Key authentication (on-chain)
  - Testnet: https://api.hyperliquid-testnet.xyz
  - Mainnet: https://api.hyperliquid.xyz

## Quick Start

```python
from white_agent.trading_agent import RealWorldTradingAgent
import os

# Initialize agent (ALWAYS USE TESTNET FIRST!)
agent = RealWorldTradingAgent(
    exchange="hyperliquid",
    private_key=os.getenv("HYPERLIQUID_PRIVATE_KEY"),
    wallet_address=os.getenv("HYPERLIQUID_WALLET_ADDRESS"),
    testnet=True,  # IMPORTANT: Start with testnet!
    llm_model="gpt-4o",
    name="My Trading Agent"
)

# Run one trading cycle
result = agent.run_cycle(symbols=["BTC", "ETH"])

# Check AI decision
print(f"Decision: {result['decision']['action']}")
print(f"Reasoning: {result['decision']['reasoning']}")
```

## Architecture

```
trading_agent/
├── __init__.py                    # Module exports
├── agent.py                       # Main RealWorldTradingAgent class
├── setup_hyperliquid.py          # Hyperliquid setup & connection test
├── test_binance_vpn.py           # Test Binance API access (with VPN)
├── demo_custom_instructions.py   # Demo: Custom AI instructions
└── README.md                      # This file
```

## Running Setup Scripts

From the project root `/Users/louis/Desktop/CS294`:

```bash
# Test Binance API access (requires VPN in some regions)
python3 defi_agent_eval/white_agent/trading_agent/test_binance_vpn.py

# Setup and test Hyperliquid connection
python3 defi_agent_eval/white_agent/trading_agent/setup_hyperliquid.py

# Try custom instructions demo
python3 defi_agent_eval/white_agent/trading_agent/demo_custom_instructions.py
```

Or from within the `trading_agent` folder:

```bash
cd defi_agent_eval/white_agent/trading_agent

# Run setup
python3 setup_hyperliquid.py

# Test Binance
python3 test_binance_vpn.py

# Demo custom instructions
python3 demo_custom_instructions.py
```

## Security Warning

**This agent trades with REAL MONEY on REAL exchanges!**

**Best Practices:**
1. **Always test on testnet first**
2. **Never share your private keys or API keys**
3. **Use separate "agent wallet" for DEX trading (not your main funds)**
4. **Start with small amounts**
5. **Monitor closely during initial runs**

## Environment Variables

Create a `.env` file in the project root:

```bash
# For Binance
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_secret

# For Hyperliquid
HYPERLIQUID_PRIVATE_KEY=0x...
HYPERLIQUID_WALLET_ADDRESS=0x...

# LLM API
OPENAI_API_KEY=sk-...
# OR
DEEPSEEK_API_KEY=sk-...
```

## Custom Instructions

You can guide the AI's behavior with custom instructions:

```python
result = agent.run_cycle(
    symbols=["BTC", "ETH"],
    custom_instruction="Only trade BTC. Be conservative with position sizes."
)
```

## Trading Cycle

Each `run_cycle()` call:
1. Analyzes historical performance (last 20 cycles)
2. Fetches account balance from exchange
3. Gets current positions
4. Fetches real-time market data
5. AI makes decision with Chain of Thought
6. Executes decision on exchange
7. Records decision for future analysis

## AI Decision Format

The AI returns decisions in this format:

```json
{
  "action": "open_long" | "open_short" | "close_position" | "hold",
  "symbol": "BTCUSDT",
  "size_usd": 100.0,
  "leverage": 5,
  "reason": "BTC showing strong bullish momentum"
}
```

## License

Part of the CS294 DeFi Agent Evaluation Framework.
