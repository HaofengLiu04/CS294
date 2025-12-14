"""
Simulated trading account for backtesting.
Provides realistic exchange behavior simulation with fees, slippage, and leverage.
"""
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Position:
    """Represents an open position in the simulated account"""
    symbol: str
    side: str  # 'long' or 'short'
    quantity: float
    entry_price: float
    leverage: int
    margin: float
    notional: float
    liquidation_price: float
    open_time: int


class BacktestAccount:
    """
    Simulated trading account that mimics real exchange behavior.
    Supports long/short positions with leverage, fees, slippage, and liquidation.
    """
    
    EPSILON = 1e-8  # For float comparisons
    
    def __init__(self, initial_balance: float, fee_bps: float = 5.0, slippage_bps: float = 2.0):
        """
        Initialize simulated account.
        
        Args:
            initial_balance: Starting balance in USDT
            fee_bps: Trading fee in basis points (5 = 0.05%)
            slippage_bps: Slippage in basis points (2 = 0.02%)
        """
        self.initial_balance = initial_balance
        self.cash = initial_balance
        self.fee_rate = fee_bps / 10000.0
        self.slippage_rate = slippage_bps / 10000.0
        self.positions: Dict[str, Position] = {}  # key: "SYMBOL:side"
        self.realized_pnl = 0.0
    
    @staticmethod
    def _position_key(symbol: str, side: str) -> str:
        """Generate unique key for position"""
        return f"{symbol.upper()}:{side}"
    
    def _ensure_position(self, symbol: str, side: str) -> Position:
        """Get or create position"""
        key = self._position_key(symbol, side)
        if key in self.positions:
            return self.positions[key]
        
        pos = Position(
            symbol=symbol.upper(),
            side=side,
            quantity=0.0,
            entry_price=0.0,
            leverage=1,
            margin=0.0,
            notional=0.0,
            liquidation_price=0.0,
            open_time=0
        )
        self.positions[key] = pos
        return pos
    
    def _remove_position(self, pos: Position):
        """Remove position from account"""
        key = self._position_key(pos.symbol, pos.side)
        if key in self.positions:
            del self.positions[key]
    
    def open(self, symbol: str, side: str, quantity: float, leverage: int, 
             price: float, timestamp: int) -> Tuple[Optional[Position], float, float, Optional[str]]:
        """
        Open a new position or add to existing position.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'long' or 'short'
            quantity: Amount to trade
            leverage: Leverage multiplier (1-10x)
            price: Market price
            timestamp: Unix timestamp
            
        Returns:
            (position, fee, execution_price, error)
        """
        if quantity <= self.EPSILON:
            return None, 0.0, 0.0, "quantity too small"
        
        if leverage < 1:
            leverage = 1
        
        pos = self._ensure_position(symbol, side)
        
        # Apply slippage to execution price
        exec_price = self._apply_slippage(price, self.slippage_rate, side, is_open=True)
        
        # Calculate order value and costs
        order_value = quantity * exec_price
        fee = order_value * self.fee_rate
        margin_needed = order_value / leverage
        total_cost = margin_needed + fee
        
        # Check if sufficient cash
        if total_cost > self.cash:
            return None, 0.0, 0.0, "insufficient balance"
        
        # Deduct costs
        self.cash -= total_cost
        self.realized_pnl -= fee  # Fees are realized losses
        
        # Update position
        if pos.quantity < self.EPSILON:
            # New position
            pos.quantity = quantity
            pos.entry_price = exec_price
            pos.leverage = leverage
            pos.margin = margin_needed
            pos.notional = order_value
            pos.open_time = timestamp
        else:
            # Adding to existing position - calculate new weighted average
            total_qty = pos.quantity + quantity
            total_cost = (pos.quantity * pos.entry_price) + (quantity * exec_price)
            new_entry = total_cost / total_qty
            
            pos.quantity = total_qty
            pos.entry_price = new_entry
            pos.margin += margin_needed
            pos.notional += order_value
            # Keep same leverage
        
        # Calculate liquidation price
        pos.liquidation_price = self._compute_liquidation(pos.entry_price, pos.leverage, pos.side)
        
        return pos, fee, exec_price, None
    
    def close(self, symbol: str, side: str, quantity: float, 
              price: float) -> Tuple[float, float, float, Optional[str]]:
        """
        Close a position (partially or fully).
        
        Args:
            symbol: Trading pair
            side: 'long' or 'short'
            quantity: Amount to close
            price: Market price
            
        Returns:
            (realized_pnl, fee, execution_price, error)
        """
        key = self._position_key(symbol, side)
        if key not in self.positions:
            return 0.0, 0.0, 0.0, "no position found"
        
        pos = self.positions[key]
        
        if quantity <= self.EPSILON or quantity > pos.quantity + self.EPSILON:
            return 0.0, 0.0, 0.0, "invalid quantity"
        
        # Apply slippage to execution price
        exec_price = self._apply_slippage(price, self.slippage_rate, side, is_open=False)
        
        # Calculate close value and fee
        close_value = quantity * exec_price
        fee = close_value * self.fee_rate
        
        # Calculate PnL for the quantity being closed
        pnl = self._realized_pnl(pos, quantity, exec_price)
        
        # Calculate margin to return
        close_ratio = quantity / pos.quantity
        margin_returned = pos.margin * close_ratio
        
        # Update cash (return margin + pnl - fee)
        self.cash += margin_returned + pnl - fee
        self.realized_pnl += pnl - fee
        
        # Update position
        pos.quantity -= quantity
        pos.margin -= margin_returned
        pos.notional -= (quantity * pos.entry_price)
        
        # Remove position if fully closed
        if pos.quantity < self.EPSILON:
            self._remove_position(pos)
        
        return pnl, fee, exec_price, None
    
    def total_equity(self, price_map: Dict[str, float]) -> Tuple[float, float, Dict[str, float]]:
        """
        Calculate total account equity.
        
        Args:
            price_map: Current prices {symbol: price}
            
        Returns:
            (total_equity, unrealized_pnl, per_position_pnl)
        """
        unrealized = 0.0
        margin = 0.0
        per_symbol = {}
        
        for key, pos in self.positions.items():
            current_price = price_map.get(pos.symbol, pos.entry_price)
            pnl = self._unrealized_pnl(pos, current_price)
            
            unrealized += pnl
            margin += pos.margin
            per_symbol[key] = pnl
        
        total_equity = self.cash + margin + unrealized
        return total_equity, unrealized, per_symbol
    
    def get_positions(self) -> List[Position]:
        """Get all open positions"""
        return list(self.positions.values())
    
    def position_leverage(self, symbol: str, side: str) -> int:
        """Get leverage of a position"""
        key = self._position_key(symbol, side)
        if key in self.positions and self.positions[key].quantity > self.EPSILON:
            return self.positions[key].leverage
        return 0
    
    def get_cash(self) -> float:
        """Get available cash"""
        return self.cash
    
    def get_initial_balance(self) -> float:
        """Get initial balance"""
        return self.initial_balance
    
    def get_realized_pnl(self) -> float:
        """Get total realized PnL"""
        return self.realized_pnl
    
    def restore_from_snapshots(self, cash: float, realized: float, snapshots: List[Dict]):
        """Restore account state from checkpoint (for pause/resume)"""
        self.cash = cash
        self.realized_pnl = realized
        self.positions.clear()
        
        for snap in snapshots:
            pos = Position(
                symbol=snap['symbol'],
                side=snap['side'],
                quantity=snap['position_amt'],
                entry_price=snap['entry_price'],
                leverage=snap.get('leverage', 1),
                margin=snap['position_amt'] * snap['entry_price'] / snap.get('leverage', 1),
                notional=snap['position_amt'] * snap['entry_price'],
                liquidation_price=snap.get('liquidation_price', 0.0),
                open_time=0
            )
            key = self._position_key(pos.symbol, pos.side)
            self.positions[key] = pos
    
    @staticmethod
    def _apply_slippage(price: float, rate: float, side: str, is_open: bool) -> float:
        """
        Apply slippage to execution price.
        
        For longs: buying pushes price up, selling pushes down
        For shorts: selling pushes price down, buying pushes up
        """
        slippage_amount = price * rate
        
        if side == 'long':
            if is_open:
                return price + slippage_amount  # Buy at higher price
            else:
                return price - slippage_amount  # Sell at lower price
        else:  # short
            if is_open:
                return price - slippage_amount  # Short at lower price
            else:
                return price + slippage_amount  # Cover at higher price
    
    @staticmethod
    def _compute_liquidation(entry: float, leverage: int, side: str) -> float:
        """
        Calculate liquidation price.
        
        Liquidation happens when loss >= margin
        With leverage, margin = notional / leverage
        So loss = notional / leverage means 100% of margin is lost
        """
        if leverage <= 0:
            return 0.0
        
        # Liquidation at 100% loss of margin
        loss_pct = 1.0 / leverage  # e.g., 5x leverage = 20% price move to liquidate
        
        if side == 'long':
            # Price drops by loss_pct
            return entry * (1.0 - loss_pct)
        else:  # short
            # Price rises by loss_pct
            return entry * (1.0 + loss_pct)
    
    @staticmethod
    def _realized_pnl(pos: Position, qty: float, exit_price: float) -> float:
        """Calculate realized PnL for closing a position"""
        if pos.side == 'long':
            return (exit_price - pos.entry_price) * qty
        else:  # short
            return (pos.entry_price - exit_price) * qty
    
    @staticmethod
    def _unrealized_pnl(pos: Position, current_price: float) -> float:
        """Calculate unrealized PnL for an open position"""
        if pos.side == 'long':
            return (current_price - pos.entry_price) * pos.quantity
        else:  # short
            return (pos.entry_price - current_price) * pos.quantity
