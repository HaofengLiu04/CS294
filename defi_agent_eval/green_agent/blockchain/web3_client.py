"""
Blockchain connection and Web3 client management
Handles connection to Anvil local fork
"""

from web3 import Web3
from eth_account import Account
from typing import Dict, Optional
import json
import os
from dotenv import load_dotenv

load_dotenv()


class BlockchainClient:
    """Manages Web3 connection to local Anvil fork"""
    
    def __init__(self, rpc_url: Optional[str] = None):
        self.rpc_url = rpc_url or os.getenv("ANVIL_RPC_URL", "http://127.0.0.1:8545")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), "../../configs/local_fork.json")
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Test accounts
        self.accounts = self._load_accounts()
        
    def _load_accounts(self) -> Dict[str, str]:
        """Load test accounts from Anvil default accounts"""
        # Anvil default accounts (first 3)
        return {
            "deployer": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "user1": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
            "user2": "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
        }
    
    def is_connected(self) -> bool:
        """Check if connected to blockchain"""
        try:
            return self.w3.is_connected()
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def get_balance(self, address: str) -> float:
        """Get ETH balance of an address"""
        balance_wei = self.w3.eth.get_balance(address)
        return self.w3.from_wei(balance_wei, 'ether')
    
    def get_block_number(self) -> int:
        """Get current block number"""
        return self.w3.eth.block_number
    
    def get_token_balance(self, token_address: str, account_address: str) -> int:
        """Get ERC20 token balance in wei/smallest units"""
        # Standard ERC20 balanceOf function
        token_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=self._get_erc20_abi()
        )
        return token_contract.functions.balanceOf(Web3.to_checksum_address(account_address)).call()
    
    def get_token_balance_human(self, token_name: str, account_address: str) -> float:
        """Get ERC20 token balance in human-readable format"""
        token_address = self.get_contract_address(token_name)
        if not token_address:
            return 0.0
        
        balance_wei = self.get_token_balance(token_address, account_address)
        decimals = self._get_token_decimals(token_name)
        return balance_wei / (10 ** decimals)
    
    def transfer_erc20(self, token_name: str, from_account: str, to_account: str, 
                       amount: float, private_key: str) -> dict:
        """Transfer ERC20 tokens between accounts"""
        try:
            token_address = self.get_contract_address(token_name)
            if not token_address:
                return {"success": False, "error": f"Unknown token: {token_name}"}
            
            # Convert amount to wei
            decimals = self._get_token_decimals(token_name)
            amount_wei = int(amount * (10 ** decimals))
            
            # Create contract instance
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=self._get_erc20_abi()
            )
            
            # Build transaction
            tx = token_contract.functions.transfer(
                Web3.to_checksum_address(to_account),
                amount_wei
            ).build_transaction({
                'from': Web3.to_checksum_address(from_account),
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(Web3.to_checksum_address(from_account))
            })
            
            # Sign and send transaction
            from eth_account import Account
            account = Account.from_key(private_key)
            signed_tx = account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                "success": receipt['status'] == 1,
                "tx_hash": receipt['transactionHash'].hex(),
                "gas_used": receipt['gasUsed']
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def fund_account_tokens(self, account: str, token_name: str, amount: float):
        """Fund account with ERC20 tokens using whale impersonation (for testing)"""
        try:
            token_address = self.get_contract_address(token_name)
            decimals = self._get_token_decimals(token_name)
            amount_wei = int(amount * (10 ** decimals))
            
            # Known whale addresses for major tokens
            whale_addresses = {
                self.get_contract_address("USDC"): "0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503",
                self.get_contract_address("DAI"): "0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503", 
                self.get_contract_address("WETH"): "0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503"
            }
            
            whale = whale_addresses.get(token_address)
            if not whale:
                raise Exception(f"No whale address found for token {token_address}")
            
            # Impersonate whale
            self.w3.provider.make_request("anvil_impersonateAccount", [whale])
            
            # Transfer tokens
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=self._get_erc20_abi()
            )
            
            tx = token_contract.functions.transfer(
                Web3.to_checksum_address(account),
                amount_wei
            ).build_transaction({
                'from': whale,
                'gas': 100000,
                'gasPrice': 0
            })
            
            tx_hash = self.w3.eth.send_transaction(tx)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Stop impersonating
            self.w3.provider.make_request("anvil_stopImpersonatingAccount", [whale])
            
        except Exception as e:
            print(f"Error funding account with {token_name}: {e}")
            raise e
    
    def set_eth_balance(self, account: str, balance_eth: float):
        """Set ETH balance using Anvil RPC call (for testing)"""
        balance_wei = self.w3.to_wei(balance_eth, 'ether')
        self.w3.provider.make_request(
            "anvil_setBalance",
            [Web3.to_checksum_address(account), hex(balance_wei)]
        )
    
    def send_eth(self, from_account: str, to_account: str, amount_eth: float, private_key: str) -> str:
        """Send ETH from one account to another"""
        account = Account.from_key(private_key)
        
        tx = {
            'from': Web3.to_checksum_address(from_account),
            'to': Web3.to_checksum_address(to_account),
            'value': self.w3.to_wei(amount_eth, 'ether'),
            'gas': 21000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(Web3.to_checksum_address(from_account))
        }
        
        signed_tx = account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return receipt['transactionHash'].hex()
    
    def _get_erc20_abi(self):
        """Minimal ERC20 ABI"""
        return [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            }
        ]
    
    def _get_token_decimals(self, token_name: str) -> int:
        """Get decimal places for a token"""
        # Hardcoded for known tokens (could query contract in production)
        decimals_map = {
            "USDC": 6,
            "DAI": 18, 
            "WETH": 18,
            "ETH": 18
        }
        return decimals_map.get(token_name, 18)
    
    def get_contract_address(self, name: str) -> str:
        """Get contract address from config"""
        return self.config["contracts"].get(name, "")


if __name__ == "__main__":
    # Test connection
    client = BlockchainClient()
    print(f"Connected: {client.is_connected()}")
    print(f"Block number: {client.get_block_number()}")
    print(f"Deployer balance: {client.get_balance(client.accounts['deployer'])} ETH")
