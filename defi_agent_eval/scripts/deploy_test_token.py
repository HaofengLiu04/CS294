#!/usr/bin/env python3
"""
Deploy a simple ERC20 test token to Anvil for testing
"""

import sys
from pathlib import Path
from web3 import Web3
from eth_account import Account

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Anvil default account #0
DEPLOYER_ADDRESS = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
DEPLOYER_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

# Simple ERC20 contract bytecode (OpenZeppelin-like)
# This is a pre-compiled minimal ERC20 with name="TestUSDC", symbol="USDC", decimals=6
ERC20_BYTECODE = "0x608060405234801561001057600080fd5b506040518060400160405280600881526020017f5465737455534443000000000000000000000000000000000000000000000000815250604051806040016040528060048152602001635553444360e01b81525060068260039081610075919061025e565b506004610082828261025e565b50505050600061009661009c60201b60201c565b5061031d565b601290565b634e487b7160e01b600052604160045260246000fd5b600181811c908216806100cd57607f821691505b6020821081036100ed57634e487b7160e01b600052602260045260246000fd5b50919050565b601f82111561013e57600081815260208120601f850160051c810160208610156101225750805b601f850160051c820191505b818110156101415782815560010161012e565b5050505b505050565b81516001600160401b0381111561016357610163610142565b610177816101718454610158565b846100f3565b602080601f8311600181146101ac57600084156101945750858301515b600019600386901b1c1916600185901b178555610141565b600085815260208120601f198616915b828110156101db578886015182559484019460019091019084016101bc565b50858210156101f95787850151600019600388901b60f8161c191681555b5050505050600190811b01905550565b634e487b7160e01b600052603260045260246000fd5b60006001820161024057634e487b7160e01b600052601160045260246000fd5b5060010190565b818103818111156102585761025861021f565b92915050565b81516001600160401b0381111561027757610277610142565b61028b816102858454610158565b846100f3565b602080601f8311600181146102c057600084156102a85750858301515b600019600386901b1c1916600185901b178555610141565b600085815260208120601f198616915b828110156102ef578886015182559484019460019091019084016102d0565b508582101561030d5787850151600019600388901b60f8161c191681555b5050505050600190811b01905550565b6107b98061032c6000396000f3fe608060405234801561001057600080fd5b50600436106100a95760003560e01c80633950935111610071578063395093511461012357806370a082311461013657806395d89b411461015f578063a457c2d714610167578063a9059cbb1461017a578063dd62ed3e1461018d57600080fd5b806306fdde03146100ae578063095ea7b3146100cc57806318160ddd146100ef57806323b872dd14610101578063313ce56714610114575b600080fd5b6100b66101c6565b6040516100c391906105e6565b60405180910390f35b6100df6100da366004610650565b610258565b60405190151581526020016100c3565b6002545b6040519081526020016100c3565b6100df61010f36600461067a565b610272565b604051601281526020016100c3565b6100df610131366004610650565b610296565b6100f36101443660046106b6565b6001600160a01b031660009081526020819052604090205490565b6100b66102b8565b6100df610175366004610650565b6102c7565b6100df610188366004610650565b610347565b6100f361019b3660046106d8565b6001600160a01b03918216600090815260016020908152604080832093909416825291909152205490565b6060600380546101d59061070b565b80601f01602080910402602001604051908101604052809291908181526020018280546102019061070b565b801561024e5780601f106102235761010080835404028352916020019161024e565b820191906000526020600020905b81548152906001019060200180831161023157829003601f168201915b5050505050905090565b600033610266818585610355565b60019150505b92915050565b600033610280858285610479565b61028b8585856104f3565b506001949350505050565b6000336102668185856102a9838361019b565b6102b39190610745565b610355565b6060600480546101d59061070b565b600033816102d5828661019b565b90508381101561033a5760405162461bcd60e51b815260206004820152602560248201527f45524332303a2064656372656173656420616c6c6f77616e63652062656c6f77604482015264207a65726f60d81b60648201526084015b60405180910390fd5b61028b8286868403610355565b6000336102668185856104f3565b6001600160a01b0383166103b75760405162461bcd60e51b8152602060048201526024808201527f45524332303a20617070726f76652066726f6d20746865207a65726f206164646044820152637265737360e01b6064820152608401610331565b6001600160a01b0382166104185760405162461bcd60e51b815260206004820152602260248201527f45524332303a20617070726f766520746f20746865207a65726f206164647265604482015261737360f01b6064820152608401610331565b6001600160a01b0383811660008181526001602090815260408083209487168084529482529182902085905590518481527f8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925910160405180910390a3505050565b6000610485848461019b565b905060001981146104ed57818110156104e05760405162461bcd60e51b815260206004820152601d60248201527f45524332303a20696e73756666696369656e7420616c6c6f77616e63650000006044820152606401610331565b6104ed8484848403610355565b50505050565b6001600160a01b0383166105575760405162461bcd60e51b815260206004820152602560248201527f45524332303a207472616e736665722066726f6d20746865207a65726f206164604482015264647265737360d81b6064820152608401610331565b6001600160a01b0382166105b95760405162461bcd60e51b815260206004820152602360248201527f45524332303a207472616e7366657220746f20746865207a65726f206164647260448201526265737360e81b6064820152608401610331565b6105c4838383610692565b505050565b600060208083528351808285015260005b818110156105f6578581018301518582016040015282016105da565b506000604082860101526040601f19601f8301168501019250505092915050565b80356001600160a01b038116811461062e57600080fd5b919050565b634e487b7160e01b600052604160045260246000fd5b6000806040838503121561065c57600080fd5b61066583610617565b946020939093013593505050565b60008060006060848603121561068857600080fd5b61069184610617565b925061069f60208501610617565b9150604084013590509250925092565b6000602082840312156106c157600080fd5b6106ca82610617565b9392505050565b600080604083850312156106e457600080fd5b6106ed83610617565b91506106fb60208401610617565b90509250929050565b600181811c9082168061071857607f821691505b60208210810361073857634e487b7160e01b600052602260045260246000fd5b50919050565b8082018082111561026c57634e487b7160e01b600052601160045260246000fdfea264697066735822122069c8b5c5c4b4e4b5c5c4e4b4e5c5c4e4b4e5c5c4e4b4e5c5c4e4b4e5c5c464736f6c63430008130033"

