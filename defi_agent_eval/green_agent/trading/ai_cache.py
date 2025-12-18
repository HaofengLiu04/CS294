"""
AI Decision Cache for Trading Evaluator

Caches AI decisions to avoid redundant API calls with the same market data.
Inspired by nofx's AICache implementation.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

from .models import TradingDecision


class AICache:
    """
    Caches AI trading decisions to reduce API costs and enable replay.
    
    Cache key is computed from:
    - Agent name
    - Prompt content (which contains all market data)
    - Timestamp
    
    This ensures that identical market conditions return cached decisions.
    """
    
    def __init__(self, cache_file: Optional[str] = None):
        """
        Initialize AI cache.
        
        Args:
            cache_file: Path to cache file. If None, caching is disabled.
        """
        self.cache_file = cache_file
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.hits = 0
        self.misses = 0
        
        if cache_file and os.path.exists(cache_file):
            self.load()
    
    def _compute_key(self, agent_name: str, prompt: str, timestamp: str) -> str:
        """
        Compute cache key from agent name, prompt, and timestamp.
        
        We hash the prompt to create a compact key while ensuring
        identical prompts map to the same key.
        """
        # Create a stable string representation
        content = f"{agent_name}|{timestamp}|{prompt}"
        # Use SHA256 for collision resistance
        hash_obj = hashlib.sha256(content.encode('utf-8'))
        return hash_obj.hexdigest()[:16]  # Use first 16 chars for readability
    
    def get(self, agent_name: str, prompt: str, timestamp: str) -> Optional[TradingDecision]:
        """
        Retrieve cached decision if available.
        
        Returns:
            TradingDecision if cache hit, None if cache miss
        """
        if not self.cache_file:
            return None
        
        key = self._compute_key(agent_name, prompt, timestamp)
        
        if key in self.cache:
            self.hits += 1
            cached = self.cache[key]
            
            # Reconstruct TradingDecision from cached data
            from .models import TradingAction
            
            actions = [
                TradingAction(
                    symbol=a["symbol"],
                    action=a["action"],
                    leverage=a.get("leverage", 1),
                    quantity=a.get("quantity", 0)
                )
                for a in cached.get("actions", [])
            ]
            
            return TradingDecision(
                summary=cached.get("summary", ""),
                reasoning=cached.get("reasoning", ""),
                actions=actions
            )
        else:
            self.misses += 1
            return None
    
    def put(
        self, 
        agent_name: str, 
        prompt: str, 
        timestamp: str, 
        decision: TradingDecision
    ) -> None:
        """
        Store decision in cache.
        """
        if not self.cache_file:
            return
        
        key = self._compute_key(agent_name, prompt, timestamp)
        
        # Serialize TradingDecision
        self.cache[key] = {
            "agent_name": agent_name,
            "timestamp": timestamp,
            "summary": decision.summary,
            "reasoning": decision.reasoning,
            "actions": [
                {
                    "symbol": a.symbol,
                    "action": a.action,
                    "leverage": a.leverage,
                    "quantity": a.quantity
                }
                for a in decision.actions
            ],
            "cached_at": datetime.utcnow().isoformat()
        }
        
        # Auto-save after each put (for crash recovery)
        self.save()
    
    def load(self) -> None:
        """Load cache from disk."""
        if not self.cache_file or not os.path.exists(self.cache_file):
            return
        
        try:
            with open(self.cache_file, 'r') as f:
                self.cache = json.load(f)
            print(f"✅ Loaded AI cache: {len(self.cache)} entries from {self.cache_file}")
        except Exception as e:
            print(f"⚠️  Failed to load AI cache: {e}")
            self.cache = {}
    
    def save(self) -> None:
        """Save cache to disk."""
        if not self.cache_file:
            return
        
        try:
            # Ensure directory exists
            Path(self.cache_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save AI cache: {e}")
    
    def stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "entries": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%"
        }
    
    def clear(self) -> None:
        """Clear cache (both memory and disk)."""
        self.cache = {}
        self.hits = 0
        self.misses = 0
        
        if self.cache_file and os.path.exists(self.cache_file):
            os.remove(self.cache_file)
            print(f"🗑️  Cleared AI cache: {self.cache_file}")

