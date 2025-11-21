"""
ERC20 Token Transfer Operation
Handles sending ERC20 tokens from one account to another
"""

from typing import Dict, Any
from web3 import Web3
from ..blockchain.web3_client import BlockchainClient


class ERC20Transfer:
    """Handles ERC20 token transfer operations"""
    
    def __init__(self, client: BlockchainClient):
        self.client = client
        self.w3 = client.w3
    
    def execute(self, params: Dict[str, Any], from_account: str, private_key: str) -> Dict[str, Any]:
        """
        Execute an ERC20 token transfer
        
        Args:
            params: {
                "token": "USDC",
                "to": "0x...",
                "amount": 1000
            }
            from_account: Sender address
            private_key: Sender private key
            
        Returns:
            {
                "success": True/False,
                "tx_hash": "0x...",
                "error": "..." (if failed)
            }
        """
        token_name = params.get("token", "USDC")
        to_address = params.get("to")
        amount = params.get("amount")
        
        # Use the consolidated client method
        return self.client.transfer_erc20(token_name, from_account, to_address, amount, private_key)
    
    def check_balance(self, token_name: str, account: str) -> float:
        """Check ERC20 token balance"""
        return self.client.get_token_balance_human(token_name, account)
    
    def generate_cli_command(self, params: Dict[str, Any], from_account: str) -> str:
        """
        Generate Foundry cast command for this operation
        
        Returns:
            CLI command string that can be executed
        """
        token_name = params.get("token", "USDC")
        to_address = params.get("to")
        amount = params.get("amount")
        
        token_address = self.client.get_contract_address(token_name)
        decimals = self.client._get_token_decimals(token_name)
        amount_wei = int(amount * (10 ** decimals))
        
        # Foundry cast send command
        cmd = f"""cast send {token_address} \\
  "transfer(address,uint256)" \\
  {to_address} \\
  {amount_wei} \\
  --from {from_account} \\
  --rpc-url $ANVIL_RPC_URL"""
        
        return cmd
    
    def generate_python_code(self, params: Dict[str, Any], from_account: str) -> str:
        """
        Generate Python code for this operation
        
        Returns:
            Python code string that can be executed
        """
        token_name = params.get("token", "USDC")
        to_address = params.get("to")
        amount = params.get("amount")
        
        code = f"""
from web3 import Web3

# Connect to Anvil
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Token contract
token_address = '{self.client.get_contract_address(token_name)}'
erc20_abi = [
    {{"constant": False, "inputs": [{{"name": "_to", "type": "address"}}, {{"name": "_value", "type": "uint256"}}], "name": "transfer", "outputs": [{{"name": "", "type": "bool"}}], "type": "function"}}
]

token = w3.eth.contract(address=token_address, abi=erc20_abi)

# Prepare transaction
decimals = {self.client._get_token_decimals(token_name)}
amount_wei = int({amount} * (10 ** decimals))

tx = token.functions.transfer('{to_address}', amount_wei).build_transaction({{
    'from': '{from_account}',
    'gas': 100000,
    'gasPrice': w3.eth.gas_price,
    'nonce': w3.eth.get_transaction_count('{from_account}')
}})

# Sign and send (private key needed)
# signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
# tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
# receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
# print(f"Transaction successful: {{receipt['transactionHash'].hex()}}")
"""
        return code.strip()


if __name__ == "__main__":
    # Test ERC20 transfer
    from ..blockchain.web3_client import BlockchainClient
    
    client = BlockchainClient()
    erc20 = ERC20Transfer(client)
    
    # Generate CLI command
    params = {
        "token": "USDC",
        "to": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        "amount": 1000
    }
    
    print("CLI Command:")
    print(erc20.generate_cli_command(params, client.accounts['deployer']))
    print("\nPython Code:")
    print(erc20.generate_python_code(params, client.accounts['deployer']))
