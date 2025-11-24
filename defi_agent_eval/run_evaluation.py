#!/usr/bin/env python3
"""
Runner script to execute the DeFi Agent Evaluation with LLM White Agent

This script:
1. Initializes the Green Agent Evaluator
2. Creates an LLM White Agent powered by OpenAI
3. Runs a test scenario
4. Displays results

Prerequisites:
- Anvil must be running on localhost:8545
- OpenAI API key must be set in .env file
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from green_agent.core.evaluator import GreenAgentEvaluator
from white_agent.llm_agent import LLMWhiteAgent


def main():
    print("=" * 80)
    print("[START] DeFi Agent Evaluation - LLM White Agent Test")
    print("=" * 80)
    
    # Check if Anvil is running
    print("\n⚠️  Prerequisites:")
    print("   1. Anvil must be running on http://localhost:8545")
    print("   2. OpenAI API key must be set in .env file")
    print("\nTo start Anvil, run in a separate terminal:")
    print("   anvil")
    print("\n" + "=" * 80)
    
    # Auto-proceed (comment this out if you want manual confirmation)
    # input("\nPress Enter to continue...")
    print("\n▶️  Auto-starting evaluation...\n")
    
    # Initialize Green Agent Evaluator
    print("\n[INFO] Initializing Green Agent Evaluator...")
    evaluator = GreenAgentEvaluator()
    
    # Initialize LLM White Agent
    print("[AGENT] Initializing LLM White Agent...")
    # Using Anvil's default account #0 private key
    white_agent = LLMWhiteAgent(
        rpc_url="http://localhost:8545",
        private_key="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    )
    print(f"[OK] White Agent initialized: {white_agent.name}")
    
    # Define test scenario
    test_scenario = {
        "id": "test_llm_erc20_transfer",
        "name": "ERC20 Transfer via LLM White Agent",
        "start_state": {
            "account": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",  # Anvil account #0
            "ETH_balance": 10.0,
            "USDC_balance": 5000
        },
        "operations": [
            {
                "type": "send_erc20",
                "params": {
                    "token": "USDC",
                    "to": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",  # Anvil account #1
                    "amount": 1000
                }
            }
        ],
        "end_state": {
            "account": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "USDC_balance": 4000
        }
    }
    
    print(f"\n📝 Test Scenario: {test_scenario['name']}")
    print(f"   Scenario ID: {test_scenario['id']}")
    
    # Run evaluation
    result = evaluator.evaluate_with_white_agent(test_scenario, white_agent)
    
    # Display results
    print("\n" + "=" * 80)
    print("[DATA] EVALUATION RESULTS")
    print("=" * 80)
    
    if 'error' in result:
        print(f"[ERROR] Evaluation Failed:")
        print(f"   Error: {result['error']}")
    else:
        print(f"Scenario: {result.get('scenario_name', 'Unknown')}")
        print(f"Success: {'[OK] PASSED' if result.get('success') else '[ERROR] FAILED'}")
        print(f"\nInstruction given to agent:")
        print(f"   {result.get('instruction', 'N/A')}")
        
        if 'white_agent_result' in result:
            print(f"\nWhite Agent Execution:")
            print(f"   Success: {result['white_agent_result']['success']}")
            print(f"   TX Hash: {result['white_agent_result']['transaction_hash']}")
            if result['white_agent_result'].get('metadata'):
                print(f"   Note: {result['white_agent_result']['metadata'].get('note', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("[COMPLETE] Evaluation Complete!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Evaluation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
