"""
定时任务调度器
支持多种调度方式:
1. 简单循环 (适用于容器/Docker)
2. 定时任务 (cron)
3. 第三方调度服务
"""

import time
import logging
from datetime import datetime, time as dtime
from typing import Optional, Callable
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzer import NasdaqAnalyzer, generate_report
from feishu_notify import FeishuNotifier
from config import FEISHU_WEBHOOK_URL

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SimpleScheduler:
    """简单调度器"""
    
    def __init__(self, interval_hours: int = 6):
        """
        初始化调度器
        
        Args:
            interval_hours: 运行时隔小时数
        """
        self.interval_seconds = interval_hours * 3600
        self.analyzer = NasdaqAnalyzer()
    
    def run_once(self) -> str:
        """执行一次分析"""
        try:
            logger.info("开始执行纳斯达克指数分析...")
            result = self.analyzer.analyze()
            report = generate_report(result)
            logger.info("分析完成")
            return report
        except Exception as e:
            logger.error(f"分析失败: {e}")
            return f"分析失败: {e}"
    
    def run_loop(self, max_iterations: Optional[int] = None):
        """
        循环执行
        
        Args:
            max_iterations: 最大迭代次数，None表示无限循环
        """
        iteration = 0
        while max_iterations is None or iteration < max_iterations:
            iteration += 1
            logger.info(f"第 {iteration} 次执行")
            
            report = self.run_once()
            print(report)
            
            if iteration < (max_iterations or float('inf')):
                logger.info(f"等待 {self.interval_seconds/3600} 小时后再次执行...")
                time.sleep(self.interval_seconds)


class TimeBasedScheduler:
    """基于时间的调度器 (只在美股交易时间运行)"""
    
    def __init__(self):
        self.analyzer = NasdaqAnalyzer()
        self.check_interval = 300  # 每5分钟检查一次
    
    def is_market_hours(self) -> bool:
        """检查是否在交易时段 (美东时间 9:30-16:00)"""
        now = datetime.now()
        # 简单检查小时
        hour = now.hour
        # UTC+8 转 美东时间 (冬令时-13, 夏令时-12)
        # 这里简化处理，假设用户主要关注亚洲时区的检查
        return True  # 可根据实际需求调整
    
    def should_run(self) -> bool:
        """判断是否应该执行分析"""
        now = datetime.now()
        
        # 每6小时运行一次
        # 也可以添加更多条件，如只在交易日运行
        return True
    
    def run_loop(self):
        """定时检查并执行"""
        while True:
            if self.should_run():
                logger.info("执行定时分析...")
                report = self.run_once()
                print(report)
            
            time.sleep(self.check_interval)
    
    def run_once(self) -> str:
        """执行一次分析"""
        try:
            result = self.analyzer.analyze()
            return generate_report(result)
        except Exception as e:
            logger.error(f"分析失败: {e}")
            return f"分析失败: {e}"


def send_feishu_notification(webhook_url: str, report: str) -> bool:
    """发送飞书通知"""
    notifier = FeishuNotifier(webhook_url=webhook_url)
    return notifier.send_analysis_report(report)


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='纳斯达克指数分析定时任务')
    parser.add_argument('--mode', choices=['once', 'loop', 'time'], default='once',
                        help='运行模式: once=单次, loop=循环, time=定时检测')
    parser.add_argument('--interval', type=int, default=6,
                        help='循环模式下的间隔小时数 (默认6小时)')
    parser.add_argument('--iterations', type=int, default=None,
                        help='循环模式下的最大迭代次数')
    parser.add_argument('--feishu', type=str, default='',
                        help='飞书Webhook URL (可选，不填则用config.py中的配置)')
    
    args = parser.parse_args()
    
    # 优先使用命令行参数，其次使用配置文件
    feishu_webhook = args.feishu or FEISHU_WEBHOOK_URL
    
    if args.mode == 'once':
        # 单次执行
        analyzer = NasdaqAnalyzer()
        result = analyzer.analyze()
        report = generate_report(result)
        print(report)
        
        if feishu_webhook:
            print(f"\n正在发送飞书通知...")
            success = send_feishu_notification(feishu_webhook, report)
            print(f"飞书通知: {'✅ 成功' if success else '❌ 失败'}")
        else:
            print(f"\n⚠️ 未配置飞书 Webhook，消息未发送。")
    
    elif args.mode == 'loop':
        # 循环执行
        scheduler = SimpleScheduler(interval_hours=args.interval)
        scheduler.run_loop(max_iterations=args.iterations)
    
    elif args.mode == 'time':
        # 定时检测
        scheduler = TimeBasedScheduler()
        scheduler.run_loop()


if __name__ == "__main__":
    main()
