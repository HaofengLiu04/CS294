# Quick Start Guide - DeFi Agent Evaluation

## [START] Get Running in 5 Minutes

### Step 1: Install Foundry

```bash
# Install Foundry (Anvil)
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### Step 2: Setup Environment

```bash
cd /Users/louis/Desktop/CS294/defi_agent_eval

# Install Python dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env and add your Alchemy API key
nano .env  # or use your preferred editor
```

### Step 3: Start Anvil (Terminal 1)

```bash
# Start local blockchain fork
./scripts/setup_environment.sh

# You should see:
# Anvil running at http://127.0.0.1:8545
# 10 accounts pre-funded with 10,000 ETH each
```

Keep this terminal running!

### Step 4: Run Your First Test (Terminal 2)

```bash
cd /Users/louis/Desktop/CS294/defi_agent_eval

# Run a simple test
python3 << 'EOF'
from green_agent.core.evaluator import GreenAgentEvaluator

# Initialize evaluator
evaluator = GreenAgentEvaluator()

# Define test scenario
test = {
    "id": "quick_test",
    "name": "ERC20 Transfer Test",
    "start_state": {
        "account": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        "ETH_balance": 10.0,
        "USDC_balance": 5000
    },
    "operations": [{
        "type": "send_erc20",
        "params": {
            "token": "USDC",
            "to": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
            "amount": 1000
        }
    }],
    "end_state": {
        "account": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        "USDC_balance": 4000
    }
}

# Run evaluation
result = evaluator.evaluate_scenario(test)
print(f"\\nTest {'PASSED [OK]' if result['success'] else 'FAILED [ERROR]'}")
EOF
```

## [RESULT] Expected Output

You should see:

```
[EVAL] Evaluating Scenario: quick_test
============================================================
[INFO] Step 1: Setting up initial blockchain state...
[OK] Initial state ready

[INPUT] Step 2: Generating natural language instruction...
[INSTRUCTION] Instruction: Transfer 1000 USDC tokens to address...

[EXEC]  Step 3: Executing operations...
[DATA] Execution result: success

[VERIFY] Step 4: Verifying end state...
[RESULT] Verification: PASSED
```

## [TEST] Run Full Test Suite

```bash
python3 << 'EOF'
import json
from green_agent.core.evaluator import GreenAgentEvaluator

# Load test scenarios
with open('test_scenarios/scenarios.json', 'r') as f:
    scenarios = json.load(f)

# Run only ERC20 tests
erc20_tests = [s for s in scenarios if 'erc20' in s['id']]

evaluator = GreenAgentEvaluator()
summary = evaluator.run_test_suite(erc20_tests)

print(f"\\n{'='*60}")
print(f"Success Rate: {summary['success_rate']:.1f}%")
print(f"Passed: {summary['passed']}/{summary['total_tests']}")
EOF
```

## [DEBUG] Troubleshooting

### Anvil not found
```bash
# Make sure Foundry is in your PATH
which anvil

# If not found, run:
source ~/.bashrc  # or ~/.zshrc
foundryup
```

### Web3 import errors
```bash
# Reinstall dependencies
pip install --upgrade web3 eth-account eth-utils
```

### Connection refused
```bash
# Make sure Anvil is running in Terminal 1
# Check if port 8545 is in use:
lsof -i :8545
```

### "Repository not found" for fork
```bash
# Make sure your Alchemy API key is set in .env
# Get a free key at: https://www.alchemy.com/
```

## [OK] Next Steps

1. [OK] **Add more operations**: Uniswap swaps, DAO voting, etc.
2. [OK] **Build white agent**: Create AI agent that executes instructions
3. [OK] **Expand test suite**: Add edge cases and failure scenarios
4. [OK] **Integration testing**: Test with real LLM-based agents

## [DOCS] Additional Resources

- [Foundry Documentation](https://book.getfoundry.sh/)
- [Web3.py Documentation](https://web3py.readthedocs.io/)
- [Ethereum Mainnet Contracts](https://etherscan.io/)

---

**Need Help?** Check the main README.md or open an issue!
