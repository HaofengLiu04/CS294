"""
Quick sanity test for TradingEvaluator:
- Uses REAL white agents with DeepSeek LLM.
- Fetches Binance 4h/3m data (public).
- Runs the competition loop.
- Prints agent decisions, reasoning, and performance.

Usage:
  cd /Users/tangmingxi/Desktop/green agent/CS294
  export DEEPSEEK_API_KEY=sk-98e7ecb7b05e4013860b41991cba53db
  export DEEPSEEK_API_BASE="https://api.deepseek.com"
  PYTHONPATH=. python3 defi_agent_eval/green_agent/trading/test_trading_evaluator.py
"""

from __future__ import annotations

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables from .env file
CUR_DIR = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(CUR_DIR, "..", "..", ".."))
DEFI_ROOT = os.path.abspath(os.path.join(CUR_DIR, "..", ".."))

# Load .env from project root or agentbeats-tutorial
env_paths = [
    os.path.join(ROOT, ".env"),
    os.path.join(ROOT, "agentbeats-tutorial", ".env"),
]
for env_path in env_paths:
    if os.path.exists(env_path):
        try:
            print(f"Loading environment from: {env_path}")
            load_dotenv(env_path)
            break
        except PermissionError:
            print(f"⚠️  Cannot read {env_path}, using existing environment variables")
            continue

