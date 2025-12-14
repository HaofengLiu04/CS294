"""
Demo: Run a backtest on your trading agent
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_agent.agent import RealWorldTradingAgent
from trading_agent.backtest_runner import BacktestRunner


def run_backtest_demo():
    """Run a simple backtest on historical data"""
    
    # Load environment variables
    load_dotenv()
    
    print("Trading Agent Backtest Demo")
    print("=" * 60)
    
    # Initialize your agent
    agent = RealWorldTradingAgent(
        exchange='hyperliquid',
        api_key=None,
        api_secret=None,
        private_key=os.getenv('HYPERLIQUID_PRIVATE_KEY'),
        wallet_address=os.getenv('HYPERLIQUID_WALLET_ADDRESS'),
        testnet=False,  # We need mainnet to fetch real historical data
        llm_model='deepseek-chat',
        llm_api_key=os.getenv('DEEPSEEK_API_KEY'),
        name="BacktestAgent"
    )
    
    print(f"[INIT] Agent initialized: {agent.name}")
    
    # Define backtest parameters
    symbols = ['BTCUSDT', 'ETHUSDT']
    
    # Backtest last 7 days
    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(days=7)).timestamp())
    
    print(f"\nBacktest Period:")
    print(f"   Start: {datetime.fromtimestamp(start_time)}")
    print(f"   End: {datetime.fromtimestamp(end_time)}")
    
    # Create backtest runner
    runner = BacktestRunner(
        agent=agent,
        symbols=symbols,
        start_time=start_time,
        end_time=end_time,
        initial_balance=1000.0,
        fee_bps=5.0,
        slippage_bps=2.0,
        decision_interval='4h',
        leverage_config={
            'BTC': 5,
            'ETH': 5,
            'default': 3
        }
    )
    
    print(f"\nConfiguration:")
    print(f"   Initial Balance: $1,000")
    print(f"   Trading Fees: 0.05%")
    print(f"   Slippage: 0.02%")
    print(f"   Decision Interval: Every 4 hours")
    print(f"   Leverage: BTC/ETH 5x, Others 3x")
    
    # Run backtest
    print("\n" + "=" * 60)
    metrics, equity_history, trade_events = runner.run(verbose=True)
    
    # Display detailed results
    print("\n" + "=" * 60)
    print("DETAILED RESULTS")
    print("=" * 60)
    
    print(f"\nReturns:")
    print(f"   Initial Balance:  ${runner.account.initial_balance:.2f}")
    print(f"   Final Equity:     ${equity_history[-1].equity:.2f}")
    print(f"   Total Return:     {metrics.total_return_pct:+.2f}%")
    print(f"   Realized PnL:     ${runner.account.get_realized_pnl():.2f}")
    
    print(f"\nRisk Metrics:")
    print(f"   Max Drawdown:     {metrics.max_drawdown_pct:.2f}%")
    print(f"   Sharpe Ratio:     {metrics.sharpe_ratio:.2f}")
    print(f"   Liquidated:       {'YES' if metrics.liquidated else 'No'}")
    
    print(f"\nTrading Performance:")
    print(f"   Total Trades:     {metrics.trades}")
    print(f"   Win Rate:         {metrics.win_rate:.1f}%")
    print(f"   Profit Factor:    {metrics.profit_factor:.2f}")
    print(f"   Avg Win:          ${metrics.avg_win:.2f}")
    print(f"   Avg Loss:         ${metrics.avg_loss:.2f}")
    
    if metrics.best_symbol:
        print(f"\nBest Symbol:      {metrics.best_symbol}")
    if metrics.worst_symbol:
        print(f"Worst Symbol:     {metrics.worst_symbol}")
    
    # Show recent trades
    print(f"\nRecent Trades (last 10):")
    for trade in trade_events[-10:]:
        timestamp = datetime.fromtimestamp(trade.timestamp).strftime('%Y-%m-%d %H:%M')
        action_indicator = '[OPEN]' if 'open' in trade.action else '[CLOSE]'
        pnl_str = f"${trade.realized_pnl:+.2f}" if trade.realized_pnl != 0 else ""
        
        print(f"   {action_indicator} {timestamp} | {trade.symbol:8} | {trade.action:12} | "
              f"{trade.quantity:.4f} @ ${trade.price:.2f} | {pnl_str}")
    
    # Show equity curve samples
    print(f"\nEquity Curve (samples):")
    sample_interval = max(1, len(equity_history) // 10)
    for i in range(0, len(equity_history), sample_interval):
        point = equity_history[i]
        timestamp = datetime.fromtimestamp(point.timestamp).strftime('%Y-%m-%d %H:%M')
        equity_change = point.pnl_pct
        direction = '[UP]' if equity_change >= 0 else '[DOWN]'
        
        print(f"   {direction} {timestamp} | Equity: ${point.equity:7.2f} | "
              f"PnL: {equity_change:+6.2f}% | DD: {point.drawdown_pct:5.2f}%")
    print("\n" + "=" * 60)
    print("Backtest Complete!")
    print("=" * 60)
    
    # Save results to file
    output_file = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(output_file, 'w') as f:
        f.write("BACKTEST RESULTS\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Period: {datetime.fromtimestamp(start_time)} to {datetime.fromtimestamp(end_time)}\n")
        f.write(f"Symbols: {', '.join(symbols)}\n\n")
        f.write(f"Total Return: {metrics.total_return_pct:+.2f}%\n")
        f.write(f"Max Drawdown: {metrics.max_drawdown_pct:.2f}%\n")
        f.write(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}\n")
        f.write(f"Win Rate: {metrics.win_rate:.1f}%\n")
        f.write(f"Total Trades: {metrics.trades}\n")
        f.write(f"Profit Factor: {metrics.profit_factor:.2f}\n\n")
        
        f.write("TRADE HISTORY:\n")
        f.write("-" * 60 + "\n")
        for trade in trade_events:
            timestamp = datetime.fromtimestamp(trade.timestamp).strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp} | {trade.symbol} | {trade.action} | "
                   f"{trade.quantity:.4f} @ ${trade.price:.2f} | "
                   f"PnL: ${trade.realized_pnl:+.2f}\n")
    
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    try:
        run_backtest_demo()
    except KeyboardInterrupt:
        print("\n\nBacktest interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
