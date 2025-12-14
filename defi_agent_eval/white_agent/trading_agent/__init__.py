"""
Trading Agent Module

Real-world cryptocurrency trading agent that connects to live exchanges.
"""

from .agent import RealWorldTradingAgent
from .backtest_account import BacktestAccount, Position
from .backtest_runner import BacktestRunner, TradeEvent, EquityPoint, BacktestMetrics

__all__ = [
    'RealWorldTradingAgent',
    'BacktestAccount',
    'Position',
    'BacktestRunner',
    'TradeEvent',
    'EquityPoint',
    'BacktestMetrics'
]