# Ensure imports work when run as a script
for p in (ROOT, DEFI_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from defi_agent_eval.green_agent.trading.trading_evaluator import TradingEvaluator, TradingDecision
from defi_agent_eval.green_agent.trading.models import TradingAction
from litellm import completion
import pandas as pd


# Strategy profiles from green_white_logic.md
STRATEGY_PROFILES = {
    "Conservative": "Avoid high-risk trades. Prefer established coins, low leverage (1-2x). Exit quickly if stop-loss is hit.",
    "Balanced": "Balance risk and reward. Use moderate leverage (2-4x). Diversify across a few assets.",
    "Aggressive": "Seek high returns. Use higher leverage (5-10x). Take calculated risks on volatile assets.",
    "Momentum": "Follow strong trends. Buy breakouts, ride the momentum. Use trailing stops.",
    "MeanReversion": "Look for overbought/oversold conditions. Buy dips, sell rallies. Expect price to revert to mean.",
}


def make_real_white_agent(name: str, role: str):
    """
    Creates a real white agent that uses DeepSeek LLM to generate trading decisions.
    """
    strategy_instruction = STRATEGY_PROFILES.get(role, "")
    
    # Decision Process from green_white_logic.md
    decision_process = """
# Decision Process (for White Agents)

1. **Read Market Context**: Parse the prompt (current price, indicators, open positions, etc.).
2. **Assess Trend & Momentum**: Is the market bullish, bearish, or ranging?
3. **Evaluate Risk**: Check your current exposure, leverage, and account balance.
4. **Decide Action**:
   - `open_long` / `open_short`: If you see a strong signal and have capacity.
   - `close_long` / `close_short`: If position is profitable or stop-loss triggered.
   - `hold`: If no clear signal or waiting for better entry.
5. **Set Leverage & Quantity**: Align with your strategy profile (Conservative=low, Aggressive=high).
6. **Provide Reasoning**: Explain your decision with reference to market data and indicators.
"""
    
    system_prompt = f"""You are a professional cryptocurrency trading agent named "{name}".

Your Trading Strategy: {strategy_instruction}

{decision_process}

Always respond with valid JSON in this format:
{{
  "summary": "Brief one-line summary of your decision",
  "reasoning": "Detailed explanation of your analysis and decision (minimum 50 characters)",
  "actions": [
    {{
      "symbol": "BTCUSDT",
      "action": "open_long|open_short|close_long|close_short|hold",
      "leverage": 1-10,
      "position_size_usd": notional value in USD (includes leverage)
    }}
  ]
}}

IMPORTANT - Position Sizing:
- `position_size_usd` is the NOTIONAL VALUE (includes leverage), NOT margin requirement
- Calculation: Available Margin × Leverage = position_size_usd
- Example: Available Cash = $500, Leverage = 5x
  • Available Margin = $500 × 0.88 = $440 (reserve 12% for fees)
  • position_size_usd = $440 × 5 = $2,200 ← Use this value
  • Actual margin used = $440, remaining $60 for fees

With account balance $10,000:
- Max with 8x leverage: $10,000 × 0.88 × 8 = $70,400
- Conservative (50% capital): ~$35,000
- Aggressive (80% capital): ~$56,000
"""
    
    def handler(prompt: str) -> TradingDecision:
        """Calls DeepSeek LLM to generate a trading decision."""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
        
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY not set in environment")
        
        print(f"\n{'='*60}")
        print(f"[{name}] Generating decision...")
        print(f"{'='*60}")
        print(f"\n[{name}] PROMPT PREVIEW (first 500 chars):")
        print(prompt[:500])
        print("...")
        
        try:
            response = completion(
                model="deepseek/deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                api_key=api_key,
                api_base=api_base,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            decision_dict = json.loads(content)
            
            # Print the decision for visibility
            print(f"\n[{name}] DECISION:")
            print(f"  Summary: {decision_dict.get('summary', 'N/A')}")
            print(f"  Reasoning: {decision_dict.get('reasoning', 'N/A')[:200]}...")
            print(f"  Actions: {decision_dict.get('actions', [])}")
            
            # Convert to TradingDecision
            actions = [
                TradingAction(
                    symbol=a["symbol"],
                    action=a["action"],
                    leverage=a.get("leverage", 1),
                    quantity=a.get("quantity", 0)
                )
                for a in decision_dict.get("actions", [])
            ]
            
            return TradingDecision(
                summary=decision_dict.get("summary", ""),
                reasoning=decision_dict.get("reasoning", ""),
                actions=actions
            )
            
        except Exception as e:
            print(f"[{name}] ERROR: {e}")
            raise
    
    return handler


def checkpoint_market_data(evaluator):
    """Check if market data is fetched correctly and print indicators."""
    print("\n" + "="*80)
    print("CHECKPOINT: Verifying Market Data and Indicators")
    print("="*80)
    
    # Check if data_fetcher is initialized
    if not hasattr(evaluator, 'data_fetcher') or evaluator.data_fetcher is None:
        print("❌ ERROR: data_fetcher not initialized!")
        return False
    
    print(f"✅ DataFetcher initialized")
    print(f"   Start: {evaluator.config['start_date']}")
    print(f"   End: {evaluator.config['end_date']}")
    print(f"   Decision Interval: {evaluator.config['decision_interval']}")
    print(f"   Symbols: {evaluator.config['symbols']}")
    
    # Load data using the evaluator's method
    print(f"\n📊 Loading market data from Binance...")
    try:
        evaluator.load_and_prepare_data()
        print(f"✅ Market data loaded successfully!")
        print(f"   Symbols fetched: {len(evaluator.data_4h)} symbols (4h data)")
        print(f"   Symbols: {list(evaluator.data_4h.keys())[:3]}...")
        
        # Check for a specific symbol's data
        symbol = "BTCUSDT"
        if symbol in evaluator.data_4h:
            df_4h = evaluator.data_4h[symbol]
            print(f"\n📈 Data for {symbol}:")
            print(f"   Shape: {df_4h.shape}")
            print(f"   Date range: {df_4h['open_time'].min()} to {df_4h['open_time'].max()}")
            print(f"   Columns: {list(df_4h.columns)[:10]}")
            
            # Show latest indicators
            latest = df_4h.iloc[-1]
            print(f"\n   Latest values at {latest['open_time']}:")
            print(f"   Close Price: ${latest['close']:.2f}")
            
            if 'ema20' in df_4h.columns:
                ema20 = latest['ema20']
                print(f"   EMA20: ${ema20:.2f}" if not pd.isna(ema20) else "   EMA20: N/A")
            
            if 'macd' in df_4h.columns:
                macd = latest['macd']
                macd_signal = latest.get('macd_signal', float('nan'))
                print(f"   MACD: {macd:.4f}" if not pd.isna(macd) else "   MACD: N/A")
                print(f"   MACD Signal: {macd_signal:.4f}" if not pd.isna(macd_signal) else "   MACD Signal: N/A")
            
            if 'rsi14' in df_4h.columns:
                rsi = latest['rsi14']
                print(f"   RSI14: {rsi:.2f}" if not pd.isna(rsi) else "   RSI14: N/A")
            
            if 'atr' in df_4h.columns:
                atr = latest['atr']
                print(f"   ATR: ${atr:.2f}" if not pd.isna(atr) else "   ATR: N/A")
            
            # Show sample of recent data
            print(f"\n📋 Last 3 rows of {symbol} data:")
            cols_to_show = ['open_time', 'close', 'ema20', 'rsi14', 'macd']
            cols_available = [c for c in cols_to_show if c in df_4h.columns]
            if cols_available:
                print(df_4h[cols_available].tail(3).to_string())
        
    except Exception as e:
        print(f"❌ ERROR fetching 4h data: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test building a prompt
    print(f"\n📝 Testing prompt generation...")
    try:
        symbol = "BTCUSDT"
        if symbol in evaluator.data_4h:
            df_4h = evaluator.data_4h[symbol]
            # Use the 'open_time' column, not the index
            test_timestamp = df_4h.iloc[-1]['open_time']
            print(f"   Using timestamp: {test_timestamp} (type: {type(test_timestamp)})")
            
            # build_market_prompt signature: (agent_name, cycle_idx, timestamp)
            # Use one of the actual agent names that has an account
            prompt = evaluator.build_market_prompt(
                agent_name="Conservative",
                cycle_idx=1,
                timestamp=test_timestamp
            )
            print(f"✅ Prompt generated successfully!")
            print(f"   Length: {len(prompt)} characters")
            print(f"\n   Preview (first 1000 chars):")
            print(prompt[:1000])
            print("   ...")
        else:
            print(f"⚠️  Could not test prompt generation: {symbol} data not loaded")
    except Exception as e:
        print(f"❌ ERROR generating prompt: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*80)
    print("✅ CHECKPOINT PASSED: Market data looks good!")
    print("="*80 + "\n")
    return True


def main():
    # Only two agents for simpler competition
    agent_names = ["Conservative", "Aggressive"]
    agent_clients = {name: make_real_white_agent(name, name) for name in agent_names}

    # Enable AI cache for faster re-runs and cost savings
    cache_dir = os.path.join(ROOT, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, "ai_decisions_cache.json")
    
    config = {
        "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],  # Only 3 symbols for faster data loading
        "start_date": "2025-11-01",  # Extended range to have enough data for indicators
        "end_date": "2025-11-15",    # 2 weeks of data
        "decision_interval": "4h",
        "intraday_interval": "3m",
        "intraday_lookback_hours": 4,
        "intraday_candles_count": 80,
        "initial_balance": 10_000.0,
        "fee_bps": 5.0,
        "slippage_bps": 2.0,
        "enable_multi_round": False,  # Disable multi-round for quick test
        "total_decision_cycles": 3,   # Only run 3 cycles for testing
        "disclosure_cycles": [],      # No disclosure for quick test
        "disclosure_days": [],
        "ai_cache_file": cache_file,  # Enable AI caching
    }

    evaluator = TradingEvaluator(agent_names=agent_names, agent_clients=agent_clients, config=config)
    
    # CHECKPOINT: Verify market data before running competition
    if not checkpoint_market_data(evaluator):
        print("❌ Checkpoint failed! Exiting.")
        return
    
    # Ask user if they want to continue
    print("\n🚀 Starting competition with 10 cycles...")
    print("Press Ctrl+C within 1 second to stop...\n")
    import time
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopped by user.")
        return
    
    performance = evaluator.run_competition()
    judge_text = performance.pop("_judge_text", "")

    print("\n" + "="*80)
    print("📊 FINAL PERFORMANCE RESULTS")
    print("="*80)
    
    # Sort by total_score descending
    sorted_perf = sorted(performance.items(), key=lambda x: x[1].total_score, reverse=True)
    
    for rank, (name, perf) in enumerate(sorted_perf, 1):
        print(f"\n{'🥇' if rank == 1 else '🥈' if rank == 2 else '🥉'} Agent: {name} (Rank #{rank})")
        print(f"   ┌─ Total Score: {perf.total_score:.4f}")
        print(f"   │")
        print(f"   ├─ Quantitative Metrics:")
        print(f"   │  ├─ Total Return: {perf.total_return_pct:.2f}% (${perf.total_return_usd:,.2f})")
        print(f"   │  ├─ Sharpe Ratio: {perf.sharpe_ratio:.4f}")
        print(f"   │  ├─ Max Drawdown: {perf.max_drawdown_pct:.2f}%")
        print(f"   │  ├─ Win Rate: {perf.win_rate:.2f}%")
        print(f"   │  ├─ Profit Factor: {perf.profit_factor:.2f}")
        print(f"   │  ├─ CAGR: {perf.cagr:.2f}%")
        print(f"   │  ├─ Volatility: {perf.volatility:.2f}%")
        print(f"   │  ├─ Sortino Ratio: {perf.sortino_ratio:.4f}")
        print(f"   │  └─ Total Trades: {perf.total_trades}")
        print(f"   │")
        print(f"   ├─ Score Breakdown (70% Quant + 30% Reasoning):")
        print(f"   │  ├─ Profitability: {perf.profitability_score:.4f}")
        print(f"   │  ├─ Risk Management: {perf.risk_management_score:.4f}")
        print(f"   │  ├─ Consistency: {perf.consistency_score:.4f}")
        print(f"   │  ├─ Efficiency: {perf.efficiency_score:.4f}")
        print(f"   │  ├─ Robustness: {perf.robustness_score:.4f}")
        print(f"   │  └─ Reasoning Quality: {perf.reasoning_score:.4f}")
        print(f"   │")
        print(f"   └─ Strategy: {perf.strategy}")
    
    print("\n" + "="*80)
    print("🏆 GREEN AGENT'S EVALUATION")
    print("="*80)
    print(judge_text)
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

