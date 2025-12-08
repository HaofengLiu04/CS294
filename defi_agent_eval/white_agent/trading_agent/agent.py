"""
Real-World AI Trading Agent

AI-powered trading agent that connects to REAL exchanges
and uses REAL-TIME market data from the internet.

Supported Exchanges:
- Binance Futures (via python-binance library)
- Hyperliquid (via hyperliquid-python-sdk)
- More can be added...

Authentication Methods:
1. Binance/Bybit/OKX: API Key + Secret Key (REST API)
2. Hyperliquid/DEX: Ethereum Private Key (Onchain signatures)

How It Works:
1. Connect to real exchange API (NO simulated blockchain)
2. Fetch REAL market data (prices, klines, positions)
3. AI analyzes real-time data
4. Execute trades on REAL exchange (with real money - BE CAREFUL!)

Prerequisites:
- pip install python-binance hyperliquid-python-sdk
- Exchange API credentials
- Real funds in exchange account (USE TESTNET FIRST!)
"""

import time
import json
import os
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Optional imports for different exchanges
try:
    from binance.client import Client as BinanceClient
    from binance.enums import *
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    print("WARNING: python-binance not installed. Install with: pip install python-binance")

try:
    from hyperliquid.exchange import Exchange
    from hyperliquid.info import Info
    from eth_account import Account
    HYPERLIQUID_AVAILABLE = True
except ImportError:
    HYPERLIQUID_AVAILABLE = False
    print("WARNING: hyperliquid-python-sdk not installed. Install with: pip install hyperliquid-python-sdk")

load_dotenv()


