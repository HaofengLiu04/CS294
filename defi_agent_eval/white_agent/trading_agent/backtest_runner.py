"""
Backtest runner for trading agent.
Orchestrates historical data replay and performance analysis.
"""
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from .backtest_account import BacktestAccount, Position


@dataclass
class TradeEvent:
    """Record of a simulated trade"""
    timestamp: int
    symbol: str
    action: str  # 'open_long', 'close_long', 'open_short', 'close_short', 'hold'
    side: str  # 'long', 'short', or ''
    quantity: float
    price: float
    fee: float
    slippage: float
    order_value: float
    realized_pnl: float
    leverage: int
    cycle: int
    position_after: float
    liquidation: bool = False
    note: str = ""


@dataclass
class EquityPoint:
    """Equity snapshot at a point in time"""
    timestamp: int
    equity: float
    available: float
    pnl: float
    pnl_pct: float
    drawdown_pct: float
    cycle: int


@dataclass
class BacktestMetrics:
    """Final backtest performance metrics"""
    total_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    profit_factor: float
    win_rate: float
    trades: int
    avg_win: float
    avg_loss: float
    best_symbol: str
    worst_symbol: str
    liquidated: bool


class BacktestRunner:
    """
    Runs backtest simulation with historical data.
    Loads real market data, executes AI decisions, and calculates performance metrics.
    """
    
    def __init__(
        self,
        agent,
        symbols: List[str],
        start_time: int,
        end_time: int,
        initial_balance: float = 1000.0,
        fee_bps: float = 5.0,
        slippage_bps: float = 2.0,
        decision_interval: str = "1h",  # How often to make decisions
        leverage_config: Optional[Dict[str, int]] = None
    ):
        """
        Initialize backtest runner.
        
        Args:
            agent: Your RealWorldTradingAgent instance
            symbols: List of trading pairs
            start_time: Start timestamp (unix)
            end_time: End timestamp (unix)
            initial_balance: Starting balance
            fee_bps: Trading fees in basis points
            slippage_bps: Slippage in basis points
            decision_interval: How often AI makes decisions ('1h', '4h', etc.)
            leverage_config: {'BTC': 5, 'ETH': 5, 'default': 3}
        """
        self.agent = agent
        self.symbols = symbols
        self.start_time = start_time
        self.end_time = end_time
        self.decision_interval = decision_interval
        
        # Initialize simulated account
        self.account = BacktestAccount(initial_balance, fee_bps, slippage_bps)
        
        # Leverage configuration
        self.leverage_config = leverage_config or {
            'BTC': 5,
            'ETH': 5,
            'default': 3
        }
        
        # State tracking
        self.cycle_count = 0
        self.equity_history: List[EquityPoint] = []
        self.trade_events: List[TradeEvent] = []
        self.max_equity = initial_balance
        self.min_equity = initial_balance
        self.max_drawdown = 0.0
        
        # Historical data cache
        self.historical_data: Dict[str, List[Dict]] = {}
    
    def run(self, verbose: bool = True) -> Tuple[BacktestMetrics, List[EquityPoint], List[TradeEvent]]:
        """
        Run the backtest simulation.
        
        Returns:
            (metrics, equity_history, trade_events)
        """
        if verbose:
            print(f"\n[START] Starting Backtest")
            print(f"Symbols: {', '.join(self.symbols)}")
            print(f"Period: {datetime.fromtimestamp(self.start_time)} to {datetime.fromtimestamp(self.end_time)}")
            print(f"Initial Balance: ${self.account.initial_balance:.2f}")
            print(f"Fee: {self.account.fee_rate * 10000:.2f} bps")
            print(f"Slippage: {self.account.slippage_rate * 10000:.2f} bps")
            print("=" * 60)
        
        # Load historical data for all symbols
        self._load_historical_data()
        
        # Get decision timestamps based on interval
        decision_timestamps = self._get_decision_timestamps()
        
        total_cycles = len(decision_timestamps)
        
        for idx, ts in enumerate(decision_timestamps):
            self.cycle_count += 1
            
            # Get current market data at this timestamp
            market_data = self._get_market_data_at(ts)
            price_map = {sym: data['close'] for sym, data in market_data.items()}
            
            # Check for liquidations
            liquidation_note = self._check_liquidations(price_map)
            if liquidation_note:
                if verbose:
                    print(f"\n[LIQUIDATED] at cycle {self.cycle_count}: {liquidation_note}")
                self._record_equity_point(ts, price_map, liquidated=True)
                break
            
            # Get AI decision
            if verbose and self.cycle_count % 10 == 0:
                equity, _, _ = self.account.total_equity(price_map)
                progress = (idx + 1) / total_cycles * 100
                print(f"Cycle {self.cycle_count}/{total_cycles} ({progress:.1f}%) | Equity: ${equity:.2f}")
            
            try:
                decision = self._get_ai_decision(ts, market_data, price_map)
                
                # Execute decision
                trades = self._execute_decision(decision, price_map, ts)
                self.trade_events.extend(trades)
                
            except Exception as e:
                if verbose:
                    print(f"[WARNING] Error in cycle {self.cycle_count}: {e}")
                # Continue even if AI decision fails
                decision = {'action': 'hold'}
            
            # Record equity point
            self._record_equity_point(ts, price_map)
        
        # Calculate final metrics
        metrics = self._calculate_metrics()
        
        if verbose:
            print("\n" + "=" * 60)
            print("Backtest Results:")
            print(f"Total Return: {metrics.total_return_pct:+.2f}%")
            print(f"Max Drawdown: {metrics.max_drawdown_pct:.2f}%")
            print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
            print(f"Win Rate: {metrics.win_rate:.1f}%")
            print(f"Total Trades: {metrics.trades}")
            print(f"Profit Factor: {metrics.profit_factor:.2f}")
            if metrics.liquidated:
                print("[WARNING] Account was LIQUIDATED")
        
        return metrics, self.equity_history, self.trade_events
    
    def _load_historical_data(self):
        """Load historical kline data for all symbols"""
        print(f"\n[LOAD] Loading historical data...")
        
        for symbol in self.symbols:
            try:
                # Use agent's get_klines method to fetch historical data
                klines = self.agent.get_klines(
                    symbol,
                    interval=self.decision_interval,
                    limit=1000  # Adjust based on time range
                )
                
                self.historical_data[symbol] = klines
                print(f"   [OK] {symbol}: {len(klines)} candles")
                
            except Exception as e:
                print(f"   [FAIL] {symbol}: Failed to load data - {e}")
                self.historical_data[symbol] = []
    
    def _get_decision_timestamps(self) -> List[int]:
        """Generate list of timestamps where AI makes decisions"""
        # Parse interval (e.g., "1h" -> 3600 seconds)
        interval_map = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }
        
        interval_seconds = interval_map.get(self.decision_interval, 3600)
        
        timestamps = []
        current = self.start_time
        
        while current <= self.end_time:
            timestamps.append(current)
            current += interval_seconds
        
        return timestamps
    
    def _get_market_data_at(self, timestamp: int) -> Dict[str, Dict]:
        """Get market data snapshot at a specific timestamp"""
        market_data = {}
        
        for symbol, klines in self.historical_data.items():
            # Find the kline that contains this timestamp
            for kline in klines:
                kline_time = kline.get('timestamp', kline.get('open_time', 0))
                
                # Convert to seconds if in milliseconds
                if kline_time > 1e10:
                    kline_time = kline_time // 1000
                
                if kline_time <= timestamp:
                    market_data[symbol] = {
                        'timestamp': kline_time,
                        'open': float(kline.get('open', 0)),
                        'high': float(kline.get('high', 0)),
                        'low': float(kline.get('low', 0)),
                        'close': float(kline.get('close', 0)),
                        'volume': float(kline.get('volume', 0))
                    }
        
        return market_data
    
    def _check_liquidations(self, price_map: Dict[str, float]) -> Optional[str]:
        """Check if any positions should be liquidated"""
        for pos in self.account.get_positions():
            current_price = price_map.get(pos.symbol, pos.entry_price)
            
            if pos.side == 'long' and current_price <= pos.liquidation_price:
                return f"{pos.symbol} long liquidated at ${current_price:.2f}"
            elif pos.side == 'short' and current_price >= pos.liquidation_price:
                return f"{pos.symbol} short liquidated at ${current_price:.2f}"
        
        return None
    
    def _get_ai_decision(self, timestamp: int, market_data: Dict, price_map: Dict) -> Dict:
        """Get AI trading decision (simplified - uses agent's decision logic)"""
        # Build context similar to live trading
        equity, unrealized, _ = self.account.total_equity(price_map)
        
        # Convert positions to agent format
        positions = []
        for pos in self.account.get_positions():
            current_price = price_map.get(pos.symbol, pos.entry_price)
            unrealized_pnl = BacktestAccount._unrealized_pnl(pos, current_price)
            
            positions.append({
                'symbol': pos.symbol,
                'side': pos.side,
                'quantity': pos.quantity,
                'entry_price': pos.entry_price,
                'current_price': current_price,
                'unrealized_pnl': unrealized_pnl,
                'leverage': pos.leverage
            })
        
        balance_info = {
            'total_equity': equity,
            'available_balance': self.account.get_cash(),
            'total_pnl': equity - self.account.initial_balance,
            'unrealized_pnl': unrealized
        }
        
        # Call agent's AI decision method
        # Note: This is simplified - you may need to adapt based on your agent's interface
        decision = self.agent._get_ai_decision(
            cycle_number=self.cycle_count,
            balance=balance_info,
            positions=positions,
            market_data=market_data,
            custom_instruction="Backtest mode: simulate historical trading"
        )
        
        return decision
    
    def _execute_decision(self, decision: Dict, price_map: Dict, timestamp: int) -> List[TradeEvent]:
        """Execute AI decision in simulated account"""
        trades = []
        action = decision.get('action', 'hold').lower()
        
        if action == 'hold':
            return trades
        
        symbol = decision.get('symbol', '').upper()
        if not symbol or symbol not in price_map:
            return trades
        
        price = price_map[symbol]
        leverage = self._resolve_leverage(decision.get('leverage', 1), symbol)
        
        # Handle different actions
        if action == 'open_long' or action == 'buy':
            qty = self._determine_quantity(decision, price, leverage)
            if qty > 0:
                pos, fee, exec_price, err = self.account.open(
                    symbol, 'long', qty, leverage, price, timestamp
                )
                
                if pos:
                    trades.append(TradeEvent(
                        timestamp=timestamp,
                        symbol=symbol,
                        action='open_long',
                        side='long',
                        quantity=qty,
                        price=exec_price,
                        fee=fee,
                        slippage=exec_price - price,
                        order_value=exec_price * qty,
                        realized_pnl=0,
                        leverage=leverage,
                        cycle=self.cycle_count,
                        position_after=pos.quantity
                    ))
        
        elif action == 'open_short' or action == 'sell':
            qty = self._determine_quantity(decision, price, leverage)
            if qty > 0:
                pos, fee, exec_price, err = self.account.open(
                    symbol, 'short', qty, leverage, price, timestamp
                )
                
                if pos:
                    trades.append(TradeEvent(
                        timestamp=timestamp,
                        symbol=symbol,
                        action='open_short',
                        side='short',
                        quantity=qty,
                        price=exec_price,
                        fee=fee,
                        slippage=price - exec_price,
                        order_value=exec_price * qty,
                        realized_pnl=0,
                        leverage=leverage,
                        cycle=self.cycle_count,
                        position_after=pos.quantity
                    ))
        
        elif action == 'close_long':
            qty = self._determine_close_quantity(symbol, 'long', decision)
            if qty > 0:
                realized, fee, exec_price, err = self.account.close(
                    symbol, 'long', qty, price
                )
                
                if err is None:
                    trades.append(TradeEvent(
                        timestamp=timestamp,
                        symbol=symbol,
                        action='close_long',
                        side='long',
                        quantity=qty,
                        price=exec_price,
                        fee=fee,
                        slippage=price - exec_price,
                        order_value=exec_price * qty,
                        realized_pnl=realized,
                        leverage=0,
                        cycle=self.cycle_count,
                        position_after=self._remaining_position(symbol, 'long')
                    ))
        
        elif action == 'close_short':
            qty = self._determine_close_quantity(symbol, 'short', decision)
            if qty > 0:
                realized, fee, exec_price, err = self.account.close(
                    symbol, 'short', qty, price
                )
                
                if err is None:
                    trades.append(TradeEvent(
                        timestamp=timestamp,
                        symbol=symbol,
                        action='close_short',
                        side='short',
                        quantity=qty,
                        price=exec_price,
                        fee=fee,
                        slippage=exec_price - price,
                        order_value=exec_price * qty,
                        realized_pnl=realized,
                        leverage=0,
                        cycle=self.cycle_count,
                        position_after=self._remaining_position(symbol, 'short')
                    ))
        
        return trades
    
    def _determine_quantity(self, decision: Dict, price: float, leverage: int) -> float:
        """Calculate quantity to trade based on decision"""
        size_usd = decision.get('size_usd', 0)
        
        if size_usd <= 0:
            # Default to 10% of equity
            equity, _, _ = self.account.total_equity({})
            size_usd = equity * 0.1
        
        # Calculate quantity needed
        qty = size_usd / price
        
        # Check if we have enough margin
        margin_needed = size_usd / leverage
        if margin_needed > self.account.get_cash():
            # Scale down to available cash
            qty = (self.account.get_cash() * leverage) / price
        
        return qty
    
    def _determine_close_quantity(self, symbol: str, side: str, decision: Dict) -> float:
        """Determine how much of a position to close"""
        key = f"{symbol}:{side}"
        positions = {self.account._position_key(p.symbol, p.side): p 
                    for p in self.account.get_positions()}
        
        if key not in positions:
            return 0.0
        
        pos = positions[key]
        
        # Check if decision specifies quantity
        close_pct = decision.get('close_pct', 1.0)  # Default: close 100%
        
        return pos.quantity * close_pct
    
    def _remaining_position(self, symbol: str, side: str) -> float:
        """Get remaining position after trade"""
        key = f"{symbol}:{side}"
        positions = {self.account._position_key(p.symbol, p.side): p 
                    for p in self.account.get_positions()}
        
        if key in positions:
            return positions[key].quantity
        return 0.0
    
    def _resolve_leverage(self, requested: int, symbol: str) -> int:
        """Get leverage for a symbol"""
        if 'BTC' in symbol:
            return self.leverage_config.get('BTC', 5)
        elif 'ETH' in symbol:
            return self.leverage_config.get('ETH', 5)
        else:
            return self.leverage_config.get('default', 3)
    
    def _record_equity_point(self, timestamp: int, price_map: Dict, liquidated: bool = False):
        """Record equity snapshot"""
        equity, unrealized, _ = self.account.total_equity(price_map)
        
        # Update max/min equity
        if equity > self.max_equity:
            self.max_equity = equity
        if equity < self.min_equity:
            self.min_equity = equity
        
        # Calculate drawdown
        if self.max_equity > 0:
            drawdown = ((self.max_equity - equity) / self.max_equity) * 100
            if drawdown > self.max_drawdown:
                self.max_drawdown = drawdown
        else:
            drawdown = 0
        
        pnl = equity - self.account.initial_balance
        pnl_pct = (pnl / self.account.initial_balance) * 100
        
        point = EquityPoint(
            timestamp=timestamp,
            equity=equity,
            available=self.account.get_cash(),
            pnl=pnl,
            pnl_pct=pnl_pct,
            drawdown_pct=drawdown,
            cycle=self.cycle_count
        )
        
        self.equity_history.append(point)
    
    def _calculate_metrics(self) -> BacktestMetrics:
        """Calculate final performance metrics"""
        final_equity = self.equity_history[-1].equity if self.equity_history else self.account.initial_balance
        
        total_return_pct = ((final_equity - self.account.initial_balance) / 
                           self.account.initial_balance) * 100
        
        # Calculate Sharpe ratio
        sharpe = self._calculate_sharpe()
        
        # Calculate trade metrics
        trade_metrics = self._calculate_trade_metrics()
        
        return BacktestMetrics(
            total_return_pct=total_return_pct,
            max_drawdown_pct=self.max_drawdown,
            sharpe_ratio=sharpe,
            profit_factor=trade_metrics['profit_factor'],
            win_rate=trade_metrics['win_rate'],
            trades=trade_metrics['total_trades'],
            avg_win=trade_metrics['avg_win'],
            avg_loss=trade_metrics['avg_loss'],
            best_symbol=trade_metrics['best_symbol'],
            worst_symbol=trade_metrics['worst_symbol'],
            liquidated=any(e.equity <= 0 for e in self.equity_history)
        )
    
    def _calculate_sharpe(self) -> float:
        """Calculate Sharpe ratio from equity curve"""
        if len(self.equity_history) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(self.equity_history)):
            prev = self.equity_history[i-1].equity
            curr = self.equity_history[i].equity
            if prev > 0:
                ret = (curr - prev) / prev
                returns.append(ret)
        
        if not returns:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        
        if len(returns) < 2:
            return 0.0
        
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0.0
        
        # Annualize (assuming daily returns for simplification)
        sharpe = (mean_return / std_dev) * (365 ** 0.5)
        
        return sharpe
    
    def _calculate_trade_metrics(self) -> Dict:
        """Calculate win rate, profit factor, etc."""
        closing_trades = [t for t in self.trade_events if 'close' in t.action]
        
        if not closing_trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'best_symbol': '',
                'worst_symbol': ''
            }
        
        wins = [t for t in closing_trades if t.realized_pnl > 0]
        losses = [t for t in closing_trades if t.realized_pnl < 0]
        
        total_trades = len(closing_trades)
        win_count = len(wins)
        loss_count = len(losses)
        
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0.0
        
        total_win = sum(t.realized_pnl for t in wins)
        total_loss = abs(sum(t.realized_pnl for t in losses))
        
        profit_factor = (total_win / total_loss) if total_loss > 0 else (999 if total_win > 0 else 0)
        
        avg_win = (total_win / win_count) if win_count > 0 else 0.0
        avg_loss = (total_loss / loss_count) if loss_count > 0 else 0.0
        
        # Per-symbol analysis
        symbol_pnl = {}
        for trade in closing_trades:
            if trade.symbol not in symbol_pnl:
                symbol_pnl[trade.symbol] = 0.0
            symbol_pnl[trade.symbol] += trade.realized_pnl
        
        best_symbol = max(symbol_pnl.items(), key=lambda x: x[1])[0] if symbol_pnl else ''
        worst_symbol = min(symbol_pnl.items(), key=lambda x: x[1])[0] if symbol_pnl else ''
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'best_symbol': best_symbol,
            'worst_symbol': worst_symbol
        }
