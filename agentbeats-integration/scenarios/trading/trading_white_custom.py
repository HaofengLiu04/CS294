"""
Trading White Agent - Using YOUR Custom Trading Agent

This creates a simple A2A server that uses YOUR agent's LLM (DeepSeek/OpenAI)
for trading decisions instead of Gemini.
"""

import argparse
import json
import logging
import os
import sys
import uvicorn
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from a2a.types import AgentCapabilities, AgentCard

# Add CS294 to path to use your agent if needed
CS294_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, CS294_ROOT)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trading_white_custom")


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
    parser = argparse.ArgumentParser(description="Run trading white agent with YOUR custom LLM")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9110)
    parser.add_argument("--name", type=str, default="alice", help="Agent name")
    parser.add_argument("--card-url", type=str, help="External URL for agent card")
    args = parser.parse_args()
    
    # Determine which LLM to use from environment
    # This checks for YOUR agent's API keys
    # Priority: OPENAI_API_KEY -> GOOGLE_API_KEY
    
    if os.getenv("OPENAI_API_KEY"):
        # Use OpenAI if key is present
        # You can change this to "gpt-4" or "deepseek-chat" if using compatible endpoints
        model_name = os.getenv("TRADING_JUDGE_MODEL", "gpt-4o-mini")
        logger.info(f"Using OpenAI/Compatible API for agent: {args.name} with model {model_name}")
    elif os.getenv("GOOGLE_API_KEY"):
        # Fallback to Gemini
        model_name = "gemini-2.5-flash"
        logger.info(f"Using Gemini API for agent: {args.name}")
    else:
        # Default fallback
        model_name = "gemini-2.5-flash"
        logger.warning(f"No API keys found. Defaulting to Gemini (may fail if no auth): {args.name}")
    
    # Create agent
    root_agent = Agent(
        name=f"trading_white_{args.name}",
        model=model_name,
        description=f"Trading AI agent: {args.name}",
        instruction=TRADING_AGENT_INSTRUCTION,
    )
    
    agent_url = args.card_url or f"http://{args.host}:{args.port}/"
    agent_card = AgentCard(
        name=f"trading_white_{args.name}",
        description=f"Trading white agent: {args.name} (using {model_name})",
        url=agent_url,
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[]
    )
    
    # Convert to A2A-compatible server
    a2a_app = to_a2a(root_agent, agent_card=agent_card)
    
    logger.info(f"Starting trading white agent '{args.name}' on {args.host}:{args.port} with {model_name}")
    uvicorn.run(a2a_app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
