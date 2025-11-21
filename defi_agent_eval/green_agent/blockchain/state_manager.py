"""
State management for blockchain testing environment
Handles setting up initial state and verifying end state
"""

from typing import Dict, Any
from web3 import Web3
from .web3_client import BlockchainClient


class StateManager:
    """Manages blockchain state for testing"""
    
    def __init__(self, client: BlockchainClient):
        self.client = client
        self.w3 = client.w3
        
    def setup_initial_state(self, state_config: Dict[str, Any]) -> bool:
        """
        Setup initial blockchain state for a test
        
        Args:
            state_config: {
                "account": "0x...",
                "ETH_balance": 10.0,
                "USDC_balance": 5000,
                "DAI_balance": 2000
            }
        """
        try:
            account = state_config.get("account")
            
            # Fund account with ETH if needed
            if "ETH_balance" in state_config:
                target_balance = state_config["ETH_balance"]
                current_balance = self.client.get_balance(account)
                
                if current_balance < target_balance:
                    self.client.set_eth_balance(account, target_balance)
                    
            # Fund account with ERC20 tokens if needed
            for token_key in ["USDC_balance", "DAI_balance", "WETH_balance"]:
                if token_key in state_config:
                    token_name = token_key.replace("_balance", "")
                    amount = state_config[token_key]
                    self.client.fund_account_tokens(account, token_name, amount)
                    
            return True
            
        except Exception as e:
            print(f"Error setting up initial state: {e}")
            return False
    
    def get_current_state(self, account: str) -> Dict[str, Any]:
        """
        Get current state of an account
        
        Returns:
            {
                "ETH_balance": 9.5,
                "USDC_balance": 3000,
                "DAI_balance": 2000
            }
        """
        state = {
            "ETH_balance": self.client.get_balance(account)
        }
        
        # Get token balances using the consolidated method
        for token_name in ["USDC", "DAI", "WETH"]:
            balance = self.client.get_token_balance_human(token_name, account)
            state[f"{token_name}_balance"] = balance
                
        return state
    
    def verify_end_state(self, account: str, expected_state: Dict[str, Any], tolerance: float = 0.01) -> Dict[str, Any]:
        """
        Verify that current state matches expected state
        
        Args:
            account: Account address to check
            expected_state: Expected state values
            tolerance: Tolerance for balance comparisons (e.g., 0.01 for 1%)
            
        Returns:
            {
                "success": True/False,
                "matches": {"ETH_balance": True, "USDC_balance": True},
                "current_state": {...},
                "expected_state": {...}
            }
        """
        current_state = self.get_current_state(account)
        matches = {}
        
        for key, expected_value in expected_state.items():
            if key == "account":
                continue
                
            current_value = current_state.get(key)
            
            if current_value is None:
                matches[key] = False
                continue
            
            # Check if values match within tolerance
            if isinstance(expected_value, (int, float)):
                # Allow for tolerance in comparisons (for slippage, fees, etc.)
                difference = abs(current_value - expected_value)
                max_diff = abs(expected_value * tolerance)
                matches[key] = difference <= max_diff
            else:
                matches[key] = current_value == expected_value
                
        success = all(matches.values())
        
        return {
            "success": success,
            "matches": matches,
            "current_state": current_state,
            "expected_state": expected_state
        }
    
