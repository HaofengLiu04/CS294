"""
LLM-based White Agent

An AI agent that interprets natural language instructions and generates
blockchain operations autonomously using an LLM.
"""

import time
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from web3 import Web3
from eth_account import Account
from openai import OpenAI
from dotenv import load_dotenv
from .base_agent import WhiteAgent, ExecutionResult

# Import blockchain client
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from green_agent.blockchain.web3_client import BlockchainClient

load_dotenv()


class LLMWhiteAgent(WhiteAgent):
    """
    White agent that uses an LLM to interpret instructions and execute operations.
    
    This agent:
    1. Receives natural language instruction
    2. Uses LLM to understand and plan execution
    3. Generates appropriate Web3 code or CLI commands
    4. Executes and returns results
    
    Note: This is a template. Integration with actual LLM (GPT-4, Claude, etc.)
    would require API keys and additional dependencies.
    """
    
    def __init__(
        self, 
        rpc_url: str = "http://localhost:8545",
        private_key: str = None,
        llm_api_key: Optional[str] = None,
        name: str = "LLM Agent"
    ):
        super().__init__(
            name=name,
            description="AI agent that interprets instructions using LLM and executes blockchain operations"
        )
        
        # Initialize blockchain client
        self.blockchain_client = BlockchainClient(rpc_url=rpc_url)
        self.w3 = self.blockchain_client.w3
        
        self.private_key = private_key
        if private_key:
            self.account = Account.from_key(private_key)
            self.account_address = self.account.address
        else:
            self.account = None
            self.account_address = None
        
        # Initialize OpenAI client
        api_key = llm_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env file.")
        self.client = OpenAI(api_key=api_key)
    
    def execute_instruction(self, instruction: str, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute instruction using LLM to interpret and plan.
        
        Args:
            instruction: Natural language instruction
            context: Initial state, available assets, etc.
        
        Returns:
            ExecutionResult with transaction details
        """
        start_time = time.time()
        
        try:
            # Step 1: Use LLM to understand instruction and generate plan
            print(f"[LLM] {self.name}: Analyzing instruction with LLM...")
            plan = self._generate_execution_plan(instruction, context)
            
            if not plan:
                return ExecutionResult(
                    success=False,
                    error="Failed to generate execution plan from LLM"
                )
            
            print(f"[PLAN] {self.name}: Generated plan: {json.dumps(plan, indent=2)}")
            
            # Step 2: Execute the plan
            print(f"[EXEC] {self.name}: Executing plan...")
            result = self._execute_plan(plan, context)
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            # Record in history
            self.execution_history.append({
                'instruction': instruction,
                'plan': plan,
                'result': result,
                'timestamp': time.time()
            })
            
            return result
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=f"LLM agent error: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _generate_execution_plan(self, instruction: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to interpret instruction and create execution plan.
        """
        prompt = f"""You are a DeFi agent assistant. Your job is to convert natural language instructions into structured JSON execution plans.

Instruction:
{instruction}

Context:
{json.dumps(context, indent=2, default=str)}

Based on the instruction, generate a JSON object with this structure:
{{
    "operation_type": "send_erc20",
    "parameters": {{
        "token": "TOKEN_SYMBOL",
        "to": "0x...",
        "amount": NUMBER
    }}
}}

Rules:
- Extract the token symbol, recipient address, and amount from the instruction
- The operation_type should be "send_erc20" for token transfers
- Return ONLY valid JSON, nothing else

Generate the execution plan now:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"[ERROR] Error calling OpenAI API: {e}")
            return None
    
    def _execute_plan(self, plan: Dict[str, Any], context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the plan generated by LLM on the actual blockchain.
        """
        start_time = time.time()
        op_type = plan.get("operation_type")
        params = plan.get("parameters", {})
        
        try:
            tx_hash = None
            gas_used = None
            
            if op_type == "send_erc20":
                # Transfer ERC20 tokens on the blockchain
                token = params.get("token")
                to_address = params.get("to")
                amount = params.get("amount")
                
                print(f"[TX] Transferring {amount} {token} to {to_address} on blockchain...")
                
                result = self.blockchain_client.transfer_erc20(
                    token_name=token,
                    from_account=self.account_address,
                    to_account=to_address,
                    amount=amount,
                    private_key=self.private_key
                )
                
                if not result.get("success"):
                    raise Exception(f"Transaction failed: {result.get('error')}")
                
                tx_hash = result.get("tx_hash")
                gas_used = result.get("gas_used")
                print(f"[SUCCESS] Transaction mined: {tx_hash}")
                print(f"          Gas used: {gas_used}")
                
            elif op_type == "send_eth":
                # Transfer ETH on the blockchain
                to_address = params.get("to")
                amount = params.get("amount")
                
                print(f"[TX] Sending {amount} ETH to {to_address} on blockchain...")
                
                tx_hash = self.blockchain_client.send_eth(
                    from_account=self.account_address,
                    to_account=to_address,
                    amount_eth=amount,
                    private_key=self.private_key
                )
                
                print(f"[SUCCESS] Transaction mined: {tx_hash}")
                
            else:
                raise Exception(f"Unsupported operation type: {op_type}")
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=True,
                transaction_hash=tx_hash,
                execution_time=execution_time,
                metadata={
                    'plan': plan,
                    'gas_used': gas_used,
                    'note': 'Real blockchain transaction executed successfully'
                }
            )
            
        except Exception as e:
            print(f"[ERROR] Blockchain execution failed: {e}")
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                transaction_hash=None,
                execution_time=execution_time,
                error=str(e),
                metadata={'plan': plan}
            )
