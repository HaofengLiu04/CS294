#!/usr/bin/env python3
"""
Demo: Using Custom Instructions with Trading Agent

This shows how to provide your own prompts/instructions to the AI trading agent.
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from white_agent.trading_agent import RealWorldTradingAgent

load_dotenv()


def demo_custom_instructions():
    """Show different ways to use custom instructions"""
    
    # Initialize agent
    agent = RealWorldTradingAgent(
        exchange="binance",
        api_key=os.getenv("BINANCE_API_KEY"),
        api_secret=os.getenv("BINANCE_API_SECRET"),
        testnet=True,
        llm_model="gpt-4o"
    )
    
    print("=" * 80)
    print("Trading Agent with Custom Instructions")
    print("=" * 80)
    
    # Example 1: No custom instruction (autonomous mode)
    print("\n[Example 1] Autonomous Mode (no custom instruction)")
    print("-" * 80)
    result1 = agent.run_cycle(symbols=["BTCUSDT", "ETHUSDT"])
    print(f"Decision: {result1['decision']['action']}")
    print(f"Reasoning: {result1['decision']['reasoning'][:150]}...")
    
    # Example 2: Custom instruction - Focus on specific coin
    print("\n\n[Example 2] Custom Instruction: Focus on BTC only")
    print("-" * 80)
    result2 = agent.run_cycle(
        symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
        custom_instruction="Only consider trading Bitcoin (BTCUSDT). Ignore other coins."
    )
    print(f"Decision: {result2['decision']['action']}")
    print(f"Symbol: {result2['decision'].get('symbol', 'N/A')}")
    
    # Example 3: Custom instruction - Close all positions
    print("\n\n[Example 3] Custom Instruction: Close all positions")
    print("-" * 80)
    result3 = agent.run_cycle(
        custom_instruction="Close all open positions immediately. Do not open new positions."
    )
    print(f"Decision: {result3['decision']['action']}")
    
    # Example 4: Custom instruction - Conservative trading
    print("\n\n[Example 4] Custom Instruction: Conservative risk management")
    print("-" * 80)
    result4 = agent.run_cycle(
        custom_instruction="""
        Be extremely conservative:
        - Never use more than 2x leverage
        - Only trade if you have very high confidence (80%+)
        - Position size should not exceed 1% of account
        - Prefer holding to trading
        """
    )
    print(f"Decision: {result4['decision']['action']}")
    
    # Example 5: Custom instruction - Specific strategy
    print("\n\n[Example 5] Custom Instruction: Specific trading strategy")
    print("-" * 80)
    result5 = agent.run_cycle(
        symbols=["BTCUSDT"],
        custom_instruction="""
        Strategy: Buy the dip
        - Only open long if BTC is down more than 3% in 24h
        - Use 3x leverage
        - Position size: $200
        - If no dip, then hold
        """
    )
    print(f"Decision: {result5['decision']['action']}")
    if result5['decision'].get('symbol'):
        print(f"Symbol: {result5['decision']['symbol']}")
        print(f"Size: ${result5['decision'].get('size_usd', 0)}")
        print(f"Leverage: {result5['decision'].get('leverage', 'N/A')}x")
    
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    
    print("\n Key Takeaways:")
    print("  - No custom_instruction: Agent decides autonomously")
    print("  - With custom_instruction: You guide the AI's decision")
    print("  - Custom instructions are added to the prompt sent to LLM")
    print("  - AI still uses Chain of Thought reasoning")
    print("  - You can provide any instruction you want!")


def examples_of_custom_instructions():
    """Show different types of custom instructions you can use"""
    
    print("\n" + "=" * 80)
    print("Examples of Custom Instructions")
    print("=" * 80)
    
    examples = {
        "Risk Management": [
            "Never use more than 3x leverage",
            "Maximum position size: 5% of account",
            "Always set stop loss at 2%",
            "Only trade during US market hours"
        ],
        
        "Trading Restrictions": [
            "Only trade Bitcoin and Ethereum",
            "Do not open new positions, only manage existing ones",
            "Close all positions before the weekend",
            "Do not trade altcoins, only BTC"
        ],
        
        "Strategy Specific": [
            "Only buy when RSI is below 30",
            "Trend following: only trade in direction of 4h trend",
            "Scalping: take profit at 1%, stop loss at 0.5%",
            "DCA strategy: buy $100 of BTC every cycle if price is down"
        ],
        
        "Market Conditions": [
            "If volatility is high, reduce position size by 50%",
            "During trending markets, use trailing stops",
            "If market is choppy, stay in cash",
            "In bear market, prefer short positions"
        ],
        
        "Account Management": [
            "If account is down 10%, stop trading for the day",
            "Take profits when P/L reaches +5%",
            "After 3 losing trades, reduce size to minimum",
            "If win rate drops below 40%, switch to paper trading mode"
        ],
        
        "Time-based": [
            "It's Friday evening, close all positions",
            "Major news coming in 2 hours, reduce exposure",
            "It's the weekend, no new trades",
            "End of month, take profits and rebalance"
        ]
    }
    
    for category, instructions in examples.items():
        print(f"\n{category}:")
        for i, instruction in enumerate(instructions, 1):
            print(f"  {i}. \"{instruction}\"")
    
    print("\n" + "=" * 80)
    print("You can combine multiple instructions too!")
    print("=" * 80)
    
    combined_example = """
    COMBINED INSTRUCTIONS:
    
    Risk Management:
    - Maximum 3x leverage
    - Position size: 2% of account
    - Always use stop loss
    
    Strategy:
    - Only trade BTC and ETH
    - Trend following approach
    - Take profit at 5%, stop loss at 2%
    
    Current Situation:
    - It's Friday afternoon
    - Close any losing positions
    - Let winners run over the weekend
    """
    
    print(combined_example)
    
    print("\n Tips:")
    print("  - Be specific and clear")
    print("  - Provide context when needed")
    print("  - Can be as simple or complex as you want")
    print("  - AI will interpret and follow your instruction")


if __name__ == "__main__":
    import sys
    
    print("\nChoose demo:")
    print("  [1] Run custom instruction examples with real agent")
    print("  [2] See examples of custom instructions (no trading)")
    print("  [0] Exit")
    
    choice = input("\nEnter choice (0-2): ").strip()
    
    if choice == "1":
        # Check if credentials are available
        if not os.getenv("BINANCE_API_KEY"):
            print("\n Warning: BINANCE_API_KEY not found in .env")
            print("Set up your testnet credentials first!")
            sys.exit(1)
        
        demo_custom_instructions()
    
    elif choice == "2":
        examples_of_custom_instructions()
    
    elif choice == "0":
        print("Goodbye!")
    
    else:
        print("Invalid choice")
