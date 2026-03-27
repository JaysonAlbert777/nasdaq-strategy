"""
纳斯达克指数数据获取模块
通过 Yahoo Finance API 获取指数数据
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional
import time
import json

from config import PROXY_HTTP


class NasdaqFetcher:
    """纳斯达克指数数据获取器"""
    
    BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    
    def __init__(self, symbol: str = "^IXIC", proxy: Optional[str] = None):
        self.symbol = symbol
        self.proxy = proxy or PROXY_HTTP
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
        })
    
    def fetch(self, period: str = "1y", interval: str = "1d", max_retries: int = 3) -> pd.DataFrame:
        """
        获取历史数据
        
        Args:
            period: 数据周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: 间隔 (1m, 5m, 15m, 30m, 60m, 1h, 1d, 1wk)
            max_retries: 最大重试次数
        """
        url = self.BASE_URL.format(symbol=self.symbol)
        params = {
            "interval": interval,
            "range": period,
            "includePrePost": "false",
            "events": "div,split"
        }
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    proxies={"http": self.proxy, "https": self.proxy},
                    timeout=20
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("chart", {}).get("result", [None])[0]
                    
                    if result is None:
                        raise ValueError(f"No data returned for {self.symbol}")
                    
                    timestamps = result.get("timestamp", [])
                    quote = result.get("indicators", {}).get("quote", [{}])[0]
                    
                    df = pd.DataFrame({
                        "Open": quote.get("open", []),
                        "High": quote.get("high", []),
                        "Low": quote.get("low", []),
                        "Close": quote.get("close", []),
                        "Volume": quote.get("volume", []),
                    }, index=pd.to_datetime(timestamps, unit="s"))
                    
                    df.index.name = "Date"
                    
                    # 清理数据
                    df = df.dropna()
                    df = df[df["Close"] > 0]
                    
                    return df
                
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = (attempt + 1) * 10
                    print(f"Rate limited, waiting {wait_time}s... ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                
                else:
                    print(f"HTTP {response.status_code}: {response.text[:100]}")
                    raise ValueError(f"HTTP {response.status_code}")
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"获取数据失败: {e}，{wait_time}秒后重试... ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    raise
        
        raise RuntimeError(f"Failed to fetch {self.symbol} after {max_retries} attempts")
    
    def get_current_price(self) -> float:
        """获取当前价格"""
        df = self.fetch(period="5d")
        return float(df["Close"].iloc[-1])
    
    def get_realtime_quote(self) -> Dict:
        """获取实时报价"""
        url = self.BASE_URL.format(symbol=self.symbol)
        params = {"interval": "1d", "range": "1d", "includePrePost": "false"}
        
        response = self.session.get(
            url,
            params=params,
            proxies={"http": self.proxy, "https": self.proxy},
            timeout=20
        )
        
        data = response.json()
        result = data.get("chart", {}).get("result", [{}])[0]
        meta = result.get("meta", {})
        
        return {
            "symbol": meta.get("symbol"),
            "name": meta.get("shortName"),
            "price": meta.get("regularMarketPrice"),
            "prev_close": meta.get("chartPreviousClose"),
            "change": meta.get("regularMarketChange", 0),
            "change_pct": meta.get("regularMarketChangePercent", 0),
            "day_high": meta.get("regularMarketDayHigh"),
            "day_low": meta.get("regularMarketDayLow"),
            "fifty_two_high": meta.get("fiftyTwoWeekHigh"),
            "fifty_two_low": meta.get("fiftyTwoWeekLow"),
            "volume": meta.get("regularMarketVolume"),
            "market_time": meta.get("regularMarketTime"),
        }


if __name__ == "__main__":
    fetcher = NasdaqFetcher()
    
    print("获取NASDAQ数据...")
    
    # 获取实时报价
    try:
        quote = fetcher.get_realtime_quote()
        print(f"\n实时报价:")
        print(f"  代码: {quote['symbol']}")
        print(f"  名称: {quote['name']}")
        print(f"  当前价: ${quote['price']}")
        print(f"  涨跌: {quote['change']:+.2f} ({quote['change_pct']:+.2f}%)")
        print(f"  日高/日低: ${quote['day_high']} / ${quote['day_low']}")
        print(f"  52周高/低: ${quote['fifty_two_high']} / ${quote['fifty_two_low']}")
    except Exception as e:
        print(f"实时报价获取失败: {e}")
    
    # 获取历史数据
    try:
        df = fetcher.fetch(period="6mo")
        print(f"\n历史数据 (6个月):")
        print(f"  数据点数: {len(df)}")
        print(f"  最新收盘: ${df['Close'].iloc[-1]:.2f}")
        print(df.tail())
    except Exception as e:
        print(f"历史数据获取失败: {e}")