class RealWorldTradingAgent:
    """
    AI trading agent that connects to REAL exchanges.
    
    This agent:
    - Fetches REAL market data from internet
    - Uses REAL exchange APIs (Binance, Hyperliquid, etc.)
    - Executes REAL trades with REAL money
    - AI-powered decision making
    
    WARNING: This trades with REAL MONEY. Use testnet/paper trading first!
    """
    
    def __init__(
        self,
        exchange: str = "binance",  # "binance" or "hyperliquid"
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        private_key: Optional[str] = None,  # For Hyperliquid/DEX
        wallet_address: Optional[str] = None,  # For Hyperliquid
        testnet: bool = True,  # USE TESTNET FIRST!
        llm_model: str = "gpt-4o",
        llm_api_key: Optional[str] = None,
        name: str = "Real-World Trading Agent"
    ):
        self.name = name
        self.exchange_type = exchange
        self.testnet = testnet
        
        # Initialize LLM (for AI decisions)
        api_key_llm = llm_api_key or os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        if not api_key_llm:
            raise ValueError("LLM API key required. Set OPENAI_API_KEY or DEEPSEEK_API_KEY in .env")
        
        # Support DeepSeek API
        if llm_model and "deepseek" in llm_model.lower():
            self.llm_client = OpenAI(
                api_key=api_key_llm,
                base_url="https://api.deepseek.com"
            )
        else:
            self.llm_client = OpenAI(api_key=api_key_llm)
        self.llm_model = llm_model
        
        # Initialize exchange connection
        self.exchange = None
        if exchange == "binance":
            self._init_binance(api_key, api_secret, testnet)
        elif exchange == "hyperliquid":
            self._init_hyperliquid(private_key, wallet_address, testnet)
        else:
            raise ValueError(f"Unsupported exchange: {exchange}")
        
        # Decision history for tracking performance
        self.decision_history = []
        
        print(f"[OK] {self.name} initialized")
        print(f"   Exchange: {exchange} ({'TESTNET' if testnet else 'LIVE TRADING'})")
        print(f"   LLM: {llm_model}")
    
    def _init_binance(self, api_key: str, api_secret: str, testnet: bool):
        """Initialize Binance Futures connection"""
        if not BINANCE_AVAILABLE:
            raise ImportError("python-binance not installed. Run: pip install python-binance")
        
        if not api_key or not api_secret:
            raise ValueError("Binance requires API_KEY and API_SECRET")
        
        # Create Binance client
        self.exchange = BinanceClient(api_key, api_secret, testnet=testnet)
        
        if testnet:
            # Set testnet URL for futures
            self.exchange.API_URL = 'https://testnet.binancefuture.com'
        
        # Test connection
        try:
            self.exchange.futures_account()
            print(f"   [OK] Connected to Binance Futures")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Binance: {e}")
    
    def _init_hyperliquid(self, private_key: str, wallet_address: str, testnet: bool):
        """Initialize Hyperliquid connection"""
        if not HYPERLIQUID_AVAILABLE:
            raise ImportError("hyperliquid-python-sdk not installed. Run: pip install hyperliquid-python-sdk")
        
        if not private_key:
            raise ValueError("Hyperliquid requires PRIVATE_KEY")
        
        # Parse private key
        account = Account.from_key(private_key)
        
        # Create Hyperliquid client
        base_url = "https://api.hyperliquid-testnet.xyz" if testnet else "https://api.hyperliquid.xyz"
        
        self.exchange = {
            'info': Info(base_url, skip_ws=True),
            'exchange': Exchange(account, base_url),
            'wallet': wallet_address or account.address
        }
        
        print(f"   [OK] Connected to Hyperliquid")
        print(f"   Wallet: {self.exchange['wallet']}")
    
    # ================= MARKET DATA FETCHING (Real-time from internet) =================
    
    def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance from REAL exchange
        """
        if self.exchange_type == "binance":
            account = self.exchange.futures_account()
            return {
                'total_equity': float(account['totalWalletBalance']),
                'available_balance': float(account['availableBalance']),
                'unrealized_pnl': float(account['totalUnrealizedProfit'])
            }
        
        elif self.exchange_type == "hyperliquid":
            user_state = self.exchange['info'].user_state(self.exchange['wallet'])
            return {
                'total_equity': float(user_state['marginSummary']['accountValue']),
                'available_balance': float(user_state['withdrawable']),  # Fixed: was totalMarginUsed
                'unrealized_pnl': 0  # Calculate from positions
            }
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions from REAL exchange
        """
        if self.exchange_type == "binance":
            positions = self.exchange.futures_position_information()
            # Filter out zero positions
            active_positions = []
            for pos in positions:
                pos_amt = float(pos['positionAmt'])
                if abs(pos_amt) > 0:
                    active_positions.append({
                        'symbol': pos['symbol'],
                        'side': 'long' if pos_amt > 0 else 'short',
                        'size': abs(pos_amt),
                        'entry_price': float(pos['entryPrice']),
                        'mark_price': float(pos['markPrice']),
                        'unrealized_pnl': float(pos['unRealizedProfit']),
                        'leverage': int(pos['leverage'])
                    })
            return active_positions
        
        elif self.exchange_type == "hyperliquid":
            user_state = self.exchange['info'].user_state(self.exchange['wallet'])
            positions = []
            for pos in user_state.get('assetPositions', []):
                positions.append({
                    'symbol': pos['position']['coin'],
                    'side': 'long' if float(pos['position']['szi']) > 0 else 'short',
                    'size': abs(float(pos['position']['szi'])),
                    'entry_price': float(pos['position']['entryPx']),
                    'unrealized_pnl': float(pos['position']['unrealizedPnl']),
                    'leverage': float(pos['position']['leverage']['value'])
                })
            return positions
    
    def get_market_price(self, symbol: str) -> float:
        """
        Get current market price from REAL exchange
        """
        if self.exchange_type == "binance":
            ticker = self.exchange.futures_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        
        elif self.exchange_type == "hyperliquid":
            all_mids = self.exchange['info'].all_mids()
            return float(all_mids.get(symbol, 0))
    
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get historical klines/candles from REAL exchange
        """
        if self.exchange_type == "binance":
            klines = self.exchange.futures_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            result = []
            for k in klines:
                result.append({
                    'timestamp': int(k[0]),
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                })
            return result
        
        elif self.exchange_type == "hyperliquid":
            # Hyperliquid uses different interval format
            import time
            end_time = int(time.time() * 1000)  # Current time in milliseconds
            start_time = end_time - (100 * 60 * 60 * 1000)  # 100 hours ago
            
            candles = self.exchange['info'].candles_snapshot(
                name=symbol,  # Correct parameter is 'name'
                interval="1h",  # Hyperliquid intervals: 1m, 5m, 15m, 1h, 4h, 1d
                startTime=start_time,
                endTime=end_time
            )
            
            result = []
            for candle in candles:
                result.append({
                    'timestamp': int(candle['t']),
                    'open': float(candle['o']),
                    'high': float(candle['h']),
                    'low': float(candle['l']),
                    'close': float(candle['c']),
                    'volume': float(candle['v'])
                })
            return result
    
    # ================= AI DECISION ENGINE =================
    
    def run_cycle(self, symbols: List[str] = None, custom_instruction: str = None) -> Dict[str, Any]:
        """
        Run one decision cycle
        
        Args:
            symbols: List of trading symbols to analyze (e.g., ["BTCUSDT", "ETHUSDT"])
            custom_instruction: Optional custom prompt/instruction for the AI
                              e.g., "Focus on BTC only" or "Close all positions"
        
        Steps:
        1. Analyze historical performance (last 20 cycles)
        2. Get account status from REAL exchange
        3. Get current positions
        4. Fetch REAL market data for candidate symbols
        5. AI makes decision with Chain of Thought
        6. Execute decision on REAL exchange
        7. Record decision for future analysis
        """
        cycle_number = len(self.decision_history) + 1
        print(f"\n{'='*80}")
        print(f"AI Trading Cycle #{cycle_number} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        # Default symbols if not provided
        if symbols is None:
            if self.exchange_type == "binance":
                symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
            else:
                symbols = ["BTC", "ETH", "SOL"]
        
        try:
            # Step 1: Analyze historical performance
            print("[STEP 1/7] Analyzing historical performance...")
            history_analysis = self._analyze_history()
            print(f"   Completed cycles: {history_analysis['total_cycles']}")
            print(f"   Win rate: {history_analysis['win_rate']:.1f}%")
            
            # Step 2: Get account status from REAL exchange
            print("\n[STEP 2/7] Fetching account balance from REAL exchange...")
            balance = self.get_balance()
            print(f"   Total Equity: ${balance['total_equity']:.2f}")
            print(f"   Available: ${balance['available_balance']:.2f}")
            print(f"   Unrealized P/L: ${balance['unrealized_pnl']:.2f}")
            
            # Step 3: Get current positions
            print("\n[STEP 3/7] Fetching current positions...")
            positions = self.get_positions()
            print(f"   Active positions: {len(positions)}")
            for pos in positions:
                print(f"   - {pos['symbol']}: {pos['side']} ${pos['size']:.2f} @ ${pos['entry_price']:.2f}")
            
            # Step 4: Fetch REAL market data
            print(f"\n[STEP 4/7] Fetching REAL-TIME market data from internet...")
            market_data = {}
            for symbol in symbols:
                try:
                    price = self.get_market_price(symbol)
                    klines = self.get_klines(symbol, interval="1h", limit=24)  # Last 24 hours
                    
                    # Calculate simple indicators
                    closes = [k['close'] for k in klines]
                    sma_24 = sum(closes) / len(closes) if closes else price
                    
                    market_data[symbol] = {
                        'price': price,
                        'klines': klines[-5:],  # Last 5 candles
                        'sma_24h': sma_24,
                        'change_24h': ((price - closes[0]) / closes[0] * 100) if closes else 0
                    }
                    
                    print(f"   [OK] {symbol}: ${price:.2f} ({market_data[symbol]['change_24h']:+.2f}%)")
                except Exception as e:
                    print(f"   [FAIL] {symbol}: Failed to fetch data - {e}")
            
            # Step 5: Build context and get AI decision
            print(f"\n[STEP 5/7] Generating AI decision with Chain of Thought...")
            if custom_instruction:
                print(f"   Custom Instruction: {custom_instruction}")
            decision = self._get_ai_decision(
                cycle_number=cycle_number,
                history_analysis=history_analysis,
                balance=balance,
                positions=positions,
                market_data=market_data,
                custom_instruction=custom_instruction
            )
            
            print(f"   Decision: {decision['action']}")
            if decision.get('reasoning'):
                reasoning_preview = decision['reasoning'][:200]
                print(f"   Reasoning: {reasoning_preview}...")
            
            # Step 6: Execute decision on REAL exchange
            print(f"\n[STEP 6/7] Executing decision on REAL exchange...")
            execution_result = self._execute_decision(decision)
            print(f"   Execution: {'SUCCESS' if execution_result['success'] else 'FAILED'}")
            
            # Step 7: Record decision
            print(f"\n[STEP 7/7] Recording decision for future analysis...")
            self._record_decision(
                cycle_number=cycle_number,
                decision=decision,
                execution_result=execution_result,
                market_data=market_data
            )
            
            print(f"\n{'='*80}")
            print(f"Cycle #{cycle_number} Complete")
            print(f"{'='*80}\n")
            
            return {
                'cycle_number': cycle_number,
                'decision': decision,
                'execution': execution_result,
                'balance': balance,
                'positions': positions
            }
            
        except Exception as e:
            print(f"\n[ERROR] Error in cycle #{cycle_number}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'cycle_number': cycle_number,
                'error': str(e),
                'success': False
            }
    
    def _analyze_history(self) -> Dict[str, Any]:
        """
        Analyze last 20 decision cycles for performance
        """
        recent_history = self.decision_history[-20:] if len(self.decision_history) > 0 else []
        
        total_cycles = len(recent_history)
        winning_cycles = sum(1 for h in recent_history if h.get('execution', {}).get('success'))
        win_rate = (winning_cycles / total_cycles * 100) if total_cycles > 0 else 0
        
        return {
            'total_cycles': total_cycles,
            'winning_cycles': winning_cycles,
            'win_rate': win_rate,
            'recent_decisions': recent_history[-5:] if recent_history else []
        }
    
    def _build_system_prompt(self, history_analysis: Dict[str, Any]) -> str:
        """
        Build system prompt for AI
        """
        return f"""You are a professional cryptocurrency futures trader operating on {self.exchange_type.upper()}.

