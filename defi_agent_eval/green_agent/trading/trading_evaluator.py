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
from typing import Callable, Dict, List, Optional, Tuple

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


DEFAULT_CONFIG: Dict = {
    # Broader candidate set so agents can self-select
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
    "start_date": "2025-11-14",
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
    ):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.agent_names = agent_names
        self.agent_clients = agent_clients or {}

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

        # Header
        prompt_lines = [
            f"Time: {decision_time} | Cycle: #{cycle_idx} | Runtime: {runtime_days:.1f}d",
        ]

        # BTC headline if available
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
        current_price = price_map.get(pos.symbol, pos.entry_price)
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

        return (
            f"{idx}. {pos.symbol} {pos.side.upper()} | Entry {pos.entry_price:.2f} Current {current_price:.2f} | "
            f"Qty {pos.quantity:.4f} | Notional {notional:.2f} USDT | PnL {pnl_pct:+.2f}% | PnL Amt {unrealized:+.2f} USDT | "
            f"Max Profit N/A | Leverage {pos.leverage}x | Margin {pos.margin:.2f} | Liq {pos.liquidation_price:.2f} | Hold {hold_hours:.1f}h\n\n"
            f"current_price = {current_price:.2f}, current_ema20 = {tail4h['ema20'].iloc[-1]:.2f if not tail4h.empty else 'N/A'}, "
            f"current_macd = {tail4h['macd'].iloc[-1]:.4f if not tail4h.empty else 'N/A'}, current_rsi (7 period) = {tail4h['rsi7'].iloc[-1]:.2f if not tail4h.empty else 'N/A'}\n\n"
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
            f"current_price = {current_price:.2f if current_price else 'N/A'}, current_ema20 = {ema20:.2f if ema20 else 'N/A'}, "
            f"current_macd = {macd_val:.4f if macd_val else 'N/A'}, current_rsi (7 period) = {rsi7_val:.2f if rsi7_val else 'N/A'}\n\n"
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
    def get_agent_decision(self, agent_name: str, prompt: str) -> TradingDecision:
        """
        Obtain a TradingDecision from a White Agent.

        The callable in agent_clients should accept a prompt string and return either
        a TradingDecision or a dict with the same shape.
        """
        handler = self.agent_clients.get(agent_name)
        if handler is None:
            return TradingDecision(summary="hold", reasoning="no agent attached", actions=[])

        result = handler(prompt)
        if isinstance(result, TradingDecision):
            return result

        # Gracefully handle plain dicts
        actions = [
            TradingAction(**a) if not isinstance(a, TradingAction) else a
            for a in result.get("actions", [])
        ]
        return TradingDecision(
            summary=result.get("summary", ""),
            reasoning=result.get("reasoning", ""),
            actions=actions,
        )

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
            leverage = max(1, int(action.leverage))
            side = "long" if "long" in action.action else "short"

            if action.action == "open_long":
                pos, fee, exec_price, err = account.open(
                    symbol, "long", action.quantity, leverage, price, int(timestamp.timestamp())
                )
                if err is None and pos:
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
                if err is None and pos:
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

    # ------------------------------------------------------------------ #
    # Competition driver
    # ------------------------------------------------------------------ #
    def run_competition(self) -> Dict[str, AgentPerformance]:
        """Main 4h decision loop."""
        self.load_and_prepare_data()
        timestamps = pd.date_range(
            start=self.config["start_date"],
            end=self.config["end_date"],
            freq=self.config["decision_interval"].upper(),
            inclusive="left",
        )

        for cycle_idx, ts in enumerate(timestamps, 1):
            if cycle_idx in self.config["disclosure_cycles"]:
                self.create_disclosure_package(cycle_idx, ts)

            for agent_name in self.agent_names:
                prompt = self.build_market_prompt(agent_name, cycle_idx, ts)
                decision = self.get_agent_decision(agent_name, prompt)
                self.store_round_decision(agent_name, cycle_idx, decision)
                self.execute_decision(agent_name, decision, ts)

        # Final performance
        for agent_name in self.agent_names:
            self.performance[agent_name] = self._calculate_performance(agent_name)
        return self.performance

