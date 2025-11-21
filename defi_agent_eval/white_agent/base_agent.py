"""
Base White Agent Interface

White agents receive natural language instructions and execute blockchain operations.
They are the AI agents being evaluated by the green agent.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """Result of executing an instruction"""
    success: bool
    transaction_hash: Optional[str] = None
    error: Optional[str] = None
    gas_used: Optional[int] = None
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class WhiteAgent(ABC):
    """
    Base class for white agents (AI agents being evaluated).
    
    White agents receive natural language instructions and must:
    1. Understand the instruction
    2. Generate appropriate blockchain operations
    3. Execute them correctly
    4. Return execution results
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.execution_history = []
    
    @abstractmethod
    def execute_instruction(self, instruction: str, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute a natural language instruction.
        
        Args:
            instruction: Natural language description of what to do
            context: Additional context (initial state, available tokens, etc.)
        
        Returns:
            ExecutionResult with transaction details
        """
        pass
    
    def get_execution_history(self):
        """Return history of all executions"""
        return self.execution_history
    
    def reset_history(self):
        """Clear execution history"""
        self.execution_history = []
