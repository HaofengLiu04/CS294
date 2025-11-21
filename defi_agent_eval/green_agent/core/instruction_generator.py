"""
Natural Language Instruction Generator
Converts <start_state, operations, end_state> into natural language instructions
"""

from typing import Dict, List, Any


class InstructionGenerator:
    """Generates natural language instructions from test scenarios"""
    
    def __init__(self):
        self.operation_templates = {
            "send_erc20": self._generate_erc20_transfer,
            "swap_uniswap": self._generate_uniswap_swap,
            "dao_vote": self._generate_dao_vote,
            "lending_1inch": self._generate_lending,
            "bridge_rollup": self._generate_bridge
        }
    
    def generate_instruction(self, test_scenario: Dict[str, Any]) -> str:
        """
        Generate natural language instruction from test scenario
        
        Args:
            test_scenario: {
                "start_state": {...},
                "operations": [...],
                "end_state": {...}
            }
            
        Returns:
            Natural language instruction string
        """
        operations = test_scenario.get("operations", [])
        
        if not operations:
            return "No operations specified"
        
        instructions = []
        
        for op in operations:
            if isinstance(op, dict):
                op_type = op.get("type")
                op_params = op.get("params", {})
            else:
                # Simple string operation
                op_type = op
                op_params = {}
            
            # Generate instruction for this operation
            generator = self.operation_templates.get(op_type)
            if generator:
                instruction = generator(op_params, test_scenario.get("start_state", {}))
                instructions.append(instruction)
            else:
                instructions.append(f"Unknown operation: {op_type}")
        
        # Combine all instructions
        if len(instructions) == 1:
            return instructions[0]
        else:
            return "Please complete the following operations in order:\n" + "\n".join(
                f"{i+1}. {inst}" for i, inst in enumerate(instructions)
            )
    
    def _generate_erc20_transfer(self, params: Dict[str, Any], start_state: Dict[str, Any]) -> str:
        """Generate instruction for ERC20 token transfer"""
        token = params.get("token", "USDC")
        amount = params.get("amount", 1000)
        to_address = params.get("to", "0x...")
        
        return (
            f"Transfer {amount} {token} tokens to address {to_address}. "
            f"Make sure to check your current {token} balance first and ensure you have sufficient tokens."
        )
    
    def _generate_uniswap_swap(self, params: Dict[str, Any], start_state: Dict[str, Any]) -> str:
        """Generate instruction for Uniswap swap"""
        from_token = params.get("from_token", "ETH")
        to_token = params.get("to_token", "USDC")
        amount = params.get("amount", 1.0)
        slippage = params.get("slippage_tolerance", 0.5)
        
        return (
            f"Swap {amount} {from_token} for {to_token} on Uniswap V3. "
            f"Use a slippage tolerance of {slippage}% to protect against price fluctuations. "
            f"The transaction should execute via the Uniswap V3 Router contract."
        )
    
    def _generate_dao_vote(self, params: Dict[str, Any], start_state: Dict[str, Any]) -> str:
        """Generate instruction for DAO voting"""
        dao_name = params.get("dao_name", "the DAO")
        proposal_id = params.get("proposal_id", "123")
        vote_choice = params.get("vote", "for")
        
        return (
            f"Cast a vote '{vote_choice}' on proposal #{proposal_id} in {dao_name}. "
            f"Make sure you have voting power (governance tokens) before attempting to vote."
        )
    
    def _generate_lending(self, params: Dict[str, Any], start_state: Dict[str, Any]) -> str:
        """Generate instruction for lending operation"""
        action = params.get("action", "supply")  # supply, borrow, withdraw, repay
        token = params.get("token", "USDC")
        amount = params.get("amount", 1000)
        protocol = params.get("protocol", "1inch")
        
        action_verb = {
            "supply": "Supply",
            "borrow": "Borrow", 
            "withdraw": "Withdraw",
            "repay": "Repay"
        }.get(action, "Supply")
        
        return (
            f"{action_verb} {amount} {token} {'to' if action in ['supply', 'repay'] else 'from'} "
            f"{protocol} lending protocol. Make sure to approve the protocol to access your tokens first."
        )
    
    def _generate_bridge(self, params: Dict[str, Any], start_state: Dict[str, Any]) -> str:
        """Generate instruction for rollup bridging"""
        from_chain = params.get("from_chain", "Ethereum")
        to_chain = params.get("to_chain", "Arbitrum")
        token = params.get("token", "ETH")
        amount = params.get("amount", 0.1)
        
        return (
            f"Bridge {amount} {token} from {from_chain} to {to_chain}. "
            f"Use the official bridge contract and be aware that bridging may take several minutes. "
            f"Make sure you have enough {token} for both the bridge amount and gas fees."
        )
    
    def generate_with_context(self, test_scenario: Dict[str, Any]) -> str:
        """Generate instruction with full context including constraints"""
        instruction = self.generate_instruction(test_scenario)
        
        # Add context about start and end states
        start_state = test_scenario.get("start_state", {})
        end_state = test_scenario.get("end_state", {})
        
        context = f"""
TASK CONTEXT:
Your current account state:
"""
        for key, value in start_state.items():
            if key != "account":
                context += f"  - {key}: {value}\n"
        
        context += f"\nINSTRUCTION:\n{instruction}\n"
        
        if end_state:
            context += "\nEXPECTED OUTCOME:\n"
            for key, value in end_state.items():
                if key != "account":
                    context += f"  - {key}: {value}\n"
        
        return context.strip()


if __name__ == "__main__":
    # Test instruction generation
    generator = InstructionGenerator()
    
    test_scenario = {
        "start_state": {
            "account": "0x123...",
            "ETH_balance": 10.0,
            "USDC_balance": 0
        },
        "operations": [
            {
                "type": "swap_uniswap",
                "params": {
                    "from_token": "ETH",
                    "to_token": "USDC",
                    "amount": 1.0,
                    "slippage_tolerance": 0.5
                }
            }
        ],
        "end_state": {
            "ETH_balance": 9.0,
            "USDC_balance": 2000
        }
    }
    
    print(generator.generate_with_context(test_scenario))