TRADING RULES:
1. **Risk Management**: Never risk more than 2-5% of account per trade
2. **Position Sizing**: Scale positions based on confidence and volatility
3. **Trading Frequency**: Excellent traders make 2-4 trades per day (not every cycle)
4. **Performance Awareness**: Your recent win rate is {history_analysis['win_rate']:.1f}%

HISTORICAL PERFORMANCE:
- Total cycles completed: {history_analysis['total_cycles']}
- Winning cycles: {history_analysis['winning_cycles']}
- Win rate: {history_analysis['win_rate']:.1f}%

OUTPUT FORMAT:
You MUST respond with:
<reasoning>
[Your detailed Chain of Thought analysis here]
- Current market conditions
- Account state analysis
- Risk assessment
- Decision rationale
</reasoning>

<decision>
{{
  "action": "open_long" | "open_short" | "close_position" | "hold",
  "symbol": "BTCUSDT" (or null if hold),
  "size_usd": 100.0 (or null if hold),
  "leverage": 5 (or null if hold),
  "reason": "Brief reason for this decision"
}}
</decision>

Think carefully before trading. Not every cycle requires action.
"""
    
    def _build_user_prompt(
        self,
        cycle_number: int,
        balance: Dict[str, Any],
        positions: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        custom_instruction: Optional[str] = None
    ) -> str:
        """
        Build user prompt with current data
        """
        positions_str = "\n".join([
            f"  - {p['symbol']}: {p['side']} ${p['size']:.2f} @ ${p['entry_price']:.2f} (P/L: ${p['unrealized_pnl']:.2f})"
            for p in positions
        ]) if positions else "  No active positions"
        
        market_str = "\n".join([
            f"  - {symbol}: ${data['price']:.2f} (24h: {data['change_24h']:+.2f}%, SMA: ${data['sma_24h']:.2f})"
            for symbol, data in market_data.items()
        ])
        
        base_prompt = f"""CYCLE #{cycle_number} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ACCOUNT STATUS:
  Total Equity: ${balance['total_equity']:.2f}
  Available: ${balance['available_balance']:.2f}
  Unrealized P/L: ${balance['unrealized_pnl']:+.2f}

