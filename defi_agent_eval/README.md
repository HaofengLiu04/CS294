# DeFi Agent Evaluation Framework

**CS294 - A10 Team** | Green Agent for On-Chain DeFi Operations Testing

## 🎯 Project Overview

This framework implements a **Green Agent** that evaluates whether AI agents (White Agents) can successfully conduct on-chain DeFi operations. The Green Agent:

1. ✅ **Sets up test environments** with specific blockchain states
2. ✅ **Generates natural language instructions** from operation specifications  
3. ✅ **Executes operations** via CLI tools or generated code
4. ✅ **Verifies end states** to confirm correct execution

## 🏗️ Architecture

```
Green Agent Flow:
┌─────────────────────────────────────────────────────────────┐
│ 1. Environment Setup                                         │
│    - Deploy contracts, fund accounts, set initial state     │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Instruction Generation                                    │
│    - Convert <start, operations, end> → natural language    │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. White Agent Execution                                     │
│    - Receives NL instructions                                │
│    - Generates CLI commands or Python code                   │
│    - Executes on-chain operations                            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. State Verification                                        │
│    - Check actual vs expected end state                      │
│    - Verify balances, approvals, state changes               │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- [Foundry](https://getfoundry.sh/) (for Anvil local blockchain)
- Alchemy API key (for mainnet forking)

### Installation

```bash
# 1. Clone and navigate to project
cd /Users/louis/Desktop/CS294/defi_agent_eval

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your ALCHEMY_API_KEY

# 4. Install Foundry and start Anvil
./scripts/setup_environment.sh
```

This will start Anvil (local Ethereum fork) at `http://127.0.0.1:8545`

### Running Tests

```bash
# In a new terminal (keep Anvil running)
cd /Users/louis/Desktop/CS294/defi_agent_eval

# Run evaluation
python -m green_agent.core.evaluator
```

## 📋 Supported Operations

### 1. **Send ERC20 Tokens**
Transfer tokens (USDC, DAI, WETH) between accounts

### 2. **Swap (Uniswap)**
Token swaps via Uniswap V2/V3 DEX

### 3. **DAO Voting**
Participate in governance votes

### 4. **Lending (1inch)**
Supply, borrow, withdraw, repay in lending protocols

### 5. **Bridging (Rollups)**
Cross-chain asset transfers to L2s

## 🔬 Test Scenarios

Test scenarios are defined in `test_scenarios/scenarios.json`:

```json
{
  "id": "test_erc20_001",
  "name": "Simple USDC Transfer",
  "start_state": {
    "account": "0xf39...",
    "ETH_balance": 10.0,
    "USDC_balance": 5000
  },
  "operations": [{
    "type": "send_erc20",
    "params": {
      "token": "USDC",
      "to": "0x7099...",
      "amount": 1000
    }
  }],
  "end_state": {
    "account": "0xf39...",
    "USDC_balance": 4000
  }
}
```

## 🛠️ Project Structure

```
defi_agent_eval/
├── green_agent/              # Green agent implementation
│   ├── core/
│   │   ├── evaluator.py           # Main orchestrator
│   │   └── instruction_generator.py  # NL instruction gen
│   ├── blockchain/
│   │   ├── web3_client.py         # Blockchain connection
│   │   └── state_manager.py       # State setup & verification
│   └── operations/
│       └── erc20_transfer.py      # ERC20 operations
│
├── white_agent/              # White agent (agent being tested)
├── test_scenarios/           # Test case definitions
│   └── scenarios.json
├── configs/                  # Configuration files
│   └── local_fork.json
└── scripts/                  # Utility scripts
    └── setup_environment.sh
```

## 🧪 How It Works

### Step 1: Environment Setup
```python
# Green agent sets up initial blockchain state
state_manager.setup_initial_state({
    "account": "0xf39...",
    "ETH_balance": 10.0,
    "USDC_balance": 5000
})
```

### Step 2: Generate Instructions
```python
# Converts operation spec to natural language
instruction = instruction_generator.generate_instruction(test_scenario)
# Output: "Transfer 1000 USDC tokens to address 0x7099..."
```

### Step 3: White Agent Executes
The white agent receives the instruction and can execute via:

**Option A: CLI Tools (Foundry Cast)**
```bash
cast send 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 \
  "transfer(address,uint256)" \
  0x70997970C51812dc3A010C7d01b50e0d17dc79C8 \
  1000000000 \
  --from 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 \
  --rpc-url http://127.0.0.1:8545
```

**Option B: Generated Python Code**
```python
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
# ... execute transaction
```

### Step 4: Verify State
```python
# Green agent checks if end state matches expected
verification = state_manager.verify_end_state(account, expected_state)
# Returns: {"success": True, "matches": {...}, "current_state": {...}}
```

## 📊 Evaluation Output

```
🔬 Evaluating Scenario: test_erc20_001
============================================================
📋 Step 1: Setting up initial blockchain state...
✅ Initial state ready: {'ETH_balance': 10.0, 'USDC_balance': 5000.0}

💬 Step 2: Generating natural language instruction...
📝 Instruction:
Transfer 1000 USDC tokens to address 0x7099...

⚙️  Step 3: Executing operations...
📊 Execution result: {'operations_executed': 1, 'results': [...]}

✓ Step 4: Verifying end state...
🎯 Verification: PASSED
   Matches: {'USDC_balance': True}
   Current: {'USDC_balance': 4000.0}
   Expected: {'USDC_balance': 4000}
```

## 🔑 Key Features

- ✅ **Local Blockchain Fork**: Test on mainnet state without costs
- ✅ **Realistic Testing**: Actual contract interactions, not simulations
- ✅ **Multi-Modal Execution**: Support for both CLI and code generation
- ✅ **State Verification**: Automated checking of blockchain state changes
- ✅ **Natural Language**: Convert operations to human-readable instructions
- ✅ **Comprehensive Coverage**: All 5 reference DeFi operations

## 🧑‍💻 Team

**A10 Team - CS294**
- Mingxi Tang: Environment & Infrastructure
- Yufeng Yan: Test Case Design & Validation
- Haofeng Liu: Green Agent Core Logic
- Meixin Ma: Evaluation Metrics & Analysis

## 📝 License

MIT License - CS294 Course Project

---

**Status**: ✅ Step 1-4 Complete | 🚧 White Agent Integration In Progress
