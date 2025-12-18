"""
Green Agent trading evaluator.

This class orchestrates a multi-agent backtest using the white_agent.trading_agent
BacktestAccount primitives while following the competition design described in
green_white_logic.md. It focuses on:
- Loading 4h + 3m Binance historical data
- Computing technical indicators
- Building rich prompts for White Agents
- Executing their structured decisions in isolated BacktestAccounts
- Producing disclosure packages and performance metrics
"""

from __future__ import annotations

import json
import math
from datetime import datetime
import os
import requests
from litellm import completion
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

from white_agent.trading_agent.backtest_account import BacktestAccount, Position
from white_agent.trading_agent.backtest_runner import TradeEvent, EquityPoint

from .data import (
    BinanceHTTPFetcher,
    add_indicators,
    last_rows,
    window_df,
    INTERVAL_TO_SECONDS,
)
from .models import (
    TradingAction,
    TradingDecision,
    AgentRoundDecision,
    DisclosurePackage,
    ReasoningEvaluation,
    AgentPerformance,
    AgentReasoningQuality,
)
from .ai_cache import AICache


DEFAULT_CONFIG: Dict = {
    "symbols": [
        "BTCUSDT",
        "ETHUSDT",
        "SOLUSDT",
        "BNBUSDT",
        "XRPUSDT",
        "ADAUSDT",
        "DOGEUSDT",
        "AVAXUSDT",
        "LINKUSDT",
        "MATICUSDT",
    ],
    "start_date": "2025-12-01",
    "end_date": "2025-12-14",
    "timeframe": "4h",
    "decision_interval": "4h",
    "intraday_interval": "3m",
    "intraday_lookback_hours": 4,
    "intraday_candles_count": 80,
    "decisions_per_day": 6,
    "total_decision_cycles": 180,
    "initial_balance": 10_000.0,
    "fee_bps": 5.0,
    "slippage_bps": 2.0,
    "enable_multi_round": True,
    "disclosure_cycles": [42, 84, 126],
    "disclosure_days": [7, 14, 21],
}


