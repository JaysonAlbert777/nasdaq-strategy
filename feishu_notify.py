"""
飞书通知模块
支持两种方式：
1. 自定义机器人 Webhook（用户配置）
2. 飞书开放平台 API（需要 appId/appSecret）
"""

import requests
import json
from typing import Optional
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import FEISHU_WEBHOOK_URL, PROXY_HTTP

logger = logging.getLogger(__name__)


class FeishuNotifier:
    """飞书通知发送器"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or FEISHU_WEBHOOK_URL
    
    def send_text(self, text: str, chat_id: str = None) -> bool:
        """
        发送文本消息（通过 Webhook 机器人）
        
        Args:
            text: 消息内容
            chat_id: 群聊 ID（可选，用于指定发送群）
        """
        if not self.webhook_url:
            logger.warning("未配置飞书 Webhook URL")
            return False
        
        try:
            payload = {
                "msg_type": "text",
                "content": {
                    "text": text
                }
            }
            
            # 如果指定了 chat_id，通过 content 传递
            if chat_id:
                payload["chat_id"] = chat_id
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                proxies={"http": PROXY_HTTP, "https": PROXY_HTTP}
            )
            
            result = response.json()
            
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                logger.info("飞书通知发送成功")
                return True
            else:
                logger.error(f"飞书通知发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"发送飞书通知异常: {e}")
            return False
    
    def send_card(self, card_content: dict) -> bool:
        """
        发送卡片消息（通过 Webhook 机器人）
        
        Args:
            card_content: 卡片内容 JSON
        """
        if not self.webhook_url:
            logger.warning("未配置飞书 Webhook URL")
            return False
        
        try:
            payload = {
                "msg_type": "interactive",
                "card": card_content
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=15,
                proxies={"http": PROXY_HTTP, "https": PROXY_HTTP}
            )
            
            result = response.json()
            
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                logger.info("飞书卡片消息发送成功")
                return True
            else:
                logger.error(f"飞书卡片消息发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"发送飞书卡片消息异常: {e}")
            return False
    
    def send_analysis_report(self, report_text: str) -> bool:
        """发送纳斯达克分析报告"""
        # 飞书 Webhook 卡片模板
        card = {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "📊 纳斯达克指数分析报告"
                },
                "template": "purple"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": report_text
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": "由自动化策略系统生成 | 仅供参考，不构成投资建议"
                        }
                    ]
                }
            ]
        }
        
        return self.send_card(card)


def send_feishu_message(webhook_url: str, message: str) -> bool:
    """便捷函数：发送飞书消息"""
    notifier = FeishuNotifier(webhook_url=webhook_url)
    return notifier.send_text(message)


if __name__ == "__main__":
    # 测试发送
    notifier = FeishuNotifier()
    
    if notifier.webhook_url:
        print(f"发送测试消息到飞书...")
        result = notifier.send_text("🧪 这是一条测试消息，来自纳斯达克策略分析系统。")
        print(f"发送结果: {'成功' if result else '失败'}")
    else:
        print("未配置 Webhook URL，请在 config.py 中配置 FEISHU_WEBHOOK_URL")
