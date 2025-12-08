#!/usr/bin/env python3
"""
SECURE Setup: Hyperliquid Real Trading Agent

SECURITY RULES:
1. NEVER post private keys publicly or in code
2. NEVER commit .env file to git
3. Use environment variables or .env file ONLY
4. Keep private keys offline when not in use
"""

import os
from dotenv import load_dotenv
from .agent import RealWorldTradingAgent

# Load environment variables from .env file (SECURE)
load_dotenv()

def setup_hyperliquid_agent():
    """
    Initialize Hyperliquid agent with REAL blockchain (mainnet)
    
    Required in .env file:
    - HYPERLIQUID_PRIVATE_KEY=0x...
    - HYPERLIQUID_WALLET_ADDRESS=0x...
    - DEEPSEEK_API_KEY=sk-...
    """
    
    print("\n" + "="*80)
    print("HYPERLIQUID REAL TRADING AGENT SETUP")
    print("="*80)
    
    # Get credentials from environment (SECURE - not hardcoded)
    private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")
    wallet_address = os.getenv("HYPERLIQUID_WALLET_ADDRESS")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    
    # Verify all required credentials are present
    if not private_key:
        print("\n[ERROR] HYPERLIQUID_PRIVATE_KEY not found in .env file")
        print("\nCreate a .env file with:")
        print("HYPERLIQUID_PRIVATE_KEY=0xyour_private_key")
        return None
    
    if not wallet_address:
        print("\n[ERROR] HYPERLIQUID_WALLET_ADDRESS not found in .env file")
        print("\nAdd to .env file:")
        print("HYPERLIQUID_WALLET_ADDRESS=0xyour_wallet_address")
        return None
    
    if not deepseek_key:
        print("\n[ERROR] DEEPSEEK_API_KEY not found in .env file")
        print("\nAdd to .env file:")
        print("DEEPSEEK_API_KEY=sk-your_api_key")
        return None
    
    # Mask sensitive info for display
    masked_key = private_key[:6] + "..." + private_key[-4:]
    masked_wallet = wallet_address[:6] + "..." + wallet_address[-4:]
    masked_deepseek = deepseek_key[:8] + "..." + deepseek_key[-4:]
    
    print(f"\n[OK] Private key loaded: {masked_key}")
    print(f"[OK] Wallet address: {masked_wallet}")
    print(f"[OK] DeepSeek API key: {masked_deepseek}")
    
    # Confirm before proceeding
    print("\n" + "="*80)
    print("WARNING: REAL BLOCKCHAIN - REAL MONEY!")
    print("="*80)
    print("\nThis agent will:")
    print("  - Connect to Hyperliquid MAINNET (not testnet)")
    print("  - Use REAL funds from your wallet")
    print("  - Execute REAL trades on the blockchain")
    print("  - Incur REAL gas fees and trading fees")
    print("\nMake sure:")
    print("  1. You have tested thoroughly on testnet first")
    print("  2. You understand the risks")
    print("  3. You're ready for live trading")
    
    confirm = input("\nType 'YES' to proceed with LIVE trading: ").strip()
    
    if confirm != "YES":
        print("\n[CANCELLED] Setup cancelled. Good decision to be cautious!")
        return None
    
    print("\n[1/2] Initializing Hyperliquid agent (MAINNET)...")
    
    try:
        agent = RealWorldTradingAgent(
            exchange="hyperliquid",
            private_key=private_key,
            wallet_address=wallet_address,
            testnet=False,  # ← MAINNET = REAL MONEY!
            llm_api_key=deepseek_key,
            llm_model="deepseek-chat",  # Using DeepSeek for AI
            name="Hyperliquid Live Agent"
        )
        
        print("[✓] Agent initialized successfully!")
        
        print("\n[2/2] Checking wallet balance...")
        
        balance = agent.get_balance()
        print(f"\n   Total Equity: ${balance['total_equity']:,.2f}")
        print(f"   Available: ${balance['available_balance']:,.2f}")
        
        print("\n" + "="*80)
        print("[OK] SETUP COMPLETE - Agent is ready for LIVE trading")
        print("="*80)
        
        return agent
        
    except Exception as e:
        print(f"\n[ERROR] Failed to initialize agent")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        return None


def test_basic_operations(agent):
    """Test basic read operations (safe - no trading)"""
    
    print("\n" + "="*80)
    print("TESTING BASIC OPERATIONS (Read Only - Safe)")
    print("="*80)
    
    try:
        # Test 1: Get market price
        print("\n[Test 1/3] Fetching market prices...")
        symbols = ["BTC", "ETH", "SOL"]
        for symbol in symbols:
            try:
                price = agent.get_market_price(symbol)
                print(f"   {symbol}: ${price:,.2f}")
            except Exception as e:
                print(f"   {symbol}: [ERROR] {e}")
        
        # Test 2: Get positions
        print("\n[Test 2/3] Checking current positions...")
        positions = agent.get_positions()
        if positions:
            print(f"   You have {len(positions)} open position(s):")
            for pos in positions:
                print(f"      {pos['symbol']}: {pos['side']} {pos['size']}")
        else:
            print("   No open positions")
        
        # Test 3: Get balance
        print("\n[Test 3/3] Account balance...")
        balance = agent.get_balance()
        print(f"   Total Equity: ${balance['total_equity']:,.2f}")
        print(f"   Available: ${balance['available_balance']:,.2f}")
        
        print("\n[OK] All basic operations working!")
        
    except Exception as e:
        print(f"\n[ERROR] during testing: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("\n" + "="*80)
    print("SECURE HYPERLIQUID SETUP")
    print("="*80)
    
    print("\nThis script will:")
    print("  1. Load credentials from .env file (SECURE)")
    print("  2. Initialize Hyperliquid agent on MAINNET")
    print("  3. Test basic read operations")
    print("  4. Prepare agent for live trading")
    
    print("\nMake sure you have a .env file with:")
    print("   HYPERLIQUID_PRIVATE_KEY=0x...")
    print("   HYPERLIQUID_WALLET_ADDRESS=0x...")
    print("   DEEPSEEK_API_KEY=sk-...")
    
    input("\nPress ENTER to continue...")
    
    # Setup agent
    agent = setup_hyperliquid_agent()
    
    if agent:
        # Test basic operations
        test_basic_operations(agent)
        
        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)
        print("\nYour agent is ready! You can now:")
        print("  1. Run a single trading cycle: agent.run_cycle()")
        print("  2. Provide custom instructions: agent.run_cycle(custom_instruction='...')")
        print("  3. Start automated trading (run cycles in a loop)")
        print("\nExample:")
        print("  result = agent.run_cycle()")
        print("  print(result['decision'])")


if __name__ == "__main__":
    main()
