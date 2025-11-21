# White Agent Architecture

White agents are AI agents that receive natural language instructions and execute blockchain operations. They are the agents being **evaluated** by the green agent for correctness, safety, and efficiency.

## Types of White Agents

### 1. CLI White Agent (`cli_agent.py`)
- **Execution Method**: Foundry `cast` commands
- **Use Case**: Direct blockchain interaction via CLI
- **How it works**:
  1. Receives natural language instruction
  2. Gets pre-generated `cast` command from context
  3. Executes via subprocess
  4. Parses transaction hash from output

**Example**:
```python
from white_agent import CLIWhiteAgent

agent = CLIWhiteAgent(rpc_url="http://localhost:8545")

instruction = "Transfer 1000 USDC to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
context = {
    'cli_command': 'cast send 0xA0b86991... "transfer(address,uint256)" ...'
}

result = agent.execute_instruction(instruction, context)
print(f"Success: {result.success}, TX: {result.transaction_hash}")
```

### 2. Code White Agent (`code_agent.py`)
- **Execution Method**: Web3.py Python code
- **Use Case**: Programmatic blockchain interaction
- **How it works**:
  1. Receives natural language instruction
  2. Gets pre-generated Web3.py code from context
  3. Executes code with `exec()`
  4. Waits for transaction receipt

**Example**:
```python
from white_agent import CodeWhiteAgent

agent = CodeWhiteAgent(
    rpc_url="http://localhost:8545",
    private_key="0xac09..."
)

instruction = "Transfer 1000 USDC to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
context = {
    'python_code': '''
contract = w3.eth.contract(address=token_address, abi=erc20_abi)
tx = contract.functions.transfer(recipient, amount).build_transaction({...})
signed_tx = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
result = tx_hash
'''
}

result = agent.execute_instruction(instruction, context)
print(f"Success: {result.success}, Gas Used: {result.gas_used}")
```

### 3. LLM White Agent (`llm_agent.py`)
- **Execution Method**: Autonomous LLM interpretation
- **Use Case**: Fully autonomous AI agent
- **How it works**:
  1. Receives natural language instruction
  2. Uses LLM to understand and plan execution
  3. Generates appropriate blockchain operations
  4. Executes and verifies

**Example**:
```python
from white_agent import LLMWhiteAgent

agent = LLMWhiteAgent(
    rpc_url="http://localhost:8545",
    private_key="0xac09...",
    llm_api_key="sk-..."  # OpenAI/Anthropic API key
)

instruction = "Transfer 1000 USDC to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
context = {
    'initial_balances': {'USDC': 10000000000}
}

# Agent autonomously interprets and executes
result = agent.execute_instruction(instruction, context)
```

**Note**: LLM agent is currently a template. Full implementation requires:
- Integration with LLM API (OpenAI GPT-4, Anthropic Claude, etc.)
- Structured prompt engineering for DeFi operations
- Safety validation of LLM-generated code

## Base Interface

All white agents inherit from `WhiteAgent` base class:

```python
from white_agent.base_agent import WhiteAgent, ExecutionResult

class MyCustomAgent(WhiteAgent):
    def execute_instruction(self, instruction: str, context: Dict[str, Any]) -> ExecutionResult:
        # Your implementation
        return ExecutionResult(
            success=True,
            transaction_hash="0x...",
            gas_used=50000,
            execution_time=2.5
        )
```

## ExecutionResult

All agents return an `ExecutionResult` with:
- `success`: Boolean indicating if execution succeeded
- `transaction_hash`: Transaction hash (if applicable)
- `error`: Error message (if failed)
- `gas_used`: Gas consumed by transaction
- `execution_time`: Time taken to execute
- `metadata`: Additional execution details

## Integration with Green Agent

White agents are evaluated by the green agent in the following flow:

```
1. Green Agent creates test scenario with <start_state, operations, end_state>
2. Green Agent generates natural language instruction
3. Green Agent generates CLI command OR Python code for the operation
4. White Agent receives instruction + context (with CLI/code)
5. White Agent executes the instruction
6. Green Agent verifies end state matches expected state
7. Green Agent scores: correctness, safety, efficiency
```

## Testing

Run the simple demo:
```bash
python3 test_white_agents_simple.py
```

Run with full blockchain (requires Anvil):
```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Start Anvil fork
anvil --fork-url https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY

# Run full test
python3 test_white_agents.py
```

## Files

- `base_agent.py` - Abstract base class and ExecutionResult dataclass
- `cli_agent.py` - CLI-based agent using Foundry cast
- `code_agent.py` - Code-based agent using Web3.py
- `llm_agent.py` - LLM-based autonomous agent (template)
- `__init__.py` - Package exports

## Next Steps

1. Install Foundry/Anvil for real blockchain testing
2. Implement remaining DeFi operations (Uniswap, DAO, lending, bridging)
3. Integrate LLM agent with real API (GPT-4, Claude, etc.)
4. Build comprehensive test suite with various scenarios
5. Create demo video showing green agent evaluating white agents
