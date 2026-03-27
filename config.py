"""
纳斯达克指数仓位管理分析系统配置
适用于：长期投资者 / 指数基金 / 低频调仓
"""
import os

# 代理配置
PROXY_HTTP = os.environ.get("PROXY_HTTP", "http://127.0.0.1:8118")
PROXY_SOCKS = os.environ.get("PROXY_SOCKS", "socks5://127.0.0.1:1080")

# 指数配置
INDEX_SYMBOL = "^IXIC"  # NASDAQ Composite
INDEX_ETF = "QQQ"        # 可选：纳指ETF
INDEX_NAME = "纳斯达克综合指数"

# ========== 投资风格参数 ==========
INVESTOR_STYLE = "long_term"
REBALANCE_FREQUENCY = "quarterly"  # 季度调仓

# ========== 技术指标参数 ==========
RSI_PERIOD = 14
RSI_OVERSOLD = 35        # 放宽超卖阈值
RSI_OVERBOUGHT = 65       # 放宽超买阈值
RSI_LOW = 45              # 偏低区域（适合积累）

MA_SHORT = 50             # 长期投资者用更长周期
MA_MEDIUM = 120
MA_LONG = 200            # 牛熊分界线

# ========== 仓位控制参数 ==========
MAX_POSITION_RATIO = 0.40
MIN_POSITION_RATIO = 0.05
ADD_POSITION_DROP_RATE = 0.08
ADD_POSITION_RSI = 40

# 回调幅度阈值
CORRECTION_MILD = 0.05
CORRECTION_MODERATE = 0.15  # 中度回调 15%
CORRECTION_DEEP = 0.25      # 深度回调 25%

# 交易成本考量
MIN_TRADE_SIGNAL_SCORE = 3
TRADE_COOLDOWN_DAYS = 30

# 通知配置 (飞书)
FEISHU_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/ba2567b1-6c2b-4320-b9db-9c4ada247b19"

# 数据源
DATA_SOURCE = "yfinance"
