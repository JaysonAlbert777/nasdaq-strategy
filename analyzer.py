"""
纳斯达克指数分析引擎
适用：长期投资者 / 指数基金 / 低频调仓
"""

import pandas as pd
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from config import *
from indicators import get_technical_indicators
from fetcher import NasdaqFetcher


class NasdaqAnalyzer:
    """纳斯达克指数分析器（长期投资者版）"""
    
    def __init__(self, symbol: str = INDEX_SYMBOL):
        self.symbol = symbol
        self.fetcher = NasdaqFetcher(symbol=symbol)
        self.last_trade_date = None  # 上次交易日期
        self.last_trade_score = None  # 上次交易评分
    
    def get_data(self, period: str = "1y") -> pd.DataFrame:
        """获取历史数据（长期投资者用1年数据看中期趋势）"""
        return self.fetcher.fetch(period=period)
    
    def analyze(self) -> Dict:
        """执行完整分析"""
        # 获取数据
        df = self.get_data(period="1y")
        
        # 计算指标
        indicators = get_technical_indicators(df, config)
        
        # 生成信号
        signals = self._generate_signals(indicators)
        
        # 仓位建议（长期投资者版）
        position_advice = self._get_position_advice(indicators)
        
        # 综合建议
        overall = self._get_overall_recommendation(signals, position_advice, indicators)
        
        return {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'symbol': self.symbol,
            'index_name': INDEX_NAME,
            'investor_style': INVESTOR_STYLE,
            'indicators': indicators,
            'signals': signals,
            'position_advice': position_advice,
            'overall': overall
        }
    
    def _generate_signals(self, indicators: Dict) -> Dict:
        """生成技术信号（长期投资者版，减少噪音）"""
        signals = {
            'trend': 'NEUTRAL',
            'momentum': 'NEUTRAL',
            'volatility': 'NORMAL',
            'rsi_signal': 'NEUTRAL',
            'macd_signal': 'NEUTRAL',
            'signal_strength': 'WEAK'  # 信号强度：WEAK / MODERATE / STRONG
        }
        
        price = indicators['current_price']
        ma_short = indicators['ma_short']
        ma_medium = indicators['ma_medium']
        ma_long = indicators['ma_long']
        
        # 趋势判断（长期投资者用更长周期）
        if price > ma_long and ma_short > ma_medium:
            signals['trend'] = 'UP'
        elif price < ma_long and ma_short < ma_medium:
            signals['trend'] = 'DOWN'
        
        # RSI信号（阈值已放宽）
        rsi = indicators['rsi']
        if rsi > RSI_OVERBOUGHT:
            signals['rsi_signal'] = 'OVERBOUGHT'
        elif rsi < RSI_OVERSOLD:
            signals['rsi_signal'] = 'OVERSOLD'
        
        # MACD信号
        macd = indicators['macd']
        macd_signal = indicators['macd_signal']
        if macd > macd_signal and indicators['macd_histogram'] > 0:
            signals['macd_signal'] = 'BULLISH'
        elif macd < macd_signal and indicators['macd_histogram'] < 0:
            signals['macd_signal'] = 'BEARISH'
        
        # 动量判断
        if signals['trend'] == 'UP' and signals['macd_signal'] == 'BULLISH':
            signals['momentum'] = 'BULLISH'
        elif signals['trend'] == 'DOWN' and signals['macd_signal'] == 'BEARISH':
            signals['momentum'] = 'BEARISH'
        
        # 波动率判断
        volatility = indicators['volatility']
        if volatility > 0.3:
            signals['volatility'] = 'HIGH'
        elif volatility < 0.15:
            signals['volatility'] = 'LOW'
        
        # 信号强度评估（长期投资者用，减少频繁交易）
        signal_count = 0
        if signals['trend'] == 'UP':
            signal_count += 2
        elif signals['trend'] == 'DOWN':
            signal_count -= 2
        
        if signals['rsi_signal'] == 'OVERSOLD':
            signal_count += 1
        elif signals['rsi_signal'] == 'OVERBOUGHT':
            signal_count -= 1
        
        if signals['macd_signal'] == 'BULLISH':
            signal_count += 1
        elif signals['macd_signal'] == 'BEARISH':
            signal_count -= 1
        
        if abs(indicators['drawdown']) >= CORRECTION_MODERATE * 100:
            signal_count += 1
        
        if signal_count >= 3:
            signals['signal_strength'] = 'STRONG'
        elif signal_count >= 1:
            signals['signal_strength'] = 'MODERATE'
        
        return signals
    
    def _get_position_advice(self, indicators: Dict) -> Dict:
        """获取仓位建议（长期投资者版：积累为主，减少交易）"""
        advice = {
            'current_position_ratio': 0,
            'max_position_ratio': MAX_POSITION_RATIO,
            'min_position_ratio': MIN_POSITION_RATIO,
            'add_position_triggered': False,
            'reduce_position_triggered': False,
            'should_hold': True,  # 默认持有不动
            'trade_triggered': False,
            'reasons': []
        }
        
        price = indicators['current_price']
        recent_high = indicators['recent_high']
        drawdown = indicators['drawdown']
        rsi = indicators['rsi']
        volatility = indicators['volatility']
        
        # ========== 基础仓位（根据趋势，长期投资者偏高仓位）==========
        if indicators['ma_long'] and price > indicators['ma_long']:
            base_ratio = 0.30  # 上涨趋势，基础仓位30%
        elif price < indicators['ma_long']:
            base_ratio = 0.15  # 下跌趋势，基础仓位15%
        else:
            base_ratio = 0.20  # 中性，基础仓位20%
        
        # ========== 加仓条件（长期投资者：不追求精确底部，分批积累）==========
        add_reasons = []
        
        # 1. 中度以上回调（长期投资者的主要买入机会）
        if abs(drawdown) >= CORRECTION_MODERATE * 100:
            add_reasons.append(f"从高点回调{int(abs(drawdown))}%，已达中度回调")
            base_ratio += 0.05
        
        # 2. 深度回调（极度关注）
        if abs(drawdown) >= CORRECTION_DEEP * 100:
            add_reasons.append(f"🔔 从高点回调{int(abs(drawdown))}%，深度回调，战略布局时机")
            base_ratio += 0.10
        
        # 3. RSI偏低（适合积累）
        if rsi < RSI_LOW:
            add_reasons.append(f"RSI={rsi:.1f}，处于偏低区域，适合积累")
            base_ratio += 0.03
        
        # ========== 减仓条件（长期投资者很少减仓，仅在极端情况）==========
        reduce_reasons = []
        
        # 1. RSI极端超买
        if rsi > 75:
            reduce_reasons.append(f"RSI={rsi:.1f}，极度超买")
            base_ratio -= 0.10
        
        # 2. 波动率极高
        if volatility > 0.40:
            reduce_reasons.append(f"波动率={volatility*100:.1f}%，风险加剧")
            base_ratio -= 0.05
        
        # 限制仓位范围
        advice['current_position_ratio'] = max(MIN_POSITION_RATIO, min(MAX_POSITION_RATIO, base_ratio))
        advice['add_position_triggered'] = len(add_reasons) > 0 and base_ratio > 0.20
        advice['reduce_position_triggered'] = len(reduce_reasons) > 0 and base_ratio < 0.15
        advice['should_hold'] = not advice['add_position_triggered'] and not advice['reduce_position_triggered']
        advice['trade_triggered'] = advice['add_position_triggered'] or advice['reduce_position_triggered']
        advice['reasons'] = {
            'add': add_reasons,
            'reduce': reduce_reasons
        }
        
        return advice
    
    def _get_overall_recommendation(self, signals: Dict, position_advice: Dict, indicators: Dict) -> Dict:
        """综合建议（长期投资者版）"""
        score = 0
        factors = []
        
        # 趋势得分（最重要）
        if signals['trend'] == 'UP':
            score += 2
            factors.append("✅ 长期趋势向上（价格>MA200）")
        elif signals['trend'] == 'DOWN':
            score -= 2
            factors.append("❌ 长期趋势向下，谨慎积累")
        
        # RSI得分（长期投资者关注积累时机）
        rsi = indicators['rsi']
        if rsi < RSI_OVERSOLD:
            score += 2
            factors.append(f"✅ RSI超卖({rsi:.1f})，适合积累")
        elif rsi < RSI_LOW:
            score += 1
            factors.append(f"👍 RSI偏低({rsi:.1f})，适合定投积累")
        elif rsi > RSI_OVERBOUGHT:
            score -= 1
            factors.append(f"👀 RSI偏高({rsi:.1f})，无需激进加仓")
        
        # 回调幅度（长期投资者最重要的买入信号）
        drawdown = indicators['drawdown']
        if abs(drawdown) >= CORRECTION_MODERATE * 100:
            score += 2
            factors.append(f"📉 已回调{int(abs(drawdown))}%，中度回调积累机会")
        if abs(drawdown) >= CORRECTION_DEEP * 100:
            score += 3
            factors.append(f"🔔 深幅回调{int(abs(drawdown))}%，战略布局窗口")
        
        # MACD得分
        if signals['macd_signal'] == 'BULLISH':
            score += 1
            factors.append("✅ MACD向好")
        elif signals['macd_signal'] == 'BEARISH':
            score -= 1
            factors.append("👀 MACD走弱")
        
        # ========== 综合评级（长期投资者版）==========
        if score >= 5:
            rating = "强烈推荐积累"
            action = "分批建仓/加仓，战略布局窗口"
        elif score >= 2:
            rating = "建议积累"
            action = "持有或小幅加仓"
        elif score >= -1:
            rating = "中性持有"
            action = "保持定投节奏，不追涨"
        elif score >= -3:
            rating = "建议观望"
            action = "减少新增投入，等待趋势明朗"
        else:
            rating = "谨慎"
            action = "耐心等待，不急于入场"
        
        return {
            'score': score,
            'rating': rating,
            'action': action,
            'factors': factors,
            'should_trade': abs(score) >= MIN_TRADE_SIGNAL_SCORE,
            'trade_reason': self._check_trade_cooldown(score)
        }
    
    def _check_trade_cooldown(self, score: int) -> Optional[str]:
        """检查是否在交易冷却期"""
        if self.last_trade_date is not None:
            days_since_trade = (datetime.now() - self.last_trade_date).days
            if days_since_trade < TRADE_COoldown_DAYS:
                return f"交易冷却期内（{days_since_trade}/{TRADE_COoldown_DAYS}天），建议观望"
        return None


