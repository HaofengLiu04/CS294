"""
Code-based White Agent

Executes instructions by running generated Python code using Web3.py.
This agent uses pre-generated Python code from the green agent's operations.
"""

import time
from typing import Dict, Any
from web3 import Web3
from eth_account import Account
from .base_agent import WhiteAgent, ExecutionResult


class CodeWhiteAgent(WhiteAgent):
    """
    White agent that executes blockchain operations via Python code (Web3.py).
    
    This agent:
    1. Receives natural language instruction
    2. Gets pre-generated Python code from context
    3. Executes the code in a controlled environment
    4. Returns execution results
    """
    
    def __init__(self, rpc_url: str = "http://localhost:8545", private_key: str = None, name: str = "Code Agent"):
        super().__init__(
            name=name,
            description="Executes blockchain operations using Web3.py Python code"
        )
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.private_key = private_key
        if private_key:
            self.account = Account.from_key(private_key)
        else:
            self.account = None
    
    def execute_instruction(self, instruction: str, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute instruction using Python code.
        
        Args:
            instruction: Natural language instruction
            context: Must contain 'python_code' key with the code to execute
        
        Returns:
            ExecutionResult with transaction hash and status
        """
        start_time = time.time()
        
        # Get the pre-generated Python code from context
        python_code = context.get('python_code')
        if not python_code:
            return ExecutionResult(
                success=False,
                error="No Python code provided in context"
            )
        
        try:
            # Prepare execution environment
            exec_globals = {
                'w3': self.w3,
                'account': self.account,
                'private_key': self.private_key,
                'Web3': Web3,
                'Account': Account,
                'result': None  # Will be set by the executed code
            }
            
            # Execute the code
            exec(python_code, exec_globals)
            
            execution_time = time.time() - start_time
            
            # Get result from executed code
            tx_hash = exec_globals.get('result')
            
            if tx_hash:
                # If we got a transaction hash, wait for receipt
                try:
                    receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
                    
                    exec_result = ExecutionResult(
                        success=receipt['status'] == 1,
                        transaction_hash=tx_hash.hex() if hasattr(tx_hash, 'hex') else tx_hash,
                        gas_used=receipt.get('gasUsed'),
                        execution_time=execution_time,
                        metadata={
                            'block_number': receipt.get('blockNumber'),
                            'code': python_code
                        }
                    )
                except Exception as e:
                    exec_result = ExecutionResult(
                        success=False,
                        transaction_hash=tx_hash.hex() if hasattr(tx_hash, 'hex') else tx_hash,
                        error=f"Transaction failed: {str(e)}",
                        execution_time=execution_time
                    )
            else:
                # No transaction hash - possibly a view function or error
                exec_result = ExecutionResult(
                    success=True,
                    execution_time=execution_time,
                    metadata={'code': python_code}
                )
            
            # Record in history
            self.execution_history.append({
                'instruction': instruction,
                'code': python_code,
                'result': exec_result,
                'timestamp': time.time()
            })
            
            return exec_result
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=f"Code execution error: {str(e)}",
                execution_time=time.time() - start_time,
                metadata={'code': python_code}
            )
