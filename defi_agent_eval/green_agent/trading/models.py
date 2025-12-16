from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class TradingAction:
    symbol: str
    action: str  # open_long | open_short | close_long | close_short | hold | wait
    leverage: int = 1
    quantity: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    confidence: float = 0.5
    risk_usd: float = 0.0
    reasoning: str = ""


@dataclass
class TradingDecision:
    summary: str
    reasoning: str
    actions: List[TradingAction] = field(default_factory=list)


@dataclass
class ReasoningEvaluation:
    agent_name: str
    cycle_idx: int
    timestamp: str
    decision_process_adherence: float
    technical_analysis_accuracy: float
    risk_assessment_quality: float
    logical_consistency: float
    multi_timeframe_quality: float
    overall_score: float
    strengths: str
    weaknesses: str
    suggestions: str


@dataclass
class AgentRoundDecision:
    agent_name: str
    day: int
    round: int
    market_view: str
    opponent_analysis: Optional[Dict[str, str]]
    strategy_adjustment: Optional[str]
    actions: List[TradingAction]
    full_reasoning: str


@dataclass
class DisclosurePackage:
    round_number: int
    disclosure_day: int
    leaderboard: List[Dict]
    agents_round_summary: List[Dict]


@dataclass
class AgentReasoningQuality:
    agent_name: str
    total_evaluations: int
    avg_decision_process: float
    avg_technical_analysis: float
    avg_risk_assessment: float
    avg_logical_consistency: float
    avg_multi_timeframe: float
    overall_reasoning_score: float
    excellent_count: int
    good_count: int
    poor_count: int


@dataclass
class AgentPerformance:
    agent_name: str
    strategy: str
    total_return_pct: float
    total_return_usd: float
    cagr: float
    sharpe_ratio: float
    max_drawdown_pct: float
    volatility: float
    sortino_ratio: float
    total_trades: int
    win_rate: float
    profit_factor: float
    avg_trades_per_day: float
    reasoning_quality: Optional[AgentReasoningQuality] = None
    profitability_score: float = 0.0
    risk_management_score: float = 0.0
    consistency_score: float = 0.0
    efficiency_score: float = 0.0
    robustness_score: float = 0.0
    reasoning_score: float = 0.0
    total_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)

