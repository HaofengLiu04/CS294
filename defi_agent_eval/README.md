# DeFi Agent Evaluation Framework

Advanced framework for evaluating AI agents in blockchain and DeFi environments with real on-chain execution.

## Overview

This framework provides a comprehensive testing environment for AI agents that execute blockchain operations. It includes:

- **Green Agent**: Evaluator that generates test scenarios and verifies results
- **White Agent**: LLM-powered AI agent that interprets natural language and executes blockchain operations
- **Real Blockchain Integration**: Executes actual transactions on Anvil (local Ethereum testnet)
- **ERC20 Token Operations**: Deploy and interact with test tokens

## Architecture

### Green Agent (Evaluator)
- Generates natural language instructions
- Creates test scenarios with initial/expected states
- Verifies execution results against expectations
- Provides comprehensive evaluation metrics

### White Agent (LLM Agent)
- Interprets natural language instructions using GPT-4o
- Generates execution plans in JSON format
- Executes real blockchain transactions via Web3.py
- Returns detailed transaction results

### Blockchain Layer
- Anvil local testnet for isolated testing
- TestUSDC ERC20 token contract
- Real transaction execution with gas tracking
- Web3.py integration for smart contract interaction

## Prerequisites

- Python 3.9+
- Foundry (includes Anvil)
- OpenAI API key

## Installation

### 1. Install Foundry
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### 2. Install Python Dependencies
```bash
cd defi_agent_eval
pip install -r requirements.txt
```

### 3. Configure Environment
Create `.env` file with your OpenAI API key:
```bash
OPENAI_API_KEY=your_api_key_here
```

### 4. Start Anvil
In a separate terminal:
```bash
anvil
```

### 5. Deploy Test Token
```bash
forge create --rpc-url http://localhost:8545 \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
  src/TestUSDC.sol:TestUSDC
```

Update `configs/local_fork.json` with the deployed contract address.

## Usage

### Run Complete Evaluation
```bash
python3 run_evaluation.py
```

### Run Real Blockchain Demo
```bash
python3 demo_real_blockchain.py
```

### Run Component Tests
```bash
python3 test_components.py
```

## Project Structure

```
defi_agent_eval/
├── green_agent/           # Evaluator implementation
│   ├── core/             # Core evaluation logic
│   ├── blockchain/       # Web3 client and state management
│   └── operations/       # Operation definitions
├── white_agent/          # AI agent implementations
│   ├── llm_agent.py     # LLM-powered agent (GPT-4o)
│   ├── cli_agent.py     # CLI-based agent (Foundry cast)
│   └── code_agent.py    # Code-based agent (Web3.py)
├── src/                  # Solidity contracts
│   └── TestUSDC.sol     # ERC20 test token
├── configs/              # Configuration files
├── scripts/              # Deployment and setup scripts
└── test/                 # Test files
```

## Key Features

### Natural Language Processing
The LLM agent can interpret instructions like:
- "Send 1500 USDC to account 0x70997..."
- "Transfer two thousand USDC to the second address"

### Real Blockchain Execution
- Actual transaction signing and broadcasting
- Gas cost tracking
- Transaction confirmation and verification
- On-chain state changes

### Comprehensive Evaluation
- Success/failure detection
- Gas efficiency analysis
- Correctness verification
- Safety checks

## Example Output

```
[LLM] LLM Agent: Analyzing instruction with LLM...
[PLAN] LLM Agent: Generated plan: {
  "operation_type": "send_erc20",
  "parameters": {
    "token": "USDC",
    "to": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "amount": 1500
  }
}
[EXEC] LLM Agent: Executing plan...
[TX] Transferring 1500 USDC to 0x70997970C51812dc3A010C7d01b50e0d17dc79C8...
[SUCCESS] Transaction mined: 0x879d7a797b...
          Gas used: 52338
```

## Configuration

### Network Settings
Edit `configs/local_fork.json`:
```json
{
  "rpc_url": "http://localhost:8545",
  "chain_id": 31337,
  "contracts": {
    "USDC": "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
  }
}
```

### Test Accounts
Anvil provides test accounts with pre-funded ETH:
- Account #0: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
- Account #1: 0x70997970C51812dc3A010C7d01b50e0d17dc79C8

## Development

### Running Tests
```bash
# Unit tests
python3 test_components.py

# Integration tests
python3 test_white_agents.py

# Blockchain tests
forge test
```

### Adding New Operations
1. Define operation in `green_agent/operations/`
2. Add instruction generator in `green_agent/core/instruction_generator.py`
3. Update LLM prompt in `white_agent/llm_agent.py`

## Troubleshooting

### Anvil Connection Issues
Ensure Anvil is running on port 8545:
```bash
anvil
```

### OpenAI API Errors
Verify API key is set in `.env`:
```bash
cat .env | grep OPENAI_API_KEY
```

### Transaction Failures
Check account has sufficient funds:
```bash
cast balance 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 --rpc-url http://localhost:8545
```

## Technology Stack

- **Foundry**: Ethereum development toolkit
- **Anvil**: Local Ethereum node
- **Web3.py**: Python Ethereum library
- **OpenAI**: GPT-4o for natural language processing
- **Solidity**: Smart contract development

## License

MIT

## Contributors

UC Berkeley CS294 - AI Agents (Fall 2025)
Team A10: Mingxi Tang, Yufeng Yan, Haofeng Liu, Meixin Ma
