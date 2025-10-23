"""
White Agent Simulator - Sample implementations for demo purposes

This module provides sample White Agent implementations that demonstrate
different quality levels and risk profiles for Green Agent evaluation.
"""

from green_agent import AgentAction, TaskType
import random

class WhiteAgentSimulator:
    """Simulates different types of White Agents for testing"""
    
    @staticmethod
    def create_optimal_swap_agent_action():
        """Creates a high-quality token swap action"""
        return AgentAction(
            task_type=TaskType.TOKEN_SWAP,
            action_description="Swap 2 ETH to USDC using Uniswap V3 with 0.5% slippage tolerance",
            calldata="swapExactETHForTokens(amountIn=2_ETH, path=[WETH,USDC], fee=3000, slippageTolerance=50)",
            estimated_gas=135000,
            expected_outcome={
                "amount": 3970.15,
                "token": "USDC",
                "slippage": 0.005,
                "route": "ETH->USDC_direct"
            },
            risk_factors=["moderate_slippage"]
        )
    
    @staticmethod
    def create_risky_agent_action():
        """Creates a high-risk action with multiple red flags"""
        return AgentAction(
            task_type=TaskType.TOKEN_SWAP,
            action_description="Swap 10 ETH to SHIB via unknown aggregator with 20% slippage",
            calldata="executeSwap(token=0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE, slippage=20%, verify=false)",
            estimated_gas=650000,
            expected_outcome={
                "amount": 8500000000,  # Unrealistic amount
                "token": "SHIB",
                "slippage": 0.20
            },
            risk_factors=[
                "unverified_contract", 
                "high_slippage", 
                "excessive_gas",
                "sandwich_attack_risk",
                "price_manipulation"
            ]
        )
    
    @staticmethod 
    def create_portfolio_rebalance_action():
        """Creates a portfolio rebalancing action"""
        return AgentAction(
            task_type=TaskType.PORTFOLIO_REBALANCE,
            action_description="Rebalance portfolio to 60% ETH, 25% USDC, 15% WBTC based on risk parity model",
            calldata="rebalancePortfolio(strategy='risk_parity', targets=[0.6,0.25,0.15], threshold=3%)",
            estimated_gas=420000,
            expected_outcome={
                "target_allocation": {"ETH": 0.6, "USDC": 0.25, "WBTC": 0.15},
                "rebalance_trades": 4,
                "estimated_fees": 0.035,
                "time_to_execute": "45_seconds"
            },
            risk_factors=["multiple_transactions", "timing_risk"]
        )
    
    @staticmethod
    def create_staking_action():
        """Creates a staking/lending action"""
        return AgentAction(
            task_type=TaskType.STAKING_LENDING,
            action_description="Stake 5 ETH in Lido for liquid staking with automatic rewards",
            calldata="stakeLido(amount=5_ETH, auto_compound=true, withdrawal_address=user)",
            estimated_gas=180000,
            expected_outcome={
                "staked_amount": 5.0,
                "expected_apy": 0.045,
                "staking_token": "stETH",
                "liquidity": "high"
            },
            risk_factors=["smart_contract_risk", "slashing_risk"]
        )
    
    @staticmethod
    def create_dangerous_flashloan_action():
        """Creates a dangerous flashloan strategy"""
        return AgentAction(
            task_type=TaskType.AUTOMATED_STRATEGY,
            action_description="Execute complex flashloan arbitrage with 50x leverage",
            calldata="flashloanArbitrage(amount=2000_ETH, leverage=50, protocols=[aave,compound,curve])",
            estimated_gas=1200000,
            expected_outcome={
                "profit_estimate": 125.5,
                "success_rate": 0.45,
                "liquidation_risk": 0.55,
                "max_loss": 2000  # Entire flashloan amount
            },
            risk_factors=[
                "flashloan_exploit",
                "price_manipulation", 
                "excessive_gas",
                "high_leverage",
                "liquidation_risk",
                "sandwich_attack_risk"
            ]
        )

# Demonstration of different agent quality levels
def demonstrate_agent_spectrum():
    """Show the spectrum of agent quality from excellent to dangerous"""
    
    print("🤖 WHITE AGENT SPECTRUM DEMONSTRATION")
    print("=" * 60)
    
    agents = [
        ("Excellent Agent", WhiteAgentSimulator.create_optimal_swap_agent_action()),
        ("Good Agent", WhiteAgentSimulator.create_portfolio_rebalance_action()),
        ("Average Agent", WhiteAgentSimulator.create_staking_action()),
        ("Poor Agent", WhiteAgentSimulator.create_risky_agent_action()),
        ("Dangerous Agent", WhiteAgentSimulator.create_dangerous_flashloan_action())
    ]
    
    for name, action in agents:
        print(f"\n{name}:")
        print(f"  Task: {action.task_type.value}")
        print(f"  Description: {action.action_description}")
        print(f"  Risk Factors: {len(action.risk_factors)} identified")
        print(f"  Estimated Gas: {action.estimated_gas:,}")

if __name__ == "__main__":
    demonstrate_agent_spectrum()