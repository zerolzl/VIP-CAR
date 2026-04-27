"""短信网关发送实现"""
import requests
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)

class SmsSender:
    TIMEOUT = 5

    @staticmethod
    def send(target: str, content: str, sms_config) -> tuple[bool, str]:
        """
        发送短信。
        target: 手机号
        content: 短信内容（明文）
        sms_config: SmsGatewayConfig实例
        返回: (是否成功, 详情描述)
        """
        encoded_content = quote(content)
        url = (
            f"{sms_config.url}"
            f"?mobile={target}"
            f"&content={encoded_content}"
            f"&token={sms_config.token}"
            f"&from={sms_config.from_param}"
        )
        try:
            resp = requests.get(url, timeout=SmsSender.TIMEOUT)
            if resp.status_code == 200 and "ok" in resp.text.lower():
                logger.info(f"短信发送成功: {target}")
                return True, f"HTTP {resp.status_code}"
            else:
                logger.warning(f"短信发送失败: {target}, HTTP {resp.status_code}, body={resp.text[:200]}")
                return False, f"HTTP {resp.status_code}, body={resp.text[:200]}"
        except requests.Timeout:
            logger.warning(f"短信发送超时: {target}")
            return False, "请求超时"
        except Exception as e:
            logger.error(f"短信发送异常: {target}, {e}")
            return False, str(e)
