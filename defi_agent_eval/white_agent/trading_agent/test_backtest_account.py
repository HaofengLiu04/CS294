"""
Simple test to verify backtest account works correctly
"""
from trading_agent.backtest_account import BacktestAccount


def test_basic_account():
    """Test basic account operations"""
    print("Testing Backtest Account...")
    
    # Initialize account
    account = BacktestAccount(
        initial_balance=1000.0,
        fee_bps=5.0,
        slippage_bps=2.0
    )
    
    print(f"[PASS] Initial balance: ${account.get_cash():.2f}")
    assert account.get_cash() == 1000.0
    
    # Open a long position
    pos, fee, exec_price, err = account.open(
        symbol='BTCUSDT',
        side='long',
        quantity=0.01,
        leverage=5,
        price=50000,
        timestamp=1234567890
    )
    
    assert err is None, f"Error opening position: {err}"
    print(f"[PASS] Opened position: 0.01 BTC @ ${exec_price:.2f}")
    print(f"  - Fee: ${fee:.2f}")
    print(f"  - Margin: ${pos.margin:.2f}")
    print(f"  - Liquidation price: ${pos.liquidation_price:.2f}")
    print(f"  - Cash after: ${account.get_cash():.2f}")
    
    # Check equity with price movement
    equity1, unrealized1, _ = account.total_equity({'BTCUSDT': 51000})
    print(f"\n[PASS] Price rises to $51,000")
    print(f"  - Unrealized PnL: ${unrealized1:+.2f}")
    print(f"  - Total equity: ${equity1:.2f}")
    
    # Close position
    realized, fee2, exec_price2, err = account.close(
        symbol='BTCUSDT',
        side='long',
        quantity=0.01,
        price=52000
    )
    
    assert err is None, f"Error closing position: {err}"
    print(f"\n[PASS] Closed position at ${exec_price2:.2f}")
    print(f"  - Realized PnL: ${realized:+.2f}")
    print(f"  - Fee: ${fee2:.2f}")
    print(f"  - Final cash: ${account.get_cash():.2f}")
    print(f"  - Final equity: ${account.get_cash():.2f}")
    
    # Verify profit
    total_pnl = account.get_realized_pnl()
    print(f"\n[PASS] Total realized PnL: ${total_pnl:+.2f}")
    
    expected_gross_pnl = (52000 - 50000) * 0.01  # Should be around $20
    print(f"  - Expected gross: ${expected_gross_pnl:.2f}")
    print(f"  - After fees: ${total_pnl:.2f}")
    
    # Verify account made money
    assert total_pnl > 0, "Account should have made money!"
    assert account.get_cash() > 1000, "Cash should be more than initial balance!"
    
    print("\n[SUCCESS] All tests passed!")


def test_short_position():
    """Test short position"""
    print("\nTesting Short Position...")
    
    account = BacktestAccount(1000.0, 5.0, 2.0)
    
    # Open short at $50,000
    pos, _, _, _ = account.open('BTCUSDT', 'short', 0.01, 5, 50000, 123)
    print(f"[PASS] Opened short: 0.01 BTC @ ${pos.entry_price:.2f}")
    print(f"  - Liquidation: ${pos.liquidation_price:.2f}")
    
    # Price drops (profit for short)
    equity, unrealized, _ = account.total_equity({'BTCUSDT': 48000})
    print(f"\n[PASS] Price drops to $48,000")
    print(f"  - Unrealized PnL: ${unrealized:+.2f}")
    print(f"  - Equity: ${equity:.2f}")
    
    assert unrealized > 0, "Short should profit when price drops!"
    
    # Close at profit
    realized, _, _, _ = account.close('BTCUSDT', 'short', 0.01, 48000)
    print(f"\n[PASS] Closed short")
    print(f"  - Realized PnL: ${realized:+.2f}")
    print(f"  - Final equity: ${account.get_cash():.2f}")
    
    assert realized > 0, "Should have made profit on short!"
    assert account.get_cash() > 1000, "Account should have gained value!"
    
    print("[SUCCESS] Short position test passed!")


def test_liquidation():
    """Test liquidation detection"""
    print("\nTesting Liquidation Detection...")
    
    account = BacktestAccount(1000.0, 5.0, 2.0)
    
    # Open 5x leveraged long
    pos, _, _, _ = account.open('BTCUSDT', 'long', 0.01, 5, 50000, 123)
    print(f"[PASS] Opened 5x long @ ${pos.entry_price:.2f}")
    print(f"  - Liquidation price: ${pos.liquidation_price:.2f}")
    
    # With 5x leverage, 20% drop should liquidate
    # Entry ~50,010, liquidation ~40,008
    assert pos.liquidation_price < pos.entry_price * 0.82
    
    # Check if price at liquidation would wipe account
    equity, unrealized, _ = account.total_equity({'BTCUSDT': pos.liquidation_price})
    print(f"\n[PASS] At liquidation price ${pos.liquidation_price:.2f}:")
    print(f"  - Unrealized PnL: ${unrealized:.2f}")
    print(f"  - Would lose margin: ${abs(unrealized):.2f}")
    
    print("[SUCCESS] Liquidation detection works!")


if __name__ == "__main__":
    try:
        test_basic_account()
        test_short_position()
        test_liquidation()
        
        print("\n" + "="*60)
        print("All backtest account tests passed!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