class TradingEvaluator:
    """
    Core orchestrator for the trading competition.
    """

    def __init__(
        self,
        agent_names: List[str],
        agent_clients: Optional[Dict[str, Callable[[str], TradingDecision]]] = None,
        config: Optional[Dict] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.agent_names = agent_names
        self.agent_clients = agent_clients or {}
        self._progress_callback = progress_callback

        self.accounts: Dict[str, BacktestAccount] = {
            name: BacktestAccount(
                initial_balance=self.config["initial_balance"],
                fee_bps=self.config["fee_bps"],
                slippage_bps=self.config["slippage_bps"],
            )
            for name in agent_names
        }

        self.data_fetcher = BinanceHTTPFetcher()
        self.data_4h: Dict[str, pd.DataFrame] = {}
        self.data_3m: Dict[str, pd.DataFrame] = {}

        self.current_round = 0
        self.round_decisions: List[AgentRoundDecision] = []
        self.disclosure_packages: List[DisclosurePackage] = []
        self.trade_history: Dict[str, List[TradeEvent]] = {name: [] for name in agent_names}
        self.equity_history: Dict[str, List[EquityPoint]] = {name: [] for name in agent_names}
        self.performance: Dict[str, AgentPerformance] = {}
        
    def _progress(self, event: Dict[str, Any]) -> None:
        """Best-effort progress hook (used by AgentBeats green agent to show progress)."""
        cb = getattr(self, "_progress_callback", None)
        if not cb:
            return
        try:
            cb(event)
        except Exception:
            # Never let progress reporting break evaluation
            return

        # Initialize AI cache if enabled
        cache_file = self.config.get("ai_cache_file")
        self.ai_cache = AICache(cache_file) if cache_file else None
        if self.ai_cache:
            print(f"🗄️  AI Cache enabled: {cache_file}")

    # ------------------------------------------------------------------ #
    # Data loading and preparation
    # ------------------------------------------------------------------ #
    def load_and_prepare_data(self):
        """Fetch 4h + 3m data for all symbols and compute indicators."""
        start = pd.to_datetime(self.config["start_date"])
        end = pd.to_datetime(self.config["end_date"])

        for symbol in self.config["symbols"]:
            four_h = self.data_fetcher.fetch_klines(symbol, "4h", start, end + pd.Timedelta(days=1))
            three_m = self.data_fetcher.fetch_klines(symbol, "3m", start, end + pd.Timedelta(days=1))

            self.data_4h[symbol] = add_indicators(four_h)
            self.data_3m[symbol] = add_indicators(three_m)

    # ------------------------------------------------------------------ #
    # Prompt building
    # ------------------------------------------------------------------ #
    def build_market_prompt(self, agent_name: str, cycle_idx: int, timestamp: pd.Timestamp) -> str:
        """
        Construct the prompt using the richer template provided by the user.

        Many fields (如 Funding / OI) 无法从当前数据源获得，使用占位符 "N/A"。
        """
        decision_time = timestamp
        runtime_days = (cycle_idx - 1) / max(1, self.config["decisions_per_day"])
        current_prices = self._current_price_map(decision_time)

        # Account-level aggregates
        equity, unrealized, per_symbol = self.accounts[agent_name].total_equity(current_prices)
        balance = self.accounts[agent_name].get_cash()
        margin_used = sum(p.margin for p in self.accounts[agent_name].get_positions())
        pnl_pct = (equity - self.accounts[agent_name].initial_balance) / self.accounts[agent_name].initial_balance * 100
        margin_pct = (margin_used / equity * 100) if equity > 0 else 0.0
        balance_pct = (balance / equity * 100) if equity > 0 else 0.0

    
        prompt_lines = [
            f"Time: {decision_time} | Cycle: #{cycle_idx} | Runtime: {runtime_days:.1f}d",
        ]

        btc_price = current_prices.get("BTCUSDT", None)
        if btc_price is not None:
            btc_4h = self.data_4h.get("BTCUSDT", pd.DataFrame())
            btc_change_4h = 0.0
            btc_change_1h = 0.0
            macd_val = "N/A"
            rsi_val = "N/A"
            if not btc_4h.empty:
                latest = btc_4h[btc_4h["open_time"] <= decision_time].tail(2)
                if len(latest) >= 2:
                    prev = latest.iloc[-2].close
                    last = latest.iloc[-1].close
                    btc_change_4h = (last - prev) / prev * 100 if prev else 0.0
                    macd_val = f"{latest.iloc[-1].macd:.4f}"
                    rsi_val = f"{latest.iloc[-1].rsi7:.2f}"
            prompt_lines.append(
                f"BTC: {btc_price:.2f} (1h: {btc_change_1h:+.2f}%, 4h: {btc_change_4h:+.2f}%) | "
                f"MACD: {macd_val} | RSI: {rsi_val}"
            )

        # Account snapshot
        positions = self._read_agent_positions(agent_name)
        prompt_lines.append(
            f"\nAccount: Equity {equity:.2f} | Cash {balance:.2f} ({balance_pct:.1f}%) | "
            f"P&L {pnl_pct:+.2f}% | Margin {margin_pct:.1f}% | Positions {len(positions)}\n"
        )

        # Positions section
        prompt_lines.append("## Current Positions\n")
        if positions:
            for idx, pos in enumerate(positions, 1):
                prompt_lines.append(self._format_position_rich(pos, idx, current_prices, decision_time))
        else:
            prompt_lines.append("None\n")

        # Candidates section
        prompt_lines.append(f"\n## Candidate Symbols ({len(self.config['symbols'])})\n")
        for idx, symbol in enumerate(self.config["symbols"], 1):
            prompt_lines.append(self._format_candidate_rich(symbol, idx, decision_time))

        # Disclosure intelligence
        if self.config.get("enable_multi_round") and self.disclosure_packages:
            prompt_lines.append("\n" + "=" * 60)
            prompt_lines.append("📊 Intelligence Report")
            prompt_lines.append("=" * 60 + "\n")
            for disclosure in self.disclosure_packages:
                prompt_lines.append(f"[Disclosure {disclosure.round_number} - Day {disclosure.disclosure_day}]\n")
                prompt_lines.append("Leaderboard:")
                for rank_row in disclosure.leaderboard:
                    emoji = "👑" if rank_row["rank"] == 1 else f"{rank_row['rank']}."
                    is_you = "(you)" if rank_row["name"] == agent_name else ""
                    prompt_lines.append(
                        f"  {emoji} {rank_row['name']}{is_you}: "
                        f"{rank_row['pnl_pct']:+.2f}% (${rank_row['equity']:.2f})"
                    )
                prompt_lines.append("")
                for agent_summary in disclosure.agents_round_summary:
                    if agent_summary["name"] == agent_name:
                        continue
                    prompt_lines.append(f"━━ {agent_summary['name']} ━━")
                    if agent_summary.get("market_views"):
                        prompt_lines.append(f"  Market View: {agent_summary['market_views'][-1]}")
                    if agent_summary.get("opponent_analysis"):
                        prompt_lines.append(f"  Opponent Analysis: {agent_summary['opponent_analysis']}")
                    if agent_summary.get("strategy_adjustment"):
                        prompt_lines.append(f"  Strategy Adjustment: {agent_summary['strategy_adjustment']}")
                    prompt_lines.append(f"  Actions: {agent_summary['actions_summary']}")
                    prompt_lines.append(f"  Positions: {agent_summary['positions']}")
                    prompt_lines.append(f"  PnL: {agent_summary['pnl_pct']:+.2f}%")
                    prompt_lines.append("")
                prompt_lines.append("-" * 60 + "\n")

            prompt_lines.append("Include <opponent_analysis> and <strategy_adjustment> in <reasoning>.")

        return "\n".join(prompt_lines)

    def _format_position_rich(self, pos: Position, idx: int, price_map: Dict[str, float], ts: pd.Timestamp) -> str:
        current_price = price_map.get(pos.symbol)
        if current_price is None:
            current_price = pos.entry_price
        unrealized = BacktestAccount._unrealized_pnl(pos, current_price)
        pnl_pct = (unrealized / pos.notional * 100) if pos.notional else 0.0
        notional = pos.notional
        hold_hours = 0.0
        if pos.open_time:
            hold_hours = max(0.0, (ts - pd.to_datetime(pos.open_time, unit="s", utc=True)).total_seconds() / 3600)

        # Intraday slice (last 10 of 3m)
        intraday = window_df(self.data_3m.get(pos.symbol, pd.DataFrame()), ts, self.config["intraday_lookback_hours"])
        intraday_tail = last_rows(intraday, 10)
        mid_prices = self._array_str(intraday_tail.get("close"))
        ema_3m = self._array_str(intraday_tail.get("ema20"))
        macd_3m = self._array_str(intraday_tail.get("macd"))
        rsi7_3m = self._array_str(intraday_tail.get("rsi7"))
        rsi14_3m = self._array_str(intraday_tail.get("rsi14"))
        vol_3m = self._array_str(intraday_tail.get("volume"))
        atr3m_14 = f"{intraday_tail['atr14'].iloc[-1]:.4f}" if not intraday_tail.empty else "N/A"

        # 4h context (last 10)
        df4h = self.data_4h.get(pos.symbol, pd.DataFrame())
        ctx4h = df4h[df4h["open_time"] <= ts]
        tail4h = last_rows(ctx4h, 10)
        ema20_4h = f"{tail4h['ema20'].iloc[-1]:.4f}" if not tail4h.empty else "N/A"
        ema50_4h = f"{tail4h['ema50'].iloc[-1]:.4f}" if not tail4h.empty else "N/A"
        atr3_4h = "N/A"
        atr14_4h = f"{tail4h['atr14'].iloc[-1]:.4f}" if not tail4h.empty else "N/A"
        cur_vol_4h = f"{tail4h['volume'].iloc[-1]:.2f}" if not tail4h.empty else "N/A"
        avg_vol_4h = f"{tail4h['volume'].mean():.2f}" if not tail4h.empty else "N/A"
        macd4h_arr = self._array_str(tail4h.get("macd"))
        rsi4h_arr = self._array_str(tail4h.get("rsi14"))

        # Pre-format values that might be None or contain special chars
        cp_str = f"{current_price:.2f}" if current_price is not None else "N/A"
        entry_str = f"{pos.entry_price:.2f}" if pos.entry_price is not None else "N/A"
        liq_str = f"{pos.liquidation_price:.2f}" if pos.liquidation_price is not None else "N/A"
        side_str = str(pos.side).upper() if pos.side else "N/A"
        symbol_str = str(pos.symbol) if pos.symbol else "N/A"
        qty_str = f"{pos.quantity:.4f}" if pos.quantity is not None else "0.0000"
        notional_str = f"{notional:.2f}" if notional is not None else "0.00"
        margin_str = f"{pos.margin:.2f}" if pos.margin is not None else "0.00"
        leverage_str = str(pos.leverage) if pos.leverage is not None else "1"
        
        # Pre-format indicator values that might be NaN
        ema20_now = tail4h["ema20"].iloc[-1] if not tail4h.empty else float("nan")
        macd_now  = tail4h["macd"].iloc[-1]  if not tail4h.empty else float("nan")
        rsi7_now  = tail4h["rsi7"].iloc[-1]  if not tail4h.empty else float("nan")
        
        ema20_str = f"{ema20_now:.2f}" if not pd.isna(ema20_now) else "N/A"
        macd_str = f"{macd_now:.4f}" if not pd.isna(macd_now) else "N/A"
        rsi7_str = f"{rsi7_now:.2f}" if not pd.isna(rsi7_now) else "N/A"
        
        return (
            f"{idx}. {symbol_str} {side_str} | Entry {entry_str} Current {cp_str} | "
            f"Qty {qty_str} | Notional {notional_str} USDT | PnL {pnl_pct:+.2f}% | PnL Amt {unrealized:+.2f} USDT | "
            f"Max Profit N/A | Leverage {leverage_str}x | Margin {margin_str} | Liq {liq_str} | Hold {hold_hours:.1f}h\n\n"
            f"current_price = {cp_str}, current_ema20 = {ema20_str}, "
            f"current_macd = {macd_str}, current_rsi (7 period) = {rsi7_str}\n\n"
            f"Open Interest: Latest: N/A Average: N/A\nFunding Rate: N/A\n\n"
            f"Intraday series (3‑minute intervals, oldest → latest):\n"
            f"Mid prices: [{mid_prices}]\n"
            f"EMA indicators (20‑period): [{ema_3m}]\n"
            f"MACD indicators: [{macd_3m}]\n"
            f"RSI indicators (7‑Period): [{rsi7_3m}]\n"
            f"RSI indicators (14‑Period): [{rsi14_3m}]\n"
            f"Volume: [{vol_3m}]\n\n"
            f"3m ATR (14‑period): {atr3m_14}\n\n"
            f"Longer‑term context (4‑hour timeframe):\n"
            f"20‑Period EMA: {ema20_4h} vs. 50‑Period EMA: {ema50_4h}\n"
            f"3‑Period ATR: {atr3_4h} vs. 14‑Period ATR: {atr14_4h}\n"
            f"Current Volume: {cur_vol_4h} vs. Average Volume: {avg_vol_4h}\n"
            f"MACD indicators: [{macd4h_arr}]\n"
            f"RSI indicators (14‑Period): [{rsi4h_arr}]\n"
        )

    def _format_candidate_rich(self, symbol: str, idx: int, ts: pd.Timestamp) -> str:
        df3m = self.data_3m.get(symbol, pd.DataFrame())
        df4h = self.data_4h.get(symbol, pd.DataFrame())
        latest4h = df4h[df4h["open_time"] <= ts].tail(1)
        current_price = latest4h.iloc[-1].close if not latest4h.empty else None
        ema20 = latest4h.iloc[-1].ema20 if not latest4h.empty else None
        macd_val = latest4h.iloc[-1].macd if not latest4h.empty else None
        rsi7_val = latest4h.iloc[-1].rsi7 if not latest4h.empty else None
        cp_str = f"{current_price:.2f}" if current_price is not None else "N/A"
        ema20_str = f"{ema20:.2f}" if ema20 is not None else "N/A"
        macd_str = f"{macd_val:.4f}" if macd_val is not None else "N/A"
        rsi7_str = f"{rsi7_val:.2f}" if rsi7_val is not None else "N/A"

        intraday = window_df(df3m, ts, self.config["intraday_lookback_hours"])
        intraday_tail = last_rows(intraday, 10)
        mid_prices = self._array_str(intraday_tail.get("close"))
        ema_3m = self._array_str(intraday_tail.get("ema20"))
        macd_3m = self._array_str(intraday_tail.get("macd"))
        rsi7_3m = self._array_str(intraday_tail.get("rsi7"))
        rsi14_3m = self._array_str(intraday_tail.get("rsi14"))
        vol_3m = self._array_str(intraday_tail.get("volume"))
        atr3m_14 = f"{intraday_tail['atr14'].iloc[-1]:.4f}" if not intraday_tail.empty else "N/A"

        ctx4h = df4h[df4h["open_time"] <= ts]
        tail4h = last_rows(ctx4h, 10)
        ema20_4h = f"{tail4h['ema20'].iloc[-1]:.4f}" if not tail4h.empty else "N/A"
        ema50_4h = f"{tail4h['ema50'].iloc[-1]:.4f}" if not tail4h.empty else "N/A"
        atr3_4h = "N/A"
        atr14_4h = f"{tail4h['atr14'].iloc[-1]:.4f}" if not tail4h.empty else "N/A"
        cur_vol_4h = f"{tail4h['volume'].iloc[-1]:.2f}" if not tail4h.empty else "N/A"
        avg_vol_4h = f"{tail4h['volume'].mean():.2f}" if not tail4h.empty else "N/A"
        macd4h_arr = self._array_str(tail4h.get("macd"))
        rsi4h_arr = self._array_str(tail4h.get("rsi14"))

        return (
            f"### {idx}. {symbol}\n\n"
            f"current_price = {cp_str}, current_ema20 = {ema20_str}, "
            f"current_macd = {macd_str}, current_rsi (7 period) = {rsi7_str}\n\n"
            f"Open Interest: Latest: N/A Average: N/A\n"
            f"Funding Rate: N/A\n\n"
            f"Intraday series (3‑minute intervals, oldest → latest):\n"
            f"Mid prices: [{mid_prices}]\n"
            f"EMA indicators (20‑period): [{ema_3m}]\n"
            f"MACD indicators: [{macd_3m}]\n"
            f"RSI indicators (7‑Period): [{rsi7_3m}]\n"
            f"RSI indicators (14‑Period): [{rsi14_3m}]\n"
            f"Volume: [{vol_3m}]\n\n"
            f"3m ATR (14‑period): {atr3m_14}\n\n"
            f"Longer‑term context (4‑hour timeframe):\n"
            f"20‑Period EMA: {ema20_4h} vs. 50‑Period EMA: {ema50_4h}\n"
            f"3‑Period ATR: {atr3_4h} vs. 14‑Period ATR: {atr14_4h}\n"
            f"Current Volume: {cur_vol_4h} vs. Average Volume: {avg_vol_4h}\n"
            f"MACD indicators: [{macd4h_arr}]\n"
            f"RSI indicators (14‑Period): [{rsi4h_arr}]\n"
        )

    @staticmethod
    def _array_str(series: Optional[pd.Series]) -> str:
        if series is None or series.empty:
            return ""
        return ", ".join(f"{v:.4f}" for v in series.tolist())

    def _current_price_map(self, timestamp: pd.Timestamp) -> Dict[str, float]:
        price_map: Dict[str, float] = {}
        for symbol, df in self.data_4h.items():
            latest = df[df["open_time"] <= timestamp].tail(1)
            if latest.empty:
                continue
            price_map[symbol] = float(latest.iloc[0].close)
        return price_map

    def _read_agent_positions(self, agent_name: str) -> List[Position]:
        return self.accounts[agent_name].get_positions()

    # ------------------------------------------------------------------ #
    # Agent decision handling
    # ------------------------------------------------------------------ #
    def get_agent_decision(self, agent_name: str, prompt: str, timestamp: Optional[pd.Timestamp] = None) -> TradingDecision:
        """
        Obtain a TradingDecision from a White Agent.
        
        If AI cache is enabled, checks cache first before calling the agent.

        The callable in agent_clients should accept a prompt string and return either
        a TradingDecision or a dict with the same shape.
        """
        # Try cache first
        if self.ai_cache and timestamp:
            timestamp_str = str(timestamp)
            cached_decision = self.ai_cache.get(agent_name, prompt, timestamp_str)
            if cached_decision is not None:
                print(f"  💾 [Cache HIT] {agent_name} at {timestamp_str}")
                return cached_decision
        
        # Cache miss - call AI
        handler = self.agent_clients.get(agent_name)
        if handler is None:
            raise RuntimeError(f"No agent client attached for '{agent_name}'")

        result = handler(prompt)
        if isinstance(result, TradingDecision):
            return result

        # If not TradingDecision, expect a dict-like structure
        if not isinstance(result, dict):
            raise TypeError(f"Agent '{agent_name}' returned unsupported type: {type(result)}")

        raw_actions = result.get("actions", [])
        if raw_actions is None:
            raw_actions = []
        if not isinstance(raw_actions, list):
            raise TypeError(f"Agent '{agent_name}' returned non-list actions: {type(raw_actions)}")

        actions = [
            a if isinstance(a, TradingAction) else TradingAction(**a)
            for a in raw_actions
        ]
        decision = TradingDecision(
            summary=result.get("summary", ""),
            reasoning=result.get("reasoning", ""),
            actions=actions,
        )
        if not decision.reasoning or not decision.reasoning.strip():
            raise ValueError(f"Agent '{agent_name}' must provide non-empty reasoning")
        
        # Store in cache
        if self.ai_cache and timestamp:
            timestamp_str = str(timestamp)
            self.ai_cache.put(agent_name, prompt, timestamp_str, decision)
        
        return decision

    # ------------------------------------------------------------------ #
    # Execution + bookkeeping
    # ------------------------------------------------------------------ #
    def execute_decision(
        self,
        agent_name: str,
        decision: TradingDecision,
        timestamp: pd.Timestamp,
    ) -> List[TradeEvent]:
        trades: List[TradeEvent] = []
        price_map = self._current_price_map(timestamp)
        account = self.accounts[agent_name]
        cycle_idx = len(self.equity_history[agent_name]) + 1

        for action in decision.actions:
            symbol = action.symbol.upper()
            if symbol not in price_map:
                continue
            price = price_map[symbol]
            if price is None or (isinstance(price, float) and math.isnan(price)) or price <= 0:
                print(f"  ⚠️  {agent_name} {action.action} {symbol}: skip, invalid price={price}")
                continue
            leverage = max(1, int(action.leverage))
            side = "long" if "long" in action.action else "short"

            # Convert notional -> quantity (nofx style). If model returns position_size_usd,
            # we derive base-asset quantity here so the backtest account can execute.
            # If model gives none or too large, we auto-size based on balance so it MUST place an order.
            max_notional = account.cash * leverage * 0.88 if hasattr(account, "cash") else 0.0
            pos_size = 0.0
            try:
                pos_size = float(getattr(action, "position_size_usd", 0.0)) if getattr(action, "position_size_usd", 0.0) else 0.0
            except Exception:
                pos_size = 0.0

            if max_notional > 0:
                if pos_size <= 0:
                    pos_size = max_notional  # auto-use the capped maximum if model did not provide
                if pos_size > max_notional:
                    print(
                        f"  ⚠️  {agent_name} {action.action} {symbol}: "
                        f"position_size_usd too large (${pos_size:.2f}), "
                        f"capping to ${max_notional:.2f} (cash=${account.cash:.2f}, lev={leverage}x)"
                    )
                    pos_size = max_notional
                    if hasattr(action, "position_size_usd"):
                        action.position_size_usd = pos_size

            if pos_size > 0 and price > 0:
                # Pre-check margin + fee; if still too high, scale down to fit cash
                fee_est = pos_size * 0.0004  # taker fee estimate 0.04%
                required_margin = pos_size / leverage
                total_needed = required_margin + fee_est
                if account.cash > 0 and total_needed > account.cash:
                    scale = (account.cash * 0.98) / total_needed  # leave 2% buffer
                    if scale > 0:
                        pos_size *= scale
                        if hasattr(action, "position_size_usd"):
                            action.position_size_usd = pos_size
                        required_margin = pos_size / leverage
                        fee_est = pos_size * 0.0004
                        total_needed = required_margin + fee_est
                        print(
                            f"  ⚠️  {agent_name} {action.action} {symbol}: scaled down notional to ${pos_size:.2f} "
                            f"(margin+fee now ${total_needed:.2f}, cash=${account.cash:.2f})"
                        )

                if total_needed > account.cash:
                    print(
                        f"  ❌ {agent_name} {action.action} {symbol}: insufficient cash for "
                        f"notional ${pos_size:.2f} (need margin+fee ${total_needed:.2f}, "
                        f"cash=${account.cash:.2f}, lev={leverage}x)"
                    )
                    continue

                action.quantity = pos_size / price
                print(
                    f"  📊 {agent_name} {action.action} {symbol}: "
                    f"position_size_usd=${pos_size:.2f} → quantity={action.quantity:.6f} @ price=${price:.2f}"
                )
                if action.quantity <= BacktestAccount.EPSILON:
                    raise RuntimeError(
                        f"[execute_decision] quantity too small after conversion: "
                        f"position_size_usd={pos_size}, price={price}"
                    )

            # If still no usable quantity, auto-skip to avoid failing open()
            if action.quantity <= BacktestAccount.EPSILON:
                print(
                    f"  ⚠️  {agent_name} {action.action} {symbol}: skip, quantity too small ({action.quantity})"
                )
                continue

            if action.action == "open_long":
                pos, fee, exec_price, err = account.open(
                    symbol, "long", action.quantity, leverage, price, int(timestamp.timestamp())
                )
                if err is not None:
                    print(f"  ❌ {agent_name} open_long {symbol} FAILED: {err}")
                elif err is None and pos:
                    print(f"  ✅ {agent_name} opened LONG {symbol}: qty={action.quantity}, leverage={leverage}x, price={exec_price:.2f}")
                    trades.append(
                        TradeEvent(
                            timestamp=int(timestamp.timestamp()),
                            symbol=symbol,
                            action="open_long",
                            side="long",
                            quantity=action.quantity,
                            price=exec_price,
                            fee=fee,
                            slippage=exec_price - price,
                            order_value=exec_price * action.quantity,
                            realized_pnl=0.0,
                            leverage=leverage,
                            cycle=cycle_idx,
                            position_after=pos.quantity,
                        )
                    )
            elif action.action == "open_short":
                pos, fee, exec_price, err = account.open(
                    symbol, "short", action.quantity, leverage, price, int(timestamp.timestamp())
                )
                if err is not None:
                    print(f"  ❌ {agent_name} open_short {symbol} FAILED: {err}")
                elif err is None and pos:
                    print(f"  ✅ {agent_name} opened SHORT {symbol}: qty={action.quantity}, leverage={leverage}x, price={exec_price:.2f}")
                    trades.append(
                        TradeEvent(
                            timestamp=int(timestamp.timestamp()),
                            symbol=symbol,
                            action="open_short",
                            side="short",
                            quantity=action.quantity,
                            price=exec_price,
                            fee=fee,
                            slippage=price - exec_price,
                            order_value=exec_price * action.quantity,
                            realized_pnl=0.0,
                            leverage=leverage,
                            cycle=cycle_idx,
                            position_after=pos.quantity,
                        )
                    )
            elif action.action == "close_long":
                qty = action.quantity or self._auto_close_qty(account, symbol, "long")
                if qty > 0:
                    realized, fee, exec_price, err = account.close(symbol, "long", qty, price)
                    if err is None:
                        remaining = self._auto_close_qty(account, symbol, "long")
                        trades.append(
                            TradeEvent(
                                timestamp=int(timestamp.timestamp()),
                                symbol=symbol,
                                action="close_long",
                                side="long",
                                quantity=qty,
                                price=exec_price,
                                fee=fee,
                                slippage=price - exec_price,
                                order_value=exec_price * qty,
                                realized_pnl=realized,
                                leverage=account.position_leverage(symbol, "long") or leverage,
                                cycle=cycle_idx,
                                position_after=remaining,
                            )
                        )
            elif action.action == "close_short":
                qty = action.quantity or self._auto_close_qty(account, symbol, "short")
                if qty > 0:
                    realized, fee, exec_price, err = account.close(symbol, "short", qty, price)
                    if err is None:
                        remaining = self._auto_close_qty(account, symbol, "short")
                        trades.append(
                            TradeEvent(
                                timestamp=int(timestamp.timestamp()),
                                symbol=symbol,
                                action="close_short",
                                side="short",
                                quantity=qty,
                                price=exec_price,
                                fee=fee,
                                slippage=exec_price - price,
                                order_value=exec_price * qty,
                                realized_pnl=realized,
                                leverage=account.position_leverage(symbol, "short") or leverage,
                                cycle=cycle_idx,
                                position_after=remaining,
                            )
                        )
            # wait/hold are ignored

        self.trade_history[agent_name].extend(trades)
        self._record_equity_point(agent_name, timestamp, price_map, cycle_idx)
        return trades

    def _auto_close_qty(self, account: BacktestAccount, symbol: str, side: str) -> float:
        key = account._position_key(symbol, side)
        pos = account.positions.get(key)
        return pos.quantity if pos else 0.0

    def _record_equity_point(
        self, agent_name: str, timestamp: pd.Timestamp, price_map: Dict[str, float], cycle_idx: int
    ):
        equity, unrealized, _ = self.accounts[agent_name].total_equity(price_map)
        initial = self.accounts[agent_name].initial_balance
        pnl_pct = (equity - initial) / initial * 100
        drawdown_pct = 0.0
        if self.equity_history[agent_name]:
            peak = max(p.equity for p in self.equity_history[agent_name])
            drawdown_pct = (peak - equity) / peak * 100 if peak > 0 else 0.0
        self.equity_history[agent_name].append(
            EquityPoint(
                timestamp=int(timestamp.timestamp()),
                equity=equity,
                available=self.accounts[agent_name].get_cash(),
                pnl=equity - initial,
                pnl_pct=pnl_pct,
                drawdown_pct=drawdown_pct,
                cycle=cycle_idx,
            )
        )

    # ------------------------------------------------------------------ #
    # Disclosure + parsing helpers
    # ------------------------------------------------------------------ #
    def store_round_decision(self, agent_name: str, cycle_idx: int, decision: TradingDecision):
        parsed = self._parse_reasoning_structure(decision.reasoning)
        round_decision = AgentRoundDecision(
            agent_name=agent_name,
            day=cycle_idx,
            round=self.current_round,
            market_view=parsed.get("market_view", ""),
            opponent_analysis=parsed.get("opponent_analysis"),
            strategy_adjustment=parsed.get("strategy_adjustment"),
            actions=decision.actions,
            full_reasoning=decision.reasoning,
        )
        self.round_decisions.append(round_decision)

    def _parse_reasoning_structure(self, reasoning: str) -> Dict:
        result: Dict = {}
        if "市场分析" in reasoning:
            try:
                part = reasoning.split("市场分析")[1].split("\n")[0]
                result["market_view"] = part.strip(":： ").strip()
            except Exception:
                result["market_view"] = reasoning[:120]
        if "对手分析" in reasoning:
            try:
                segment = reasoning.split("对手分析")[1]
                result["opponent_analysis"] = segment.split("\n\n")[0].strip()
            except Exception:
                result["opponent_analysis"] = None
        if "策略调整" in reasoning:
            try:
                segment = reasoning.split("策略调整")[1]
                result["strategy_adjustment"] = segment.split("\n\n")[0].strip()
            except Exception:
                result["strategy_adjustment"] = None
        return result

    def create_disclosure_package(self, cycle_idx: int, timestamp: pd.Timestamp) -> DisclosurePackage:
        self.current_round += 1
        leaderboard = self._get_current_leaderboard(timestamp)
        agents_summary = []
        for agent_name in self.agent_names:
            agent_decisions = [
                d for d in self.round_decisions if d.agent_name == agent_name and d.round == self.current_round - 1
            ]
            summary = {
                "name": agent_name,
                "market_views": [d.market_view for d in agent_decisions if d.market_view],
                "opponent_analysis": agent_decisions[-1].opponent_analysis if agent_decisions else None,
                "strategy_adjustment": agent_decisions[-1].strategy_adjustment if agent_decisions else None,
                "actions_summary": self._summarize_actions(agent_decisions),
                "positions": self._get_positions_snapshot(agent_name),
                "pnl_pct": self._calculate_pnl_pct(agent_name, timestamp),
                "equity": self._current_equity(agent_name, timestamp),
            }
            agents_summary.append(summary)

        disclosure = DisclosurePackage(
            round_number=self.current_round,
            disclosure_day=cycle_idx,
            leaderboard=leaderboard,
            agents_round_summary=agents_summary,
        )
        self.disclosure_packages.append(disclosure)
        return disclosure

    def _summarize_actions(self, decisions: List[AgentRoundDecision]) -> str:
        actions = []
        for d in decisions:
            for a in d.actions:
                actions.append(f"{a.action} {a.symbol} x{a.leverage}")
        return ", ".join(actions) if actions else "无"

    def _get_positions_snapshot(self, agent_name: str) -> str:
        positions = self.accounts[agent_name].get_positions()
        if not positions:
            return "无持仓"
        return "; ".join([f"{p.symbol} {p.side} {p.quantity:.4f} @ {p.entry_price:.2f}" for p in positions])

    def _calculate_pnl_pct(self, agent_name: str, timestamp: pd.Timestamp) -> float:
        price_map = self._current_price_map(timestamp)
        equity, _, _ = self.accounts[agent_name].total_equity(price_map)
        initial = self.accounts[agent_name].initial_balance
        return (equity - initial) / initial * 100

    def _current_equity(self, agent_name: str, timestamp: pd.Timestamp) -> float:
        price_map = self._current_price_map(timestamp)
        equity, _, _ = self.accounts[agent_name].total_equity(price_map)
        return equity

    def _get_current_leaderboard(self, timestamp: pd.Timestamp) -> List[Dict]:
        rankings = []
        for agent_name in self.agent_names:
            pnl_pct = self._calculate_pnl_pct(agent_name, timestamp)
            equity = self._current_equity(agent_name, timestamp)
            rankings.append({"name": agent_name, "pnl_pct": pnl_pct, "equity": equity})
        rankings.sort(key=lambda x: x["pnl_pct"], reverse=True)
        for i, r in enumerate(rankings, 1):
            r["rank"] = i
        return rankings

    # ------------------------------------------------------------------ #
    # Metrics + scoring
    # ------------------------------------------------------------------ #
    def calculate_sharpe_ratio(self, equity_points: List[EquityPoint]) -> float:
        if len(equity_points) < 2:
            return 0.0
        returns = []
        for prev, curr in zip(equity_points[:-1], equity_points[1:]):
            if prev.equity <= 0:
                continue
            r = (curr.equity - prev.equity) / prev.equity
            returns.append(r)
        if not returns:
            return 0.0
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / max(1, len(returns) - 1)
        std = math.sqrt(variance)
        if std == 0:
            return 0.0
        # Scale to annualized using 4h interval (~6 per day -> 2190 per year)
        scale = math.sqrt(2190)
        return (mean / std) * scale

    def _calculate_performance(self, agent_name: str) -> AgentPerformance:
        equity_points = self.equity_history[agent_name]
        if not equity_points:
            return AgentPerformance(
                agent_name=agent_name,
                strategy="",
                total_return_pct=0.0,
                total_return_usd=0.0,
                cagr=0.0,
                sharpe_ratio=0.0,
                max_drawdown_pct=0.0,
                volatility=0.0,
                sortino_ratio=0.0,
                total_trades=0,
                win_rate=0.0,
                profit_factor=0.0,
                avg_trades_per_day=0.0,
                total_score=0.0,
            )

        initial = self.accounts[agent_name].initial_balance
        final_equity = equity_points[-1].equity
        total_return_pct = (final_equity - initial) / initial * 100
        total_return_usd = final_equity - initial
        sharpe = self.calculate_sharpe_ratio(equity_points)
        max_drawdown = max((p.drawdown_pct for p in equity_points), default=0.0)
        trades = self.trade_history[agent_name]
        wins = [t for t in trades if t.realized_pnl > 0]
        losses = [t for t in trades if t.realized_pnl < 0]
        win_rate = len(wins) / len(trades) * 100 if trades else 0.0
        profit_factor = (
            (sum(t.realized_pnl for t in wins) / abs(sum(t.realized_pnl for t in losses)))
            if losses
            else float("inf") if wins else 0.0
        )
        # Approx days from decision count
        days = max(1, len(equity_points) / self.config["decisions_per_day"])

        performance = AgentPerformance(
            agent_name=agent_name,
            strategy="",
            total_return_pct=total_return_pct,
            total_return_usd=total_return_usd,
            cagr=total_return_pct / 100 / (days / 365),
            sharpe_ratio=sharpe,
            max_drawdown_pct=max_drawdown,
            volatility=0.0,
            sortino_ratio=0.0,
            total_trades=len(trades),
            win_rate=win_rate,
            profit_factor=profit_factor if profit_factor != float("inf") else 0.0,
            avg_trades_per_day=len(trades) / days,
        )

        performance = self._score_performance(performance)
        return performance

    def _score_performance(self, perf: AgentPerformance) -> AgentPerformance:
        perf.profitability_score = min(perf.cagr / 0.20, 1.0) if perf.cagr else 0.0
        perf.risk_management_score = max(1.0 - perf.max_drawdown_pct / 20.0, 0.0)
        perf.consistency_score = (perf.win_rate / 80.0 * 0.5) + (min(perf.profit_factor, 3.0) / 3.0 * 0.5)
        perf.efficiency_score = min(perf.sharpe_ratio / 2.0, 1.0)
        perf.robustness_score = max(1.0 - perf.volatility / 0.30, 0.0) if perf.volatility else 0.0
        trading_score = (
            perf.profitability_score * 0.25
            + perf.risk_management_score * 0.25
            + perf.consistency_score * 0.20
            + perf.efficiency_score * 0.20
            + perf.robustness_score * 0.10
        )
        perf.reasoning_score = perf.reasoning_quality.overall_reasoning_score if perf.reasoning_quality else 0.0
        perf.total_score = trading_score * 0.7 + perf.reasoning_score * 0.3
        return perf

    # Normalize metrics across agents and recompute total_score with normalized trading score.
    def _normalize_and_rescore(self, perfs: Dict[str, AgentPerformance]) -> Dict[str, AgentPerformance]:
        if not perfs:
            return perfs

        # Collect metric arrays
        metrics = {
            "total_return_pct": [],
            "sharpe_ratio": [],
            "max_drawdown_pct": [],
            "win_rate": [],
            "profit_factor": [],
            "cagr": [],
            "volatility": [],
        }
        for p in perfs.values():
            metrics["total_return_pct"].append(p.total_return_pct)
            metrics["sharpe_ratio"].append(p.sharpe_ratio)
            metrics["max_drawdown_pct"].append(p.max_drawdown_pct)
            metrics["win_rate"].append(p.win_rate)
            metrics["profit_factor"].append(p.profit_factor)
            metrics["cagr"].append(p.cagr)
            metrics["volatility"].append(p.volatility)

        def norm_list(arr):
            if not arr:
                return []
            lo, hi = min(arr), max(arr)
            if hi - lo < 1e-9:
                return [0.5] * len(arr)
            return [(x - lo) / (hi - lo) for x in arr]

        norm_map: Dict[str, Dict[str, float]] = {k: {} for k in metrics.keys()}
        for key, arr in metrics.items():
            normed = norm_list(arr)
            for agent_name, val in zip(perfs.keys(), normed):
                norm_map[key][agent_name] = val

        # Invert for "lower is better" metrics
        invert_keys = {"max_drawdown_pct", "volatility"}
        for k in invert_keys:
            for agent_name, val in norm_map[k].items():
                norm_map[k][agent_name] = 1.0 - val

        # Recompute a normalized trading score and total_score
        for agent_name, p in perfs.items():
            rt = norm_map["total_return_pct"][agent_name]
            sh = norm_map["sharpe_ratio"][agent_name]
            dd = norm_map["max_drawdown_pct"][agent_name]
            wr = norm_map["win_rate"][agent_name]
            pf = norm_map["profit_factor"][agent_name]
            cg = norm_map["cagr"][agent_name]
            vol = norm_map["volatility"][agent_name]

            normalized_trading = (
                rt * 0.25 +
                sh * 0.20 +
                wr * 0.15 +
                pf * 0.15 +
                dd * 0.15 +
                vol * 0.10
            )
            reasoning = p.reasoning_score or 0.0
            p.normalized_trading_score = normalized_trading  # type: ignore
            p.total_score = normalized_trading * 0.7 + reasoning * 0.3
        return perfs

    def _collect_reasoning_log(self, agent_name: str) -> str:
        """Concatenate all stored round decisions' reasoning for an agent."""
        logs = []
        for d in self.round_decisions:
            if d.agent_name != agent_name:
                continue
            summary = "; ".join([f"{a.action} {a.symbol} x{a.leverage}" for a in d.actions]) if d.actions else ""
            logs.append(
                f"[Cycle {d.round}] market_view={d.market_view or ''} actions={summary}\n{d.full_reasoning}"
            )
        return "\n\n".join(logs) if logs else "No reasoning records."

    def _collect_execution_summary(self, agent_name: str) -> Dict[str, float]:
        """Simple execution stats from trade history for prompt context."""
        trades = self.trade_history.get(agent_name, [])
        opens = [t for t in trades if "open" in t.action]
        closes = [t for t in trades if "close" in t.action]
        realized = sum(t.realized_pnl for t in trades)
        return {
            "total_trades": len(trades),
            "open_trades": len(opens),
            "close_trades": len(closes),
            "realized_pnl": realized,
        }

    def judge_performance_llm(self, performance: Dict[str, AgentPerformance]) -> tuple[str, Dict[str, float]]:
        """
        LLM-based reasoning scoring. Returns (text, {agent: reasoning_score[0,1]}).
        Model: TRADING_JUDGE_MODEL (default deepseek/deepseek-chat); API key/base from DEEPSEEK_/OPENAI_ envs.
        """
        model = os.getenv("TRADING_JUDGE_MODEL", "deepseek/deepseek-chat")
        api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        api_base = os.getenv("DEEPSEEK_API_BASE") or os.getenv("OPENAI_API_BASE")
        
        print(f"\n🤖 Green Agent Judge Configuration:")
        print(f"   Model: {model}")
        print(f"   API Key: {'✅ Set' if api_key else '❌ Missing'}")
        print(f"   API Base: {api_base if api_base else 'default'}")
        
        if not api_key:
            return "LLM judge skipped (missing API key).", {}

        sys_prompt = (
            "You are a trading competition judge. Evaluate agents on profitability, risk management, consistency, efficiency, "
            "overall total_score, AND give a reasoning_score [0,1] for explanation quality. "
            "Return short text AND JSON: {\"scores\":[{\"agent\":\"...\",\"reasoning_score\":0-1,\"note\":\"...\"}],"
            "\"winner\":\"...\",\"reason\":\"...\"}. Text <= 200 words."
        )
        perf_summary = []
        for name, perf in performance.items():
            if name == "_judge_text":
                continue
            perf_summary.append(
                {
                    "agent": name,
                    "total_return_pct": perf.total_return_pct,
                    "max_drawdown_pct": perf.max_drawdown_pct,
                    "sharpe_ratio": perf.sharpe_ratio,
                    "win_rate": perf.win_rate,
                    "profit_factor": perf.profit_factor,
                    "avg_trades_per_day": perf.avg_trades_per_day,
                    "total_score": perf.total_score,
                    "reasoning_log": self._collect_reasoning_log(name),
                    "execution_summary": self._collect_execution_summary(name),
                }
            )
        user_prompt = (
            "Evaluate these agent performances and reasonings. Each item contains metrics, "
            "full reasoning logs (all cycles), and execution summary (counts and realized pnl).\n"
            f"{json.dumps(perf_summary, indent=2)}\n"
            "Return JSON with scores as before, but reasoning_score should consider the provided reasoning_log quality.\n"
            "Also provide a brief paragraph summary."
        )

        try:
            # Direct HTTP call to DeepSeek (OpenAI-compatible API)
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            payload = {
                "model": "deepseek-chat",  # DeepSeek's model name (no prefix needed for direct API)
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
            }
            
            response = requests.post(
                f"{api_base}/v1/chat/completions" if api_base else "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            resp_json = response.json()
            content = resp_json["choices"][0]["message"]["content"]
            score_map: Dict[str, float] = {}
            import re
            try:
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    payload = json.loads(match.group(0))
                    for item in payload.get("scores", []):
                        agent = item.get("agent")
                        rs = item.get("reasoning_score")
                        if agent and isinstance(rs, (int, float)):
                            score_map[agent] = max(0.0, min(1.0, float(rs)))
            except Exception:
                score_map = {}
            return content, score_map
        except Exception as e:
            return f"LLM judge failed: {e}", {}

    # ------------------------------------------------------------------ #
    # Competition driver
    # ------------------------------------------------------------------ #
    def run_competition(self) -> Dict[str, AgentPerformance]:
        """Main 4h decision loop."""
        self._progress({"type": "stage", "stage": "load_and_prepare_data"})
        self.load_and_prepare_data()
        timestamps = pd.date_range(
            start=self.config["start_date"],
            end=self.config["end_date"],
            freq=self.config["decision_interval"].upper(),
            inclusive="left",
            tz="UTC",
        )
        
        # Limit to total_decision_cycles if specified
        max_cycles = self.config.get("total_decision_cycles")
        if max_cycles and max_cycles > 0:
            timestamps = timestamps[:max_cycles]
            print(f"\n🔄 Running {len(timestamps)} decision cycles (limited by config)...\n")
        else:
            print(f"\n🔄 Running {len(timestamps)} decision cycles...\n")

        for cycle_idx, ts in enumerate(timestamps, 1):
            print(f"\n{'='*80}")
            print(f"CYCLE {cycle_idx}/{len(timestamps)} at {ts}")
            print(f"{'='*80}")
            self._progress({"type": "cycle", "cycle_idx": cycle_idx, "total_cycles": len(timestamps), "timestamp": str(ts)})
            
            if cycle_idx in self.config["disclosure_cycles"]:
                self.create_disclosure_package(cycle_idx, ts)

            for agent_name in self.agent_names:
                self._progress({"type": "agent", "stage": "build_prompt", "agent": agent_name, "cycle_idx": cycle_idx})
                prompt = self.build_market_prompt(agent_name, cycle_idx, ts)
                self._progress({"type": "agent", "stage": "get_decision", "agent": agent_name, "cycle_idx": cycle_idx})
                decision = self.get_agent_decision(agent_name, prompt, timestamp=ts)
                self._progress({"type": "agent", "stage": "store_decision", "agent": agent_name, "cycle_idx": cycle_idx})
                self.store_round_decision(agent_name, cycle_idx, decision)
                self._progress({"type": "agent", "stage": "execute_decision", "agent": agent_name, "cycle_idx": cycle_idx})
                self.execute_decision(agent_name, decision, ts)
                self._progress({"type": "agent", "stage": "done", "agent": agent_name, "cycle_idx": cycle_idx})
        
        print(f"\n{'='*80}")
        print(f"✅ Completed {len(timestamps)} cycles. Calculating final performance...")
        print(f"{'='*80}\n")
        self._progress({"type": "stage", "stage": "calculate_performance"})
        
        # Print cache statistics
        if self.ai_cache:
            stats = self.ai_cache.stats()
            print(f"📊 AI Cache Statistics:")
            print(f"   Entries: {stats['entries']}")
            print(f"   Hits: {stats['hits']} | Misses: {stats['misses']}")
            print(f"   Hit Rate: {stats['hit_rate']}")
            print()

        # Final performance
        for agent_name in self.agent_names:
            self.performance[agent_name] = self._calculate_performance(agent_name)

        # LLM reasoning scoring: inject reasoning_score and recompute total_score
        judge_text, score_map = self.judge_performance_llm(self.performance)
        for agent_name, perf in self.performance.items():
            if agent_name in score_map:
                perf.reasoning_score = score_map[agent_name]
                # Note: _score_performance runs pre-normalized scoring; final total_score is set after normalization
                perf = self._score_performance(perf)
                self.performance[agent_name] = perf

        # Normalize across agents and recompute final total_score (normalized trading 70% + reasoning 30%)
        self.performance = self._normalize_and_rescore(self.performance)
        # store judge text for artifact use
        self.performance["_judge_text"] = judge_text  # type: ignore

        return self.performance

