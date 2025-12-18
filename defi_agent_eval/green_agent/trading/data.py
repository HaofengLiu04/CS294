"""
Market data utilities for the trading Green Agent.

We fetch historical klines directly from the public Binance REST endpoint to
avoid API key requirements. Data are returned as pandas DataFrames with
standardized columns plus pre-computed technical indicators.
"""

from __future__ import annotations

import time
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests


# Mapping of interval string to seconds for convenience
INTERVAL_TO_SECONDS = {
    "1m": 60,
    "3m": 180,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "2h": 7200,
    "4h": 14400,
    "1d": 86400,
}


class BinanceHTTPFetcher:
    """
    Lightweight Binance kline downloader that uses the public REST endpoint.
    This avoids the need for API keys while still providing reliable historical
    data for backtests.
    """

    BASE_URL = "https://api.binance.com/api/v3/klines"

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()

    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """
        Download klines between two datetimes (inclusive of start, exclusive of end).
        """
        start_ms = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000)
        all_rows: List[List] = []
        current_start = start_ms

        while current_start < end_ms:
            params = {
                "symbol": symbol,
                "interval": interval,
                "startTime": current_start,
                "endTime": end_ms,
                "limit": limit,
            }
            # Increase timeout and add retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    resp = self.session.get(self.BASE_URL, params=params, timeout=30)
                    resp.raise_for_status()
                    rows = resp.json()
                    break
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt < max_retries - 1:
                        print(f"⚠️  Timeout fetching {symbol} {interval}, retrying ({attempt + 1}/{max_retries})...")
                        time.sleep(2)
                        continue
                    else:
                        print(f"❌ Failed to fetch {symbol} {interval} after {max_retries} attempts")
                        raise
            if not rows:
                break

            all_rows.extend(rows)
            last_open_time = rows[-1][0]
            # Advance to next candle
            step_ms = INTERVAL_TO_SECONDS.get(interval, 0) * 1000
            if step_ms <= 0:
                break
            current_start = last_open_time + step_ms
            time.sleep(0.25)  # be nice to the API

        return self._to_dataframe(all_rows)

    @staticmethod
    def _to_dataframe(rows: List[List]) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame(columns=["open_time", "open", "high", "low", "close", "volume"])

        df = pd.DataFrame(
            rows,
            columns=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base_volume",
                "taker_buy_quote_volume",
                "ignore",
            ],
        )
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        numeric_cols = ["open", "high", "low", "close", "volume"]
        df[numeric_cols] = df[numeric_cols].astype(float)
        return df[["open_time", "open", "high", "low", "close", "volume"]]


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add EMA/MACD/RSI/ATR columns to the given OHLCV DataFrame.
    The input DataFrame must contain columns: open, high, low, close, volume.
    """
    result = df.copy()
    close = result["close"]
    high = result["high"]
    low = result["low"]

    # EMA
    result["ema20"] = close.ewm(span=20, adjust=False).mean()
    result["ema50"] = close.ewm(span=50, adjust=False).mean()

    # MACD (12, 26, 9)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    result["macd"] = ema12 - ema26
    result["macd_signal"] = result["macd"].ewm(span=9, adjust=False).mean()
    result["macd_hist"] = result["macd"] - result["macd_signal"]

    # RSI (7, 14)
    for period in (7, 14):
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        rs = avg_gain / (avg_loss.replace(0, 1e-9))
        result[f"rsi{period}"] = 100 - (100 / (1 + rs))

    # ATR (14)
    tr1 = (high - low).abs()
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    result["atr14"] = tr.rolling(window=14, min_periods=14).mean()

    return result


def window_df(df: pd.DataFrame, end: datetime, hours: int) -> pd.DataFrame:
    """Return the slice of df within the trailing `hours` window ending at `end`."""
    start_ts = end - timedelta(hours=hours)
    mask = (df["open_time"] >= start_ts) & (df["open_time"] <= end)
    return df.loc[mask].copy()


def last_rows(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Return the last n rows safely."""
    if df.empty:
        return df
    return df.tail(n)


