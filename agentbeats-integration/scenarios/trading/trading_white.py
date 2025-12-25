"""
Trading White Agent - A2A Server

This wraps a trading AI agent to be compatible with AgentBeats A2A protocol.
It receives trading prompts from the green agent and returns trading decisions.
"""

import argparse
import json
import logging
import os
import uvicorn
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from a2a.types import AgentCapabilities, AgentCard

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trading_white")


TRADING_AGENT_INSTRUCTION = """You are a professional cryptocurrency trading AI. 
Analyze the market data provided and make a trading decision.

Return your decision in this EXACT JSON format:
{
    "summary": "long|short|hold",
    "reasoning": "Your detailed reasoning here",
    "actions": [
        {"action": "open_long", "symbol": "BTCUSDT", "size": 0.5},
        {"action": "close", "symbol": "ETHUSDT", "size": 1.0}
    ]
}

Rules:
- summary: Must be "long", "short", or "hold"
- reasoning: Explain your decision based on the market data (technical indicators, trends, etc.)
- actions: List of trades to execute
  - action: "open_long", "open_short", "close", or "adjust"
  - symbol: The trading pair (e.g., "BTCUSDT")
  - size: Position size in contracts (can be fractional)
- If holding, return empty actions array
- Return ONLY valid JSON, nothing else
- Consider risk management: don't over-leverage, use stop losses mentally
"""


def main():
    parser = argparse.ArgumentParser(description="Run trading white agent (A2A server)")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9110)
    parser.add_argument("--name", type=str, default="alice", help="Agent name")
    parser.add_argument("--card-url", type=str, help="External URL for agent card")
    args = parser.parse_args()
    
    # Use Google ADK Agent (same pattern as debate example)
    # This is a simple LLM agent that receives prompts and responds
    root_agent = Agent(
        name=f"trading_white_{args.name}",
        model="gemini-2.5-flash",  # or use OpenAI/DeepSeek
        description=f"Trading AI agent: {args.name}",
        instruction=TRADING_AGENT_INSTRUCTION,
    )
    
    agent_url = args.card_url or f"http://{args.host}:{args.port}/"
    agent_card = AgentCard(
        name=f"trading_white_{args.name}",
        description=f"Trading white agent: {args.name}",
        url=agent_url,
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[]
    )
    
    # Convert to A2A-compatible server
    a2a_app = to_a2a(root_agent, agent_card=agent_card)
    
    logger.info(f"Starting trading white agent '{args.name}' on {args.host}:{args.port}")
    uvicorn.run(a2a_app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
