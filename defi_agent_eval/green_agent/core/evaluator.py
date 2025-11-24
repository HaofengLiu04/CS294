"""
Main Green Agent Evaluator
Orchestrates the entire evaluation process
"""

from typing import Dict, Any, List
import json
from ..blockchain.web3_client import BlockchainClient
from ..blockchain.state_manager import StateManager
from .instruction_generator import InstructionGenerator
from ..operations.erc20_transfer import ERC20Transfer


class GreenAgentEvaluator:
    """
    Main evaluator that coordinates environment setup, instruction generation,
    and state verification for DeFi agent testing
    """
    
    def __init__(self, rpc_url: str = None):
        # Initialize blockchain client
        self.client = BlockchainClient(rpc_url)
        self.state_manager = StateManager(self.client)
        self.instruction_generator = InstructionGenerator()
        
        # Initialize operation handlers
        self.operations = {
            "send_erc20": ERC20Transfer(self.client)
        }
        
        # Evaluation history
        self.evaluation_results = []
    
    def evaluate_scenario(self, test_scenario: Dict[str, Any], white_agent_response: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Complete evaluation flow for a single test scenario
        
        Args:
            test_scenario: {
                "id": "test_001",
                "name": "ERC20 Transfer Test",
                "start_state": {...},
                "operations": [...],
                "end_state": {...}
            }
            white_agent_response: Optional response from white agent (for verification)
            
        Returns:
            {
                "scenario_id": "test_001",
                "success": True/False,
                "instruction": "...",
                "state_verification": {...},
                "execution_result": {...}
            }
        """
        scenario_id = test_scenario.get("id", "unknown")
        account = test_scenario.get("start_state", {}).get("account", self.client.accounts['deployer'])
        
        print(f"\n Evaluating Scenario: {scenario_id}")
        print("=" * 60)
        
        # Step 1: Setup initial state
        print("[INFO] Step 1: Setting up initial blockchain state...")
        setup_success = self.state_manager.setup_initial_state(test_scenario["start_state"])
        
        if not setup_success:
            return {
                "scenario_id": scenario_id,
                "success": False,
                "error": "Failed to setup initial state"
            }
        
        initial_state = self.state_manager.get_current_state(account)
        print(f"[OK] Initial state ready: {initial_state}")
        
        # Step 2: Generate natural language instruction
        print("\n[INPUT] Step 2: Generating natural language instruction...")
        instruction = self.instruction_generator.generate_with_context(test_scenario)
        print(f"[INSTRUCTION] Instruction:\n{instruction}")
        
        # Step 3: Execute operations (if white agent response provided or direct execution)
        print("\n[EXEC]  Step 3: Executing operations...")
        execution_result = None
        
        if white_agent_response:
            # White agent has already executed, just verify
            print("[INFO]  White agent already executed, skipping direct execution")
        else:
            # Direct execution for testing (simulating white agent)
            execution_result = self._execute_operations(test_scenario, account)
            print(f"[DATA] Execution result: {execution_result}")
        
        # Step 4: Verify end state
        print("\n[VERIFY] Step 4: Verifying end state...")
        verification_result = self.state_manager.verify_end_state(
            account,
            test_scenario["end_state"],
            tolerance=0.01  # 1% tolerance for price fluctuations
        )
        
        print(f"[RESULT] Verification: {'PASSED' if verification_result['success'] else 'FAILED'}")
        print(f"   Matches: {verification_result['matches']}")
        print(f"   Current: {verification_result['current_state']}")
        print(f"   Expected: {verification_result['expected_state']}")
        
        # Compile result
        result = {
            "scenario_id": scenario_id,
            "scenario_name": test_scenario.get("name", ""),
            "success": verification_result["success"],
            "instruction": instruction,
            "initial_state": initial_state,
            "state_verification": verification_result,
            "execution_result": execution_result
        }
        
        self.evaluation_results.append(result)
        return result
    
    def _execute_operations(self, test_scenario: Dict[str, Any], account: str) -> Dict[str, Any]:
        """Execute operations for testing purposes"""
        operations = test_scenario.get("operations", [])
        results = []
        
        # Use test private key (Anvil default account #0)
        private_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        
        for op in operations:
            if isinstance(op, dict):
                op_type = op.get("type")
                op_params = op.get("params", {})
            else:
                op_type = op
                op_params = {}
            
            # Execute operation
            if op_type in self.operations:
                result = self.operations[op_type].execute(op_params, account, private_key)
                results.append({"operation": op_type, "result": result})
            else:
                results.append({"operation": op_type, "result": {"success": False, "error": "Unsupported operation"}})
        
        return {"operations_executed": len(results), "results": results}
    
    def evaluate_with_white_agent(self, test_scenario: Dict[str, Any], white_agent) -> Dict[str, Any]:
        """
        Evaluate a test scenario using a white agent (AI agent being tested).
        
        Args:
            test_scenario: Test scenario dict with start_state, operations, end_state
            white_agent: Instance of a WhiteAgent (e.g., LLMWhiteAgent)
        
        Returns:
            Evaluation result dict
        """
        scenario_id = test_scenario.get("id", "unknown")
        account = test_scenario.get("start_state", {}).get("account", self.client.accounts['deployer'])
        
        print(f"\n[EVAL] Evaluating Scenario: {scenario_id}")
        print(f"[AGENT] Using White Agent: {white_agent.name}")
        print("=" * 60)
        
        # Step 1: Setup initial blockchain state
        print("[INFO] Step 1: Setting up initial blockchain state...")
        setup_success = self.state_manager.setup_initial_state(test_scenario["start_state"])
        
        if not setup_success:
            return {
                "scenario_id": scenario_id,
                "success": False,
                "error": "Failed to setup initial state"
            }
        
        initial_state = self.state_manager.get_current_state(account)
        print(f"[OK] Initial state ready: {initial_state}")
        
        # Step 2: Generate natural language instruction
        print("\n[INPUT] Step 2: Generating natural language instruction...")
        instruction = self.instruction_generator.generate_with_context(test_scenario)
        print(f"[INSTRUCTION] Instruction:\n{instruction}")
        
        # Step 3: White Agent executes the instruction
        print(f"\n[AGENT] Step 3: White Agent ({white_agent.name}) executing...")
        context = {
            "initial_state": initial_state,
            "scenario": test_scenario
        }
        execution_result = white_agent.execute_instruction(instruction, context)
        
        print(f"[OK] White Agent execution completed")
        print(f"   Success: {execution_result.success}")
        if execution_result.transaction_hash:
            print(f"   TX Hash: {execution_result.transaction_hash}")
        if execution_result.error:
            print(f"   Error: {execution_result.error}")
        
        # Step 4: Verify end state (only if agent succeeded)
        print("\n[VERIFY] Step 4: Verifying end state...")
        if execution_result.success:
            verification_result = self.state_manager.verify_end_state(
                account,
                test_scenario["end_state"],
                tolerance=0.01
            )
        else:
            verification_result = {
                "success": False,
                "error": "Skipped verification because white agent execution failed"
            }
        
        print(f"[RESULT] Verification: {'PASSED' if verification_result.get('success') else 'FAILED'}")
        if 'matches' in verification_result:
            print(f"   Matches: {verification_result['matches']}")
        
        # Compile result
        result = {
            "scenario_id": scenario_id,
            "scenario_name": test_scenario.get("name", ""),
            "success": verification_result.get("success", False),
            "instruction": instruction,
            "initial_state": initial_state,
            "white_agent_result": {
                "success": execution_result.success,
                "transaction_hash": execution_result.transaction_hash,
                "error": execution_result.error,
                "execution_time": execution_result.execution_time,
                "metadata": execution_result.metadata
            },
            "state_verification": verification_result
        }
        
        self.evaluation_results.append(result)
        return result
    
    def run_test_suite(self, test_scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run a full test suite with multiple scenarios
        
        Returns:
            Summary of all test results
        """
        print("\n[START] Starting Green Agent Test Suite")
        print("=" * 80)
        
        total = len(test_scenarios)
        passed = 0
        failed = 0
        
        for scenario in test_scenarios:
            result = self.evaluate_scenario(scenario)
            if result["success"]:
                passed += 1
            else:
                failed += 1
        
        summary = {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "results": self.evaluation_results
        }
        
        print("\n" + "=" * 80)
        print("[DATA] TEST SUITE SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total}")
        print(f"[OK] Passed: {passed}")
        print(f"[ERROR] Failed: {failed}")
        print(f"[STATS] Success Rate: {summary['success_rate']:.1f}%")
        
        return summary
    
    def export_results(self, filename: str = "evaluation_results.json"):
        """Export evaluation results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.evaluation_results, f, indent=2)
        print(f"\n[SAVE] Results exported to {filename}")


if __name__ == "__main__":
    # Example test
    evaluator = GreenAgentEvaluator()
    
    test_scenario = {
        "id": "test_001",
        "name": "Simple ERC20 Transfer",
        "start_state": {
            "account": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "ETH_balance": 10.0,
            "USDC_balance": 5000
        },
        "operations": [
            {
                "type": "send_erc20",
                "params": {
                    "token": "USDC",
                    "to": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                    "amount": 1000
                }
            }
        ],
        "end_state": {
            "account": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "USDC_balance": 4000
        }
    }
    
    result = evaluator.evaluate_scenario(test_scenario)
    print(f"\n[COMPLETE] Final Result: {result}")
