#!/usr/bin/env python3
"""
Simple demo showing the LLM White Agent in action

This demonstrates the core capability: using OpenAI to interpret
natural language instructions and convert them to structured execution plans.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from white_agent.llm_agent import LLMWhiteAgent


def main():
    print("=" * 80)
    print("[LLM] LLM White Agent - Natural Language Understanding Demo")
    print("=" * 80)
    print("\nThis demo shows how the LLM White Agent uses OpenAI to understand")
    print("natural language instructions and convert them into structured plans.")
    print("\n" + "=" * 80)
    
    # Initialize LLM White Agent
    print("\n[AGENT] Initializing LLM White Agent...")
    white_agent = LLMWhiteAgent(
        rpc_url="http://localhost:8545",
        private_key="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    )
    print(f"[OK] {white_agent.name} initialized and ready!")
    
    # Test scenarios with different natural language instructions
    test_instructions = [
        {
            "instruction": "Transfer 1000 USDC tokens to address 0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
            "context": {
                "tokens": ["USDC", "ETH"],
                "current_balance": {"USDC": 5000, "ETH": 10}
            }
        },
        {
            "instruction": "Send 500 USDC to 0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
            "context": {
                "tokens": ["USDC"],
                "current_balance": {"USDC": 2000}
            }
        },
        {
            "instruction": "Please transfer two thousand USDC tokens to wallet 0x90F79bf6EB2c4f870365E785982E1f101E93b906",
            "context": {
                "tokens": ["USDC", "DAI"],
                "current_balance": {"USDC": 5000, "DAI": 3000}
            }
        }
    ]
    
    print("\n" + "=" * 80)
    print("[RESULT] Running Test Scenarios")
    print("=" * 80)
    
    for i, test in enumerate(test_instructions, 1):
        print(f"\n{'─' * 80}")
        print(f"📝 Test #{i}")
        print(f"{'─' * 80}")
        print(f"\n[INPUT] Natural Language Instruction:")
        print(f'   "{test["instruction"]}"')
        print(f"\n[DATA] Context:")
        print(f"   Available Tokens: {test['context']['tokens']}")
        print(f"   Current Balance: {test['context']['current_balance']}")
        
        print(f"\n[LLM] Sending to OpenAI for interpretation...")
        result = white_agent.execute_instruction(test["instruction"], test["context"])
        
        print(f"\n[OK] Result:")
        print(f"   Success: {result.success}")
        if result.success:
            print(f"   Transaction Hash: {result.transaction_hash}")
            if result.metadata and 'plan' in result.metadata:
                plan = result.metadata['plan']
                print(f"\n[INFO] LLM Generated Plan:")
                print(f"   Operation Type: {plan.get('operation_type', 'N/A')}")
                if 'parameters' in plan:
                    print(f"   Parameters:")
                    for key, value in plan['parameters'].items():
                        print(f"      - {key}: {value}")
        else:
            print(f"   Error: {result.error}")
        
        print(f"   Execution Time: {result.execution_time:.3f}s")
    
    print("\n" + "=" * 80)
    print("[COMPLETE] Demo Complete!")
    print("=" * 80)
    print("\n[NOTE] Key Takeaway:")
    print("   The LLM White Agent successfully used OpenAI (GPT-4) to:")
    print("   1. Understand natural language instructions")
    print("   2. Extract key parameters (token, amount, recipient)")
    print("   3. Generate structured execution plans")
    print("\n   This demonstrates the core AI capability - the actual blockchain")
    print("   transaction execution would be the next step in a production system.")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
