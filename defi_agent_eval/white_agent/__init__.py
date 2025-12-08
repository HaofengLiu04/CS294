"""
White Agent Package

Collection of white agents (AI agents being evaluated) that execute blockchain operations.
"""

from .base_agent import WhiteAgent, ExecutionResult

# Import agents that require web3 only if available
try:
    from .cli_agent import CLIWhiteAgent
    from .code_agent import CodeWhiteAgent
    from .llm_agent import LLMWhiteAgent
    from .trading_agent import RealWorldTradingAgent  # Real exchange trading
    _all_agents_available = True
except ImportError:
    _all_agents_available = False
    CLIWhiteAgent = None
    CodeWhiteAgent = None
    LLMWhiteAgent = None
    RealWorldTradingAgent = None

__all__ = [
    'WhiteAgent',
    'ExecutionResult',
    'CLIWhiteAgent',
    'CodeWhiteAgent',
    'LLMWhiteAgent',
    'RealWorldTradingAgent'  # Real-world trading agent
]
