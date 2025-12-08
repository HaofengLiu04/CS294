#!/usr/bin/env python3
"""
Test Binance API Access (With VPN)
Tests if we can connect to Binance's real APIs
"""

import sys
import os

# Path setup for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

def test_binance_public_api():
    """Test Binance public API without authentication"""
    print("\n" + "="*80)
    print("TEST 1: Binance Public API (No Authentication Required)")
    print("="*80)
    
    try:
        from binance.client import Client
        
        print("\n[1/3] Creating Binance client...")
        # No API key needed for public endpoints
        client = Client()
        print("[OK] Client created")
        
        print("\n[2/3] Testing connection with ping...")
        try:
            client.ping()
            print("[OK] Connection successful!")
        except Exception as e:
            print(f"[FAIL] Connection failed: {e}")
            return False
        
        print("\n[3/3] Fetching real-time prices from Binance...")
        
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT"]
        
        for symbol in symbols:
            try:
                ticker = client.get_symbol_ticker(symbol=symbol)
                price = float(ticker['price'])
                print(f"   {symbol:12s} = ${price:,.2f}")
            except Exception as e:
                print(f"   {symbol:12s} = [FAIL] {e}")
                return False
        
        print("\n[SUCCESS] Binance API is accessible!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_binance_futures_api():
    """Test Binance Futures API (used for real-time trading data)"""
    print("\n" + "="*80)
    print("TEST 2: Binance Futures API (Real Trading Data Source)")
    print("="*80)
    
    try:
        from binance.client import Client
        
        print("\n[1/3] Creating Binance Futures client...")
        client = Client()
        print("[OK] Client created")
        
        print("\n[2/3] Fetching futures market prices...")
        
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        
        for symbol in symbols:
            try:
                # Futures market ticker
                ticker = client.futures_symbol_ticker(symbol=symbol)
                price = float(ticker['price'])
                print(f"   {symbol:12s} = ${price:,.2f}")
            except Exception as e:
                print(f"   {symbol:12s} = [FAIL] {e}")
                return False
        
        print("\n[3/3] Fetching futures candlestick data...")
        
        try:
            # Historical candle data
            klines = client.futures_klines(
                symbol="BTCUSDT",
                interval="1h",
                limit=5
            )
            print(f"   Retrieved {len(klines)} candlesticks for BTCUSDT")
            if klines:
                latest = klines[-1]
                print(f"   Latest candle:")
                print(f"      Open:  ${float(latest[1]):,.2f}")
                print(f"      High:  ${float(latest[2]):,.2f}")
                print(f"      Low:   ${float(latest[3]):,.2f}")
                print(f"      Close: ${float(latest[4]):,.2f}")
        except Exception as e:
            print(f"   [FAIL] Could not fetch klines: {e}")
            return False
        
        print("\n[SUCCESS] Binance Futures API is accessible!")
        print("This means the trading agent can fetch real-world data!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_price_fetching():
    """Test if trading agent's actual price fetching method works"""
    print("\n" + "="*80)
    print("TEST 3: Trading Agent Price Fetching (Actual Implementation)")
    print("="*80)
    
    try:
        from white_agent.trading_agent import RealWorldTradingAgent
        from dotenv import load_dotenv
        
        load_dotenv()
        
        print("\n[1/4] Checking credentials...")
        api_key = os.getenv("BINANCE_API_KEY", "dummy_key_for_public_api")
        api_secret = os.getenv("BINANCE_API_SECRET", "dummy_secret_for_public_api")
        
        print("\n[2/4] Initializing trading agent with Binance testnet...")
        
        try:
            agent = RealWorldTradingAgent(
                exchange="binance",
                api_key=api_key,
                api_secret=api_secret,
                testnet=True,
                name="VPN Test Agent"
            )
            print("[OK] Agent initialized")
        except Exception as init_error:
            print(f"[INFO] Could not fully initialize agent: {init_error}")
            print("[INFO] This is OK if you don't have testnet credentials")
            print("[INFO] The important test is if Binance API is reachable...")
            return None
        
        print("\n[3/4] Testing agent's get_market_price() method...")
        
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        
        for symbol in symbols:
            try:
                # Agent's price fetching method
                price = agent.get_market_price(symbol)
                print(f"   {symbol:12s} = ${price:,.2f}")
            except Exception as e:
                print(f"   {symbol:12s} = [FAIL] {e}")
                return False
        
        print("\n[4/4] Testing agent's get_klines() method...")
        
        try:
            klines = agent.get_klines("BTCUSDT", interval="1h", limit=5)
            print(f"   Retrieved {len(klines)} candlesticks")
            latest = klines[-1]
            print(f"   Latest candle: Open=${latest['open']:,.2f}, Close=${latest['close']:,.2f}")
        except Exception as e:
            print(f"   [FAIL] {e}")
            return False
        
        print("\n[SUCCESS] Trading agent can fetch real-world data from Binance!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*80)
    print("BINANCE API ACCESS TEST (With VPN)")
    print("Testing if Binance APIs are accessible from your location")
    print("="*80)
    
    print("\nThis will test:")
    print("  1. Basic Binance public API connectivity")
    print("  2. Binance Futures API (real trading data source)")
    print("  3. Trading agent's price fetching methods")
    
    input("\nPress ENTER to start tests...")
    
    # Test 1: Basic API
    result1 = test_binance_public_api()
    
    # Test 2: Futures API
    result2 = test_binance_futures_api()
    
    # Test 3: Agent methods
    result3 = test_agent_price_fetching()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    if result1:
        print("✓ Binance Public API: ACCESSIBLE")
    else:
        print("✗ Binance Public API: BLOCKED")
    
    if result2:
        print("✓ Binance Futures API: ACCESSIBLE")
    else:
        print("✗ Binance Futures API: BLOCKED")
    
    if result3:
        print("✓ Trading Agent Methods: WORKING")
    elif result3 is None:
        print("? Trading Agent Methods: NEED CREDENTIALS (but Binance API is reachable)")
    else:
        print("✗ Trading Agent Methods: FAILED")
    
    print("\n" + "="*80)
    
    if result1 and result2:
        print("\nSUCCESS! VPN is working!")
        print("\nYou can now:")
        print("  1. Use Binance API for real-world price data")
        print("  2. Set up trading agent with Binance testnet")
        print("  3. Test the full trading cycle with real market data")
        print("\nNext step: Get Binance testnet credentials from:")
        print("  https://testnet.binancefuture.com")
    else:
        print("\nVPN may not be working or Binance is still blocked")
        print("\nTry:")
        print("  1. Check if VPN is connected and active")
        print("  2. Try a different VPN server location")
        print("  3. Use CoinGecko API as alternative (already tested and working)")


if __name__ == "__main__":
    main()
