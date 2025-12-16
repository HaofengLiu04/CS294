"""
Trading evaluation (Green Agent) built on top of white_agent.trading_agent backtest
components.

This package provides:
- Market data loading with indicator calculation
- Prompt construction for White Agents (trading agents)
- Backtest-style execution using BacktestAccount
- Multi-agent competition loop with disclosure rounds
"""

from .models import (
    TradingAction,
    TradingDecision,
    ReasoningEvaluation,
    AgentRoundDecision,
    DisclosurePackage,
    AgentPerformance,
)
from .trading_evaluator import TradingEvaluator

__all__ = [
    "TradingEvaluator",
    "TradingAction",
    "TradingDecision",
    "ReasoningEvaluation",
    "AgentRoundDecision",
    "DisclosurePackage",
    "AgentPerformance",
]

