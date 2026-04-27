"""定时巡检编排逻辑"""
import json
import logging
from ..db.session import SessionLocal
from ..models.spot import VipParkingSpot
from ..models.notify_config import SpotNotifyConfig
from ..models.sms_gateway import SmsGatewayConfig
from ..models.external_db import ExternalDbConfig
from .external_db_service import query_current_plate
from .alert_service import AlertService

logger = logging.getLogger(__name__)

class PatrolService:
    @staticmethod
    def execute_patrol():
        """执行一次完整的巡检"""
        logger.info("=== 开始VIP车位巡检 ===")
        db = SessionLocal()
        try:
            # 获取所有启用的车位
            spots = db.query(VipParkingSpot).filter(VipParkingSpot.status == 1).all()
            if not spots:
                logger.info("无启用的监控车位，跳过巡检")
                return

            # 获取短信网关配置
            sms_config = db.query(SmsGatewayConfig).filter(SmsGatewayConfig.enabled == 1).first()

            for spot in spots:
                try:
                    PatrolService._check_single_spot(spot, sms_config)
                except Exception as e:
                    logger.error(f"巡检车位 {spot.spot_number} 异常: {e}", exc_info=True)
                    continue

        finally:
            db.close()
        logger.info("=== VIP车位巡检结束 ===")

    @staticmethod
    def _check_single_spot(spot: VipParkingSpot, sms_config: SmsGatewayConfig | None):
        """检查单个车位"""
        # 查询当前车牌
        current_plate = query_current_plate(spot.spot_number)

        # 解析白名单
        try:
            allowed_plates = json.loads(spot.allowed_plates)
        except json.JSONDecodeError:
            logger.error(f"车位 {spot.spot_number} 的allowed_plates JSON解析失败: {spot.allowed_plates}")
            return

        # 当前无车
        if not current_plate:
            # 检查是否有未解决告警，标记为已解决
            db = SessionLocal()
            try:
                from ..models.alert_log import AlertLog
                unresolved = db.query(AlertLog).filter(
                    AlertLog.spot_id == spot.id,
                    AlertLog.is_resolved == 0,
                ).all()
                if unresolved:
                    for alert in unresolved:
                        AlertService.resolve_alert(alert.spot_id, alert.plate_number)
            finally:
                db.close()
            return

        # 车牌在白名单内
        if current_plate in allowed_plates:
            # 检查是否有该车牌的未解决告警，标记为已解决
            if AlertService.has_unresolved_alert(spot.id, current_plate):
                AlertService.resolve_alert(spot.id, current_plate)
            return

        # 车牌不在白名单内 - 检查是否已有告警（抑制逻辑）
        if AlertService.has_unresolved_alert(spot.id, current_plate):
            logger.debug(f"车位 {spot.spot_number} 车牌 {current_plate} 已在告警抑制中，跳过")
            return

        # 获取该车位所有启用的通知配置
        db = SessionLocal()
        try:
            notify_configs = db.query(SpotNotifyConfig).filter(
                SpotNotifyConfig.spot_id == spot.id,
                SpotNotifyConfig.enabled == 1,
            ).all()
        finally:
            db.close()

        # 触发告警
        logger.info(f"发现违规: 车位={spot.spot_number}, 车牌={current_plate}")
        AlertService.process_violation(
            spot=spot,
            plate_number=current_plate,
            notify_configs=notify_configs,
            sms_config=sms_config,
        )
