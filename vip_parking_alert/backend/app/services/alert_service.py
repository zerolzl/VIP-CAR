"""告警发送与抑制核心逻辑"""
import json
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session
from ..db.session import SessionLocal
from ..models.alert_log import AlertLog
from ..models.notify_config import SpotNotifyConfig
from ..models.spot import VipParkingSpot
from ..models.sms_gateway import SmsGatewayConfig
from .sms_sender import SmsSender
from .webhook_sender import WebhookSender
import logging

logger = logging.getLogger(__name__)

class AlertService:
    _lock = threading.Lock()

    @staticmethod
    def process_violation(
        spot: VipParkingSpot,
        plate_number: str,
        notify_configs: list[SpotNotifyConfig],
        sms_config: SmsGatewayConfig | None,
    ):
        """
        处理违规告警：并行发送，任一成功即写入日志。
        """
        if not notify_configs:
            logger.warning(f"车位 {spot.spot_number} 无启用的通知配置，跳过告警")
            return

        # 构造告警内容
        sms_content = (
            f"【VIP车位告警】车位:{spot.spot_number} "
            f"所属人:{spot.owner} "
            f"当前车牌:{plate_number} "
            f"请及时处理"
        )
        webhook_payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": "VIP车位异常告警",
                "text": (
                    f"**车位**: {spot.spot_number}\n"
                    f"**所属人**: {spot.owner}\n"
                    f"**当前车牌**: {plate_number}\n"
                    f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            }
        }

        has_sent = False
        sent_via_list = []
        result_details = []

        def send_task(config: SpotNotifyConfig) -> tuple[bool, str, str]:
            try:
                if config.notify_type == "sms":
                    if sms_config:
                        success, detail = SmsSender.send(
                            target=config.target,
                            content=sms_content,
                            sms_config=sms_config,
                        )
                        return success, "sms", detail
                    else:
                        return False, "sms", "短信网关未配置"
                elif config.notify_type == "webhook":
                    success, detail = WebhookSender.send(
                        url=config.target,
                        payload=webhook_payload,
                    )
                    return success, "webhook", detail
            except Exception as e:
                return False, config.notify_type, str(e)
            return False, config.notify_type, "未知错误"

        max_workers = min(len(notify_configs), 4)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(send_task, cfg): cfg for cfg in notify_configs}
            for future in as_completed(futures):
                success, channel, detail = future.result()
                if success:
                    sent_via_list.append(channel)
                    result_details.append(f"{channel}:success")
                    if not has_sent:
                        with AlertService._lock:
                            db = SessionLocal()
                            try:
                                alert = AlertLog(
                                    spot_id=spot.id,
                                    plate_number=plate_number,
                                    sent_via=",".join(sent_via_list),
                                    sent_time=datetime.now(),
                                    is_resolved=0,
                                    result="; ".join(result_details),
                                )
                                db.add(alert)
                                db.commit()
                                logger.info(f"告警已记录: 车位={spot.spot_number}, 车牌={plate_number}, 通道={sent_via_list}")
                            except Exception as e:
                                db.rollback()
                                logger.error(f"写入alert_log失败: {e}")
                            finally:
                                db.close()
                        has_sent = True
                else:
                    result_details.append(f"{channel}:failed({detail})")
                    logger.warning(f"告警发送失败: 车位={spot.spot_number}, 通道={channel}, 原因={detail}")

        if not has_sent:
            logger.warning(f"所有通道发送失败，不写入告警记录: 车位={spot.spot_number}, 车牌={plate_number}")

    @staticmethod
    def resolve_alert(spot_id: int, plate_number: str):
        """标记告警为已解决"""
        db = SessionLocal()
        try:
            alerts = db.query(AlertLog).filter(
                AlertLog.spot_id == spot_id,
                AlertLog.plate_number == plate_number,
                AlertLog.is_resolved == 0,
            ).all()
            for alert in alerts:
                alert.is_resolved = 1
                alert.resolved_time = datetime.now()
            db.commit()
            if alerts:
                logger.info(f"告警已解决: 车位ID={spot_id}, 车牌={plate_number}, 共{len(alerts)}条")
        except Exception as e:
            db.rollback()
            logger.error(f"标记告警解决失败: {e}")
        finally:
            db.close()

    @staticmethod
    def has_unresolved_alert(spot_id: int, plate_number: str) -> bool:
        """检查是否存在未解决的告警"""
        db = SessionLocal()
        try:
            count = db.query(AlertLog).filter(
                AlertLog.spot_id == spot_id,
                AlertLog.plate_number == plate_number,
                AlertLog.is_resolved == 0,
            ).count()
            return count > 0
        finally:
            db.close()