def generate_report(analysis_result: Dict) -> str:
    """生成分析报告"""
    ind = analysis_result['indicators']
    sig = analysis_result['signals']
    pos = analysis_result['position_advice']
    overall = analysis_result['overall']
    
    change_1d = f"+{ind['price_change_1d']:.2f}%" if ind['price_change_1d'] >= 0 else f"{ind['price_change_1d']:.2f}%"
    change_1w = f"+{ind['price_change_1w']:.2f}%" if ind['price_change_1w'] >= 0 else f"{ind['price_change_1w']:.2f}%"
    change_1m = f"+{ind['price_change_1m']:.2f}%" if ind['price_change_1m'] >= 0 else f"{ind['price_change_1m']:.2f}%"
    
    report = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 纳斯达克指数分析报告
🏷️ 投资风格: 长期投资 · 指数基金 · 低频调仓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🕐 更新时间: {analysis_result['timestamp']}

【价格概览】
• 当前价格: {ind['current_price']:.2f}
• 日涨跌: {change_1d}
• 周涨跌: {change_1w}
• 月涨跌: {change_1m}
• 从高点回调: {ind['drawdown']:.2f}%

【技术指标】
• RSI(14): {ind['rsi']:.1f} {'🔴超买' if ind['rsi'] > 65 else '🟢偏低' if ind['rsi'] < 45 else ''}
• MA50: {ind['ma_short']:.2f}
• MA120: {ind['ma_medium']:.2f}
• MA200: {ind['ma_long']:.2f} {'✅牛熊线上方' if ind['current_price'] > ind['ma_long'] else '❌牛熊线下方'}
• 布林带: {ind['bb_lower']:.2f} ~ {ind['bb_upper']:.2f}
• 波动率: {ind['volatility']*100:.1f}%

