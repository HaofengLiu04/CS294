#!/usr/bin/env python3
"""
Demo: LLM White Agent with REAL Blockchain Transactions

This shows the agent executing actual transactions on Anvil testnet.
"""

import sys
from pathlib import Path
from web3 import Web3

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from white_agent.llm_agent import LLMWhiteAgent
from green_agent.blockchain.web3_client import BlockchainClient


# Anvil test accounts
ACCOUNT_0 = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
ACCOUNT_1 = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
ACCOUNT_2 = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
PRIVATE_KEY_0 = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"


def print_balances(client, title):
    """Print current USDC balances"""
    print(f"\n{'─' * 80}")
    print(f"[DATA] {title}")
    print(f"{'─' * 80}")
    for name, address in [("Account #0", ACCOUNT_0), ("Account #1", ACCOUNT_1), ("Account #2", ACCOUNT_2)]:
        usdc_balance = client.get_token_balance_human("USDC", address)
        print(f"{name} ({address[:10]}...): {usdc_balance:,.2f} USDC")


def main():
    print("=" * 80)
    print("[START] LLM White Agent - REAL Blockchain Transaction Demo")
    print("=" * 80)
    print("\nThis demo executes ACTUAL transactions on the Anvil blockchain!")
    print("You'll see real tx hashes, gas usage, and on-chain state changes.")
    
    # Connect to blockchain
    print("\n[CONNECT] Connecting to Anvil...")
    client = BlockchainClient()
    
    if not client.is_connected():
        print("[ERROR] Failed to connect to Anvil. Start it with: ~/.foundry/bin/anvil")
        return
    
    print(f"[OK] Connected to Anvil (Block #{client.get_block_number()})")
    
    # Mint some USDC to account #0 using the contract's mint function
    print("\n[MINT] Minting 10,000 USDC to Account #0...")
    w3 = client.w3
    usdc_address = client.get_contract_address("USDC")
    
    # Simple mint call using web3
    mint_abi = [{
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "mint",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }]
    
    usdc_contract = w3.eth.contract(address=usdc_address, abi=mint_abi)
    
    # Mint 10,000 USDC (remember: 6 decimals for USDC)
    from eth_account import Account
    account = Account.from_key(PRIVATE_KEY_0)
    
    tx = usdc_contract.functions.mint(
        ACCOUNT_0,
        10_000 * 10**6  # 10,000 USDC with 6 decimals
    ).build_transaction({
        'from': ACCOUNT_0,
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(ACCOUNT_0)
    })
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    print(f"[OK] Minted! Tx: {tx_hash.hex()[:20]}...")
    
    # Show initial balances
    print_balances(client, "Initial Balances")
    
    # Initialize LLM White Agent
    print("\n[AGENT] Initializing LLM White Agent...")
    white_agent = LLMWhiteAgent(
        rpc_url="http://localhost:8545",
        private_key=PRIVATE_KEY_0
    )
    print(f"[OK] {white_agent.name} ready (using account {ACCOUNT_0[:10]}...)")
    
    # Test 1: Natural language instruction to transfer USDC
    print("\n" + "=" * 80)
    print("[TEST] Test #1: Transfer USDC with Natural Language")
    print("=" * 80)
    
    instruction_1 = f"Send 1500 USDC to {ACCOUNT_1}"
    context_1 = {
        "tokens": ["USDC"],
        "current_balance": {"USDC": 10000}
    }
    
    print(f"\n[INPUT] Instruction: \"{instruction_1}\"")
    print(f"[LLM] Sending to OpenAI GPT-4 for interpretation...")
    
    result_1 = white_agent.execute_instruction(instruction_1, context_1)
    
    if result_1.success:
        print(f"\n[OK] Transaction Successful!")
        print(f"   Tx Hash: {result_1.transaction_hash}")
        print(f"   Gas Used: {result_1.metadata.get('gas_used', 'N/A')}")
        print(f"   Time: {result_1.execution_time:.2f}s")
    else:
        print(f"\n[ERROR] Transaction Failed: {result_1.error}")
    
    # Show updated balances
    print_balances(client, "After Transfer #1")
    
    # Test 2: Another transfer with different phrasing
    print("\n" + "=" * 80)
    print("[TEST] Test #2: Another Transfer with Different Phrasing")
    print("=" * 80)
    
    instruction_2 = f"Transfer two thousand USDC tokens to wallet {ACCOUNT_2}"
    context_2 = {
        "tokens": ["USDC"],
        "current_balance": {"USDC": 8500}
    }
    
    print(f"\n[INPUT] Instruction: \"{instruction_2}\"")
    print(f"[LLM] Interpreting with LLM...")
    
    result_2 = white_agent.execute_instruction(instruction_2, context_2)
    
    if result_2.success:
        print(f"\n[OK] Transaction Successful!")
        print(f"   Tx Hash: {result_2.transaction_hash}")
        print(f"   Gas Used: {result_2.metadata.get('gas_used', 'N/A')}")
        print(f"   Time: {result_2.execution_time:.2f}s")
    else:
        print(f"\n[ERROR] Transaction Failed: {result_2.error}")
    
    # Show final balances
    print_balances(client, "Final Balances")
    
    # Summary
    print("\n" + "=" * 80)
    print("[COMPLETE] Demo Complete!")
    print("=" * 80)
    print("\n[RESULT] What happened:")
    print("   1. LLM interpreted natural language instructions")
    print("   2. Generated structured execution plans (JSON)")
    print("   3. Executed REAL transactions on Anvil blockchain")
    print("   4. Balances changed on-chain, verifiable via Web3")
    print("\n[NOTE] Key Insight:")
    print("   This is AI + Blockchain working together - the LLM provides")
    print("   intelligent understanding, while blockchain provides trustless execution.")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
