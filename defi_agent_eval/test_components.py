"""
Test script to verify the Green Agent framework works
This version doesn't require Anvil - just tests the core logic
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_instruction_generator():
    """Test instruction generation without blockchain"""
    print("[TEST] Testing Instruction Generator...")
    print("=" * 60)
    
    from green_agent.core.instruction_generator import InstructionGenerator
    
    generator = InstructionGenerator()
    
    test_scenario = {
        "id": "test_001",
        "start_state": {
            "account": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "ETH_balance": 10.0,
            "USDC_balance": 5000
        },
        "operations": [
            {
                "type": "swap_uniswap",
                "params": {
                    "from_token": "ETH",
                    "to_token": "USDC",
                    "amount": 1.0,
                    "slippage_tolerance": 0.5
                }
            }
        ],
        "end_state": {
            "ETH_balance": 9.0,
            "USDC_balance": 7000
        }
    }
    
    instruction = generator.generate_with_context(test_scenario)
    print(instruction)
    print("\n[OK] Instruction Generator: PASSED")
    return True

def test_cli_code_generation():
    """Test CLI command and Python code generation"""
    print("\n[TEST] Testing CLI/Code Generation...")
    print("=" * 60)
    
    # Mock blockchain client for testing
    class MockClient:
        def __init__(self):
            self.accounts = {
                'deployer': '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'
            }
            self.config = {
                "contracts": {
                    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
                }
            }
            # Mock w3 object
            self.w3 = None
        
        def get_contract_address(self, name):
            return self.config["contracts"].get(name, "")
        
        def _get_erc20_abi(self):
            return []
        
        def _get_token_decimals(self, token_name: str) -> int:
            """Mock method for token decimals"""
            return 6 if token_name == "USDC" else 18
    
    from green_agent.operations.erc20_transfer import ERC20Transfer
    
    client = MockClient()
    erc20 = ERC20Transfer(client)
    
    params = {
        "token": "USDC",
        "to": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        "amount": 1000
    }
    
    # Generate CLI command
    print("\n📝 Generated CLI Command:")
    print("-" * 60)
    cli_cmd = erc20.generate_cli_command(params, client.accounts['deployer'])
    print(cli_cmd)
    
    # Generate Python code
    print("\n📝 Generated Python Code:")
    print("-" * 60)
    python_code = erc20.generate_python_code(params, client.accounts['deployer'])
    print(python_code[:300] + "...")
    
    print("\n[OK] CLI/Code Generation: PASSED")
    return True

def check_requirements():
    """Check what's installed and what's needed"""
    print("\n🔍 Checking Requirements...")
    print("=" * 60)
    
    requirements = {
        "web3": "[OK] Installed",
        "eth_account": "[OK] Installed", 
        "python-dotenv": "[OK] Installed"
    }
    
    missing = []
    
    try:
        import web3
        print(f"[OK] web3: {web3.__version__}")
    except ImportError:
        requirements["web3"] = "[ERROR] Missing"
        missing.append("web3")
    
    try:
        import eth_account
        print(f"[OK] eth_account: installed")
    except ImportError:
        requirements["eth_account"] = "[ERROR] Missing"
        missing.append("eth-account")
    
    try:
        import dotenv
        print(f"[OK] python-dotenv: installed")
    except ImportError:
        requirements["python-dotenv"] = "[ERROR] Missing"
        missing.append("python-dotenv")
    
    # Check Anvil
    import subprocess
    try:
        result = subprocess.run(['which', 'anvil'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] Anvil (Foundry): installed at {result.stdout.strip()}")
        else:
            print(f"⚠️  Anvil: Not installed (needed for full blockchain testing)")
            print(f"   Install: curl -L https://foundry.paradigm.xyz | bash && foundryup")
    except Exception:
        print(f"⚠️  Anvil: Not installed")
    
    if missing:
        print(f"\n[ERROR] Missing packages: {', '.join(missing)}")
        print(f"   Install: pip install {' '.join(missing)}")
        return False
    
    return True

def main():
    print("[START] DeFi Agent Evaluation Framework - Component Test")
    print("=" * 80)
    
    # Check requirements
    all_installed = check_requirements()
    
    if not all_installed:
        print("\n⚠️  Some dependencies are missing. Install them first.")
        return
    
    try:
        # Test 1: Instruction generation
        test_instruction_generator()
        
        # Test 2: CLI/Code generation
        test_cli_code_generation()
        
        print("\n" + "=" * 80)
        print("[SUCCESS] ALL COMPONENT TESTS PASSED!")
        print("=" * 80)
        print("\n📝 Next Steps:")
        print("1. Install Anvil: curl -L https://foundry.paradigm.xyz | bash && foundryup")
        print("2. Start Anvil: ./scripts/setup_environment.sh")
        print("3. Run full evaluation: python -m green_agent.core.evaluator")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
