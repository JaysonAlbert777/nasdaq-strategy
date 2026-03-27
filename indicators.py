"""
技术指标计算模块
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """计算RSI相对强弱指标"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_ma(prices: pd.Series, period: int) -> pd.Series:
    """计算移动平均线"""
    return prices.rolling(window=period).mean()


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """计算指数移动平均线"""
    return prices.ewm(span=period, adjust=False).mean()


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """计算MACD指标"""
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """计算布林带"""
    ma = calculate_ma(prices, period)
    std = prices.rolling(window=period).std()
    upper_band = ma + (std * std_dev)
    lower_band = ma - (std * std_dev)
    return upper_band, ma, lower_band


def calculate_support_resistance(prices: pd.Series, lookback: int = 20) -> Tuple[float, float]:
    """计算最近的支持位和阻力位"""
    recent_prices = prices.tail(lookback)
    resistance = recent_prices.max()
    support = recent_prices.min()
    return support, resistance


def calculate_volatility(prices: pd.Series, period: int = 20) -> float:
    """计算历史波动率 (年化)"""
    returns = prices.pct_change().dropna()
    daily_volatility = returns.rolling(window=period).std().iloc[-1]
    annualized_volatility = daily_volatility * np.sqrt(252)
    return annualized_volatility


def get_technical_indicators(df: pd.DataFrame, config) -> Dict:
    """
    计算并返回所有技术指标
    """
    close = df['Close']
    
    # RSI
    rsi = calculate_rsi(close, config.RSI_PERIOD).iloc[-1]
    
    # 移动平均线
    ma_short = calculate_ma(close, config.MA_SHORT).iloc[-1]
    ma_medium = calculate_ma(close, config.MA_MEDIUM).iloc[-1]
    ma_long = calculate_ma(close, config.MA_LONG).iloc[-1]
    
    # MACD
    macd, signal, histogram = calculate_macd(close)
    macd_value = macd.iloc[-1]
    macd_signal = signal.iloc[-1]
    macd_histogram = histogram.iloc[-1]
    
    # 布林带
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(close)
    bb_upper_value = bb_upper.iloc[-1]
    bb_lower_value = bb_lower.iloc[-1]
    
    # 支撑位和阻力位
    support, resistance = calculate_support_resistance(close)
    
    # 波动率
    volatility = calculate_volatility(close)
    
    # 当前价格位置 (在布林带中的位置)
    current_price = close.iloc[-1]
    bb_position = (current_price - bb_lower_value) / (bb_upper_value - bb_lower_value) if bb_upper_value != bb_lower_value else 0.5
    
    # 价格变化
    price_change_1d = close.pct_change().iloc[-1] * 100
    price_change_1w = (close.iloc[-1] / close.iloc[-6] - 1) * 100 if len(close) > 5 else 0
    price_change_1m = (close.iloc[-1] / close.iloc[-22] - 1) * 100 if len(close) > 21 else 0
    
    # 从高点回调幅度
    recent_high = close.tail(50).max()
    drawdown = (current_price - recent_high) / recent_high * 100
    
    return {
        'rsi': rsi,
        'ma_short': ma_short,
        'ma_medium': ma_medium,
        'ma_long': ma_long,
        'macd': macd_value,
        'macd_signal': macd_signal,
        'macd_histogram': macd_histogram,
        'bb_upper': bb_upper_value,
        'bb_lower': bb_lower_value,
        'bb_position': bb_position,
        'support': support,
        'resistance': resistance,
        'volatility': volatility,
        'current_price': current_price,
        'price_change_1d': price_change_1d,
        'price_change_1w': price_change_1w,
        'price_change_1m': price_change_1m,
        'drawdown': drawdown,
        'recent_high': recent_high
    }