# ABI for the deployed token
ERC20_ABI = [
    {"inputs": [], "stateMutability": "nonpayable", "type": "constructor"},
    {
        "inputs": [{"internalType": "address", "name": "spender", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}],
        "name": "approve",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "name",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "to", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}],
        "name": "transfer",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "from", "type": "address"}, {"internalType": "address", "name": "to", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}],
        "name": "transferFrom",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]


def deploy_token():
    """Deploy ERC20 test token to Anvil"""
    print("=" * 80)
    print("[START] Deploying Test USDC Token to Anvil")
    print("=" * 80)
    
    # Connect to Anvil
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    
    if not w3.is_connected():
        print("[ERROR] Failed to connect to Anvil. Make sure it's running on port 8545")
        return None
    
    print(f"\n[OK] Connected to Anvil")
    print(f"   Chain ID: {w3.eth.chain_id}")
    print(f"   Block: {w3.eth.block_number}")
    
    # Setup account
    account = Account.from_key(DEPLOYER_PRIVATE_KEY)
    print(f"\n📝 Deployer: {DEPLOYER_ADDRESS}")
    balance = w3.eth.get_balance(DEPLOYER_ADDRESS)
    print(f"   Balance: {w3.from_wei(balance, 'ether')} ETH")
    
    # Deploy contract
    print(f"\n🔨 Deploying ERC20 contract...")
    
    nonce = w3.eth.get_transaction_count(DEPLOYER_ADDRESS)
    
    # Build deployment transaction
    tx = {
        'from': DEPLOYER_ADDRESS,
        'data': ERC20_BYTECODE,
        'gas': 2000000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
        'chainId': w3.eth.chain_id
    }
    
    # Sign and send
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    print(f"   Transaction sent: {tx_hash.hex()}")
    print(f"   Waiting for confirmation...")
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt['status'] == 1:
        contract_address = receipt['contractAddress']
        print(f"\n[OK] Contract deployed successfully!")
        print(f"   Address: {contract_address}")
        print(f"   Gas used: {receipt['gasUsed']}")
        
        # Verify deployment
        contract = w3.eth.contract(address=contract_address, abi=ERC20_ABI)
        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
        decimals = contract.functions.decimals().call()
        
        print(f"\n[INFO] Token Info:")
        print(f"   Name: {name}")
        print(f"   Symbol: {symbol}")
        print(f"   Decimals: {decimals}")
        
        return contract_address
    else:
        print(f"\n[ERROR] Deployment failed!")
        return None


def mint_tokens(token_address, recipient, amount):
    """Mint tokens to recipient by setting balance directly (Anvil cheat)"""
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    
    # Calculate storage slot for balances mapping
    # In Solidity: mapping(address => uint256) private _balances; is usually at slot 0
    # Storage location = keccak256(abi.encode(key, slot))
    
    amount_wei = amount * 10**6  # USDC has 6 decimals
    
    print(f"\n[MINT] Minting {amount} USDC to {recipient}...")
    
    # Use Anvil's setStorageAt to directly set the balance
    # This is a cheat code that only works on test networks
    slot = 0  # Assuming _balances is at slot 0
    
    # Calculate storage position
    import eth_abi
    from eth_utils import keccak
    
    key = eth_abi.encode(['address', 'uint256'], [Web3.to_checksum_address(recipient), slot])
    storage_slot = '0x' + keccak(key).hex()
    
    # Convert amount to hex (32 bytes)
    value_hex = '0x' + hex(amount_wei)[2:].zfill(64)
    
    try:
        w3.provider.make_request("anvil_setStorageAt", [token_address, storage_slot, value_hex])
        print(f"   [OK] Minted {amount} USDC")
        
        # Verify
        contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
        balance = contract.functions.balanceOf(recipient).call()
        print(f"   Balance: {balance / 10**6} USDC")
        
    except Exception as e:
        print(f"   [ERROR] Error: {e}")


if __name__ == "__main__":
    import json
    
    # Deploy token
    token_address = deploy_token()
    
    if token_address:
        # Mint tokens to test accounts
        test_accounts = [
            ("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266", 10000),  # Account #0
            ("0x70997970C51812dc3A010C7d01b50e0d17dc79C8", 5000),   # Account #1
            ("0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC", 5000),   # Account #2
        ]
        
        for account, amount in test_accounts:
            mint_tokens(token_address, account, amount)
        
        # Update config file
        config_path = project_root / "configs" / "local_fork.json"
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            config["contracts"]["USDC"] = token_address
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"\n[OK] Updated config file: {config_path}")
            print(f"\n{'=' * 80}")
            print("[COMPLETE] Setup Complete!")
            print(f"{'=' * 80}")
            print(f"\nToken Address: {token_address}")
            print(f"\nYou can now run the demo with:")
            print(f"  python3 demo_llm_agent.py")
            
        except Exception as e:
            print(f"\n⚠️  Could not update config: {e}")
            print(f"\nManually add this to configs/local_fork.json:")
            print(f'  "USDC": "{token_address}"')
