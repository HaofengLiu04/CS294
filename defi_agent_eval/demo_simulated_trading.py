#!/usr/bin/env python3
"""
Demo: AI Agent Reading Simulated Blockchain

This demonstrates an AI agent that:
1. Reads YOUR simulated blockchain state (balances, tokens, prices)
2. Uses LLM (GPT-4, DeepSeek, Claude) to analyze that state
3. Makes autonomous trading decisions based on blockchain data
4. Executes decisions on YOUR simulated blockchain
5. Green agent evaluates the execution

Everything happens in your controlled simulated environment.
NO connection to real exchanges or real money.

Prerequisites:
[Anvil - Simulated Blockchain]
1. Start: anvil
2. Deploy contracts: forge script script/DeployTestUSDC.s.sol --broadcast --rpc-url http://localhost:8545
3. Fund accounts with test tokens

[LLM API]
4. Set OPENAI_API_KEY in .env file
   (Or configure DeepSeek/Claude API if preferred)
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from white_agent.nofx_agent import NoFxStyleAgent
from green_agent.core.evaluator import GreenAgentEvaluator

load_dotenv()


def main():
    print("=" * 80)
    print("[START] AI Agent Reading Simulated Blockchain Demo")
    print("         (LLM analyzes YOUR blockchain → Makes decisions → Executes)")
    print("=" * 80)
    
    # Get private key for blockchain transactions
    private_key = os.getenv("ANVIL_PRIVATE_KEY")
    if not private_key:
        print("[ERROR] ANVIL_PRIVATE_KEY not found in .env file")
        print("[HELP] Add: ANVIL_PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80")
        return
    
    # Initialize AI agent that reads simulated blockchain
    print("\n[INIT] Initializing AI agent...")
    
    try:
        ai_agent = NoFxStyleAgent(
            rpc_url="http://localhost:8545",  # YOUR Anvil testnet
            private_key=private_key,
            model="gpt-4o",  # Can also use: gpt-4, deepseek, claude, etc.
            name="Blockchain AI Agent"
        )
        print(f"[OK] AI Agent: {ai_agent.name}")
        print(f"[OK] Blockchain: {ai_agent.w3.provider.endpoint_uri}")
        print(f"[OK] Account: {ai_agent.account_address}")
        print(f"[OK] LLM Model: {ai_agent.model}")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        print("\n[HELP] Make sure:")
        print("  1. Anvil is running: anvil")
        print("  2. OPENAI_API_KEY is set in .env")
        return
    
    # Initialize Green Agent Evaluator
    print("\n[INFO] Initializing Green Agent Evaluator...")
    evaluator = GreenAgentEvaluator()
    
    # Define test scenario
    # AI will read blockchain state and make autonomous decision
    test_scenario = {
        "id": "test_ai_blockchain_analysis",
        "name": "AI Blockchain Analysis Evaluation",
        "description": "AI reads simulated blockchain state and makes trading decision",
        "start_state": {
            "account": ai_agent.account_address,
            "recipient": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",  # Anvil account #1
            "available_tokens": ["USDC"],  # Tokens to check balances for
            "note": "AI analyzes YOUR blockchain, not real markets"
        },
        "operations": [
            {
                "type": "ai_autonomous_decision",
                "instruction": "Analyze my blockchain account state and decide whether to transfer tokens",
                "params": {
                    "decision_criteria": "Based on current balances and blockchain state",
                    "amount": 100  # Suggested amount if transferring
                }
            }
        ],
        "expected_behavior": {
            "reads_blockchain": True,
            "uses_ai_reasoning": True,
            "executes_on_blockchain": True
        }
    }
    
    print(f"\n[SCENARIO] {test_scenario['name']}")
    print(f"   Description: {test_scenario['description']}")
    print(f"   Architecture: Simulated Blockchain → AI Analysis → Decision → Execution")
    
    # Run evaluation
    print(f"\n[EVAL] Starting AI blockchain analysis...")
    print(f"[STEP 1] AI will read blockchain state (balances, tokens, etc.)")
    print(f"[STEP 2] LLM will analyze and make decision")
    print(f"[STEP 3] Decision will be executed on blockchain")
    print(f"[STEP 4] Green agent will evaluate the execution")
    
    # Build context with recipient address and available tokens
    context = {
        'recipient_address': test_scenario['start_state']['recipient'],
        'available_tokens': test_scenario['start_state']['available_tokens'],
        'amount': test_scenario['operations'][0]['params']['amount'],
        'initial_state': test_scenario['start_state']
    }
    
    result = evaluator.evaluate_with_white_agent(test_scenario, ai_agent)
    
    # Display results
    print("\n" + "=" * 80)
    print("[RESULTS] Hybrid Evaluation Complete")
    print("=" * 80)
    
    # Display results
    print("\n" + "=" * 80)
    print("[RESULTS] AI Blockchain Analysis Complete")
    print("=" * 80)
    
    if 'error' in result:
        print(f"[ERROR] Evaluation Failed:")
        print(f"   Error: {result['error']}")
    else:
        print(f"Scenario: {result.get('scenario_name', 'Unknown')}")
        print(f"Success: {'[OK] PASSED' if result.get('success') else '[ERROR] FAILED'}")
        
        if 'white_agent_result' in result:
            agent_result = result['white_agent_result']
            print(f"\n[EXECUTION]")
            print(f"   Success: {agent_result['success']}")
            
            if agent_result.get('transaction_hash'):
                print(f"   Blockchain TX: {agent_result['transaction_hash']}")
                print(f"   Gas Used: {agent_result.get('gas_used', 'N/A')}")
            
            if agent_result.get('metadata'):
                metadata = agent_result['metadata']
                
                # Show blockchain state that AI analyzed
                if metadata.get('blockchain_state'):
                    bc_state = metadata['blockchain_state']
                    print(f"\n[BLOCKCHAIN STATE] What AI Analyzed:")
                    print(f"   Account: {bc_state.get('account')}")
                    print(f"   ETH Balance: {bc_state.get('eth_balance')} ETH")
                    print(f"   Block: #{bc_state.get('block_number')}")
                    for token, balance in bc_state.get('token_balances', {}).items():
                        print(f"   {token}: {balance}")
                
                # Show AI's decision
                if metadata.get('decision'):
                    decision = metadata['decision']
                    print(f"\n[AI DECISION]")
                    print(f"   Action: {decision.get('action')}")
                    if decision.get('parameters'):
                        params = decision['parameters']
                        print(f"   Token: {params.get('token', 'N/A')}")
                        print(f"   Amount: {params.get('amount', 'N/A')}")
                        print(f"   To: {params.get('to', 'N/A')}")
                    
                    if decision.get('reasoning'):
                        print(f"\n[AI REASONING]:")
                        reasoning = decision['reasoning']
                        if len(reasoning) > 300:
                            print(f"   {reasoning[:300]}...")
                            print(f"   (+ {len(reasoning) - 300} more characters)")
                        else:
                            print(f"   {reasoning}")
    
    print("\n" + "=" * 80)
    print("[COMPLETE] Demo Finished!")
    print("=" * 80)
    print(f"\n[SUMMARY]")
    print(f"   - AI read simulated blockchain state (YOUR balances)")
    print(f"   - LLM analyzed and made autonomous decision")
    print(f"   - Decision executed on YOUR testnet")
    print(f"   - Green agent evaluated the execution")
    print(f"\n   Everything happened in YOUR controlled environment!")
    print(f"   No real money. No real exchanges. Just AI + simulated blockchain.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Demo cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
