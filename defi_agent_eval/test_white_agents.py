"""
Test script for white agents

Demonstrates how different white agents execute instructions.
"""

import sys
sys.path.insert(0, '/Users/louis/Desktop/CS294/defi_agent_eval')

from white_agent import CLIWhiteAgent, CodeWhiteAgent, LLMWhiteAgent


def test_cli_agent():
    """Test CLI-based white agent"""
    print("=" * 60)
    print("Testing CLI White Agent")
    print("=" * 60)
    
    agent = CLIWhiteAgent(rpc_url="http://localhost:8545")
    
    # Example instruction
    instruction = "Transfer 1000 USDC tokens to address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
    
    # Context includes the pre-generated CLI command
    context = {
        'cli_command': 'cast send 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 "transfer(address,uint256)" 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1 1000000000 --rpc-url http://localhost:8545 --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80'
    }
    
    print(f"\nAgent: {agent.name}")
    print(f"Instruction: {instruction}")
    print(f"\nGenerated CLI Command:")
    print(f"  {context['cli_command'][:80]}...")
    
    # Note: This will fail without Anvil running, but shows the flow
    result = agent.execute_instruction(instruction, context)
    
    print(f"\nExecution Result:")
    print(f"  Success: {result.success}")
    if result.error:
        print(f"  Error: {result.error}")
        print(f"  (This is expected without Anvil running)")
    if result.transaction_hash:
        print(f"  Transaction Hash: {result.transaction_hash}")
    print(f"  Execution Time: {result.execution_time:.3f}s")


def test_code_agent():
    """Test code-based white agent"""
    print("\n" + "=" * 60)
    print("Testing Code White Agent")
    print("=" * 60)
    
    agent = CodeWhiteAgent(
        rpc_url="http://localhost:8545",
        private_key="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    )
    
    # Example instruction
    instruction = "Transfer 1000 USDC tokens to address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
    
    # Context includes the pre-generated Python code
    context = {
        'python_code': """
# Transfer ERC20 tokens
token_address = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
recipient = '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1'
amount = 1000000000

# ERC20 ABI (transfer function only)
erc20_abi = [{"inputs":[{"name":"recipient","type":"address"},{"name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}]

# Create contract instance
contract = w3.eth.contract(address=token_address, abi=erc20_abi)

# Build transaction
tx = contract.functions.transfer(recipient, amount).build_transaction({
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address),
    'gas': 100000,
    'gasPrice': w3.eth.gas_price
})

# Sign and send
signed_tx = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
result = tx_hash
"""
    }
    
    print(f"\nAgent: {agent.name}")
    print(f"Instruction: {instruction}")
    print(f"\nGenerated Python Code:")
    print(f"  {context['python_code'][:100].strip()}...")
    
    # Note: This will fail without Anvil running, but shows the flow
    result = agent.execute_instruction(instruction, context)
    
    print(f"\nExecution Result:")
    print(f"  Success: {result.success}")
    if result.error:
        print(f"  Error: {result.error}")
        print(f"  (This is expected without Anvil running)")
    if result.transaction_hash:
        print(f"  Transaction Hash: {result.transaction_hash}")
    print(f"  Execution Time: {result.execution_time:.3f}s")


def test_llm_agent():
    """Test LLM-based white agent"""
    print("\n" + "=" * 60)
    print("Testing LLM White Agent")
    print("=" * 60)
    
    agent = LLMWhiteAgent(
        rpc_url="http://localhost:8545",
        private_key="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    )
    
    # Example instruction
    instruction = "Transfer 1000 USDC tokens to address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
    
    # Context with initial state
    context = {
        'tokens': ['USDC', 'USDT', 'DAI'],
        'initial_balances': {
            'USDC': 10000000000,
            'USDT': 5000000000,
            'DAI': 2000000000000000000000
        }
    }
    
    print(f"\nAgent: {agent.name}")
    print(f"Instruction: {instruction}")
    print(f"Context: {context}")
    
    result = agent.execute_instruction(instruction, context)
    
    print(f"\nExecution Result:")
    print(f"  Success: {result.success}")
    if result.error:
        print(f"  Error: {result.error}")
    if result.transaction_hash:
        print(f"  Transaction Hash: {result.transaction_hash}")
    if result.metadata:
        print(f"  Note: {result.metadata.get('note', '')}")
    print(f"  Execution Time: {result.execution_time:.3f}s")


def main():
    print("\n[AGENT] White Agent Testing Suite\n")
    
    print("This demonstrates three types of white agents:")
    print("1. CLI Agent - Executes via Foundry cast commands")
    print("2. Code Agent - Executes via Web3.py Python code")
    print("3. LLM Agent - Autonomously interprets and executes (mock)")
    
    try:
        test_cli_agent()
        test_code_agent()
        test_llm_agent()
        
        print("\n" + "=" * 60)
        print("[OK] All white agent types demonstrated!")
        print("=" * 60)
        print("\nNote: Actual execution requires Anvil running.")
        print("Install Foundry and run: anvil --fork-url <ALCHEMY_URL>")
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