【信号判断】
• 趋势: {'📈上升' if sig['trend'] == 'UP' else '📉下降' if sig['trend'] == 'DOWN' else '➡️中性'}
• 信号强度: {'🟢强烈' if sig['signal_strength'] == 'STRONG' else '🟡中等' if sig['signal_strength'] == 'MODERATE' else '⚪较弱'}
• RSI信号: {'🔴超买' if sig['rsi_signal'] == 'OVERBOUGHT' else '🟢超卖' if sig['rsi_signal'] == 'OVERSOLD' else '➖中性'}
• MACD: {'🟢金叉' if sig['macd_signal'] == 'BULLISH' else '🔴死叉' if sig['macd_signal'] == 'BEARISH' else '➖中性'}

【仓位建议】
• 推荐仓位: {pos['current_position_ratio']*100:.0f}%
• 仓位范围: {pos['min_position_ratio']*100:.0f}% ~ {pos['max_position_ratio']*100:.0f}%
• 操作: {'📈 加仓' if pos['add_position_triggered'] else '📉 减仓' if pos['reduce_position_triggered'] else '➡️ 持有'}

"""
    
    if pos['reasons']['add']:
        report += "📈 加仓理由:\n"
        for reason in pos['reasons']['add']:
            report += f"   • {reason}\n"
    
    if pos['reasons']['reduce']:
        report += "📉 减仓理由:\n"
        for reason in pos['reasons']['reduce']:
            report += f"   • {reason}\n"
    
    cooldown_msg = ""
    if overall.get('trade_reason'):
        cooldown_msg = f"\n⏰ {overall['trade_reason']}"
    
    report += f"""
【综合评级】
• 评分: {overall['score']}分 ({overall['rating']})
• 操作建议: {overall['action']}{cooldown_msg}

【决策因素】
"""
    for factor in overall['factors']:
        report += f"   {factor}\n"
    
    report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 长期投资者提示:
   • 指数基金更适合定投积累，不需精确择时
   • 深度回调(>25%)是战略布局窗口
   • 建议季度调仓，避免频繁交易
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    return report


def main():
    """主函数"""
    print("正在获取纳斯达克指数数据...")
    analyzer = NasdaqAnalyzer()
    
    try:
        result = analyzer.analyze()
        report = generate_report(result)
        print(report)
        
        import json
        from datetime import datetime
        
        output_file = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 详细数据已保存到: {output_file}")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