CURRENT POSITIONS:
{positions_str}

MARKET DATA (REAL-TIME):
{market_str}
"""
        
        # Add custom instruction if provided
        if custom_instruction:
            base_prompt += f"""

CUSTOM INSTRUCTION FROM USER:
{custom_instruction}

Please follow this instruction while making your trading decision.
"""
        
        base_prompt += "\nWhat is your trading decision for this cycle?"
        
        return base_prompt
    
    def _get_ai_decision(
        self,
        cycle_number: int,
        history_analysis: Dict[str, Any],
        balance: Dict[str, Any],
        positions: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        custom_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get AI decision using Chain of Thought
        """
        system_prompt = self._build_system_prompt(history_analysis)
        user_prompt = self._build_user_prompt(
            cycle_number, balance, positions, market_data, custom_instruction
        )
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            ai_response = response.choices[0].message.content
            
            # Parse response to extract reasoning and decision
            return self._parse_ai_response(ai_response)
            
        except Exception as e:
            print(f"   WARNING: AI decision failed: {e}")
            return {
                'action': 'hold',
                'symbol': None,
                'reasoning': f"Error getting AI decision: {e}",
                'error': str(e)
            }
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """
        Parse AI response to extract reasoning and decision
        """
        # Extract reasoning
        reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', response, re.DOTALL)
        reasoning = reasoning_match.group(1).strip() if reasoning_match else "No reasoning provided"
        
        # Extract decision JSON
        decision_match = re.search(r'<decision>(.*?)</decision>', response, re.DOTALL)
        if decision_match:
            try:
                decision_json = json.loads(decision_match.group(1).strip())
                decision_json['reasoning'] = reasoning
                return decision_json
            except json.JSONDecodeError:
                return {
                    'action': 'hold',
                    'symbol': None,
                    'reasoning': reasoning,
                    'error': 'Failed to parse decision JSON'
                }
        else:
            return {
                'action': 'hold',
                'symbol': None,
                'reasoning': reasoning,
                'error': 'No decision tag found'
            }
    
    def _execute_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute decision on REAL exchange
        
        WARNING: This executes REAL trades with REAL money!
        """
        action = decision.get('action', 'hold')
        
        if action == 'hold':
            return {'success': True, 'message': 'No action taken'}
        
        try:
            symbol = decision.get('symbol')
            size_usd = decision.get('size_usd', 0)
            leverage = decision.get('leverage', 1)
            
            if self.exchange_type == "binance":
                return self._execute_binance(action, symbol, size_usd, leverage)
            elif self.exchange_type == "hyperliquid":
                return self._execute_hyperliquid(action, symbol, size_usd, leverage)
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_binance(self, action: str, symbol: str, size_usd: float, leverage: int) -> Dict[str, Any]:
        """Execute trade on Binance"""
        # Set leverage
        self.exchange.futures_change_leverage(symbol=symbol, leverage=leverage)
        
        # Get current price
        price = self.get_market_price(symbol)
        
        # Calculate quantity (size in contracts)
        quantity = size_usd / price
        
        # Round to valid precision (simplified - should check symbol info)
        quantity = round(quantity, 3)
        
        # Place market order
        if action == "open_long":
            order = self.exchange.futures_create_order(
                symbol=symbol,
                side="BUY",
                type="MARKET",
                quantity=quantity
            )
        elif action == "open_short":
            order = self.exchange.futures_create_order(
                symbol=symbol,
                side="SELL",
                type="MARKET",
                quantity=quantity
            )
        elif action == "close_position":
            # Get position to determine close side
            positions = self.get_positions()
            pos = next((p for p in positions if p['symbol'] == symbol), None)
            if pos:
                side = "SELL" if pos['side'] == 'long' else "BUY"
                order = self.exchange.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type="MARKET",
                    quantity=pos['size'],
                    reduceOnly=True
                )
            else:
                return {'success': False, 'error': 'No position to close'}
        
        return {
            'success': True,
            'order_id': order['orderId'],
            'symbol': symbol,
            'quantity': quantity,
            'action': action
        }
    
    def _execute_hyperliquid(self, action: str, symbol: str, size_usd: float, leverage: int) -> Dict[str, Any]:
        """Execute trade on Hyperliquid"""
        # Get current price
        price = self.get_market_price(symbol)
        
        # Calculate size
        size = size_usd / price
        
        # Determine is_buy flag
        is_buy = action in ["open_long", "close_short"]
        
        # Place market order
        order_result = self.exchange['exchange'].market_open(
            coin=symbol,
            is_buy=is_buy,
            sz=size,
            slippage=0.05  # 5% slippage tolerance
        )
        
        return {
            'success': order_result['status'] == 'ok',
            'order': order_result,
            'symbol': symbol,
            'size': size,
            'action': action
        }
    
    def _record_decision(
        self,
        cycle_number: int,
        decision: Dict[str, Any],
        execution_result: Dict[str, Any],
        market_data: Dict[str, Any]
    ):
        """
        Record decision for future analysis
        """
        record = {
            'cycle_number': cycle_number,
            'timestamp': datetime.now().isoformat(),
            'decision': decision,
            'execution': execution_result,
            'market_data': market_data
        }
        
        self.decision_history.append(record)
        
        # Optionally save to file
        # with open(f'decisions_{self.name}.json', 'w') as f:
        #     json.dump(self.decision_history, f, indent=2)
