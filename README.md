# 纳斯达克指数仓位管理分析系统

一个自动化的纳斯达克指数分析工具，支持技术指标分析、仓位建议和定时运行。

## 功能特性

- 📊 **技术指标分析**: RSI、MACD、布林带、移动平均线等
- 📈 **趋势判断**: 基于多周期均线的趋势识别
- 💹 **仓位建议**: 根据市场状况提供科学的仓位控制建议
- 🔔 **加仓减仓提示**: 识别回调买点和管理风险
- ⏰ **定时任务**: 支持循环和定时运行模式
- 📱 **通知推送**: 支持飞书机器人通知

## 安装

```bash
cd nasdaq-strategy
pip install -r requirements.txt
```

## 快速开始

### 单次分析

```bash
python scheduler.py --mode once
```

### 定时循环运行

```bash
# 每6小时运行一次
python scheduler.py --mode loop --interval 6

# 指定最大迭代次数
python scheduler.py --mode loop --interval 6 --iterations 10
```

### 配置飞书通知

```bash
python scheduler.py --mode once --feishu "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
```

## 仓位控制策略说明

### 基础仓位规则

| 市场状态 | 基础仓位 |
|---------|---------|
| 上涨趋势 (价格>MA200, MA20>MA60) | 25% |
| 下跌趋势 (价格<MA200, MA20<MA60) | 10% |
| 中性状态 | 15% |

### 加仓条件

- **中度回调 (≥10%)**: 从高点回调10%以上，视为较好买点
- **RSI超卖 (<30)**: 强烈加仓信号
- **RSI偏低 (<40)**: 适度加仓信号

### 减仓条件

- **RSI超买 (>70)**: 考虑减仓锁定利润
- **波动率过高 (>35%)**: 降低仓位控制风险
- **价格偏离均线过远 (>10%)**: 部分止盈

## 技术指标说明

### RSI (相对强弱指数)
- 超买区: >70
- 超卖区: <30
- 偏低区: <40 (适合加仓)
- 偏高区: >60 (注意风险)

### MACD
- 金叉: MACD线从下穿越信号线 → 看涨
- 死叉: MACD线从上穿越信号线 → 看跌

### 移动平均线
- MA20: 短期趋势
- MA60: 中期趋势
- MA200: 长期趋势 (牛熊分界线)

## 项目结构

```
nasdaq-strategy/
├── config.py        # 配置文件
├── indicators.py    # 技术指标计算
├── analyzer.py     # 分析引擎
├── scheduler.py    # 定时任务调度
├── requirements.txt # 依赖列表
└── README.md        # 本文件
```

## 定时任务设置 (Linux Cron)

编辑 crontab:

```bash
crontab -e
```

添加以下行 (每天早上9点运行):

```cron
0 9 * * * cd /path/to/nasdaq-strategy && python scheduler.py --mode once --feishu "your-webhook-url" >> /path/to/nasdaq-strategy/cron.log 2>&1
```

## 注意事项

1. 本工具仅供参考，不构成投资建议
2. 股票投资有风险，决策请谨慎
3. 建议结合其他信息源综合判断
4. 定期检查和调整策略参数
