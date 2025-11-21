"""
CLI-based White Agent

Executes instructions by running Foundry cast commands.
This agent uses pre-generated CLI commands from the green agent's operations.
"""

import subprocess
import time
import re
from typing import Dict, Any
from .base_agent import WhiteAgent, ExecutionResult


class CLIWhiteAgent(WhiteAgent):
    """
    White agent that executes blockchain operations via CLI commands (Foundry cast).
    
    This agent:
    1. Receives natural language instruction
    2. Gets pre-generated CLI command from context
    3. Executes the command via subprocess
    4. Parses output and returns results
    """
    
    def __init__(self, rpc_url: str = "http://localhost:8545", name: str = "CLI Agent"):
        super().__init__(
            name=name,
            description="Executes blockchain operations using Foundry cast CLI commands"
        )
        self.rpc_url = rpc_url
    
    def execute_instruction(self, instruction: str, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute instruction using CLI command.
        
        Args:
            instruction: Natural language instruction
            context: Must contain 'cli_command' key with the command to run
        
        Returns:
            ExecutionResult with transaction hash and status
        """
        start_time = time.time()
        
        # Get the pre-generated CLI command from context
        cli_command = context.get('cli_command')
        if not cli_command:
            return ExecutionResult(
                success=False,
                error="No CLI command provided in context"
            )
        
        try:
            # Execute the command
            result = subprocess.run(
                cli_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                # Parse transaction hash from output
                tx_hash = self._parse_tx_hash(result.stdout)
                
                exec_result = ExecutionResult(
                    success=True,
                    transaction_hash=tx_hash,
                    execution_time=execution_time,
                    metadata={
                        'stdout': result.stdout,
                        'command': cli_command
                    }
                )
            else:
                exec_result = ExecutionResult(
                    success=False,
                    error=result.stderr or result.stdout,
                    execution_time=execution_time,
                    metadata={'command': cli_command}
                )
            
            # Record in history
            self.execution_history.append({
                'instruction': instruction,
                'command': cli_command,
                'result': exec_result,
                'timestamp': time.time()
            })
            
            return exec_result
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                error="Command execution timeout (30s)",
                execution_time=30.0
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=f"Execution error: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _parse_tx_hash(self, output: str) -> str:
        """Extract transaction hash from cast output"""
        # Look for hex strings that look like transaction hashes (0x + 64 hex chars)
        match = re.search(r'0x[a-fA-F0-9]{64}', output)
        if match:
            return match.group(0)
        
        # Look for common cast output patterns
        if 'transactionHash' in output:
            match = re.search(r'transactionHash["\s:]+0x[a-fA-F0-9]{64}', output)
            if match:
                return re.search(r'0x[a-fA-F0-9]{64}', match.group(0)).group(0)
        
        return output.strip() if output else None
