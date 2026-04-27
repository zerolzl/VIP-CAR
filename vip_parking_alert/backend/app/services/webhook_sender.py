"""金山协作机器人Webhook发送实现"""
import requests
import logging

logger = logging.getLogger(__name__)

class WebhookSender:
    TIMEOUT = 5

    @staticmethod
    def send(url: str, payload: dict) -> tuple[bool, str]:
        """
        发送Webhook。
        url: Webhook URL
        payload: JSON消息体
        返回: (是否成功, 详情描述)
        """
        try:
            resp = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=WebhookSender.TIMEOUT,
            )
            if resp.status_code == 200:
                logger.info(f"Webhook发送成功: {url[:50]}...")
                return True, f"HTTP {resp.status_code}"
            else:
                logger.warning(f"Webhook发送失败: HTTP {resp.status_code}, body={resp.text[:200]}")
                return False, f"HTTP {resp.status_code}, body={resp.text[:200]}"
        except requests.Timeout:
            logger.warning(f"Webhook发送超时: {url[:50]}...")
            return False, "请求超时"
        except Exception as e:
            logger.error(f"Webhook发送异常: {url[:50]}..., {e}")
            return False, str(e)
