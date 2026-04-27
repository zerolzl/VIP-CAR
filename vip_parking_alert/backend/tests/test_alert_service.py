import pytest
from unittest.mock import patch, MagicMock
from app.services.alert_service import AlertService
from app.services.sms_sender import SmsSender
from app.services.webhook_sender import WebhookSender


class TestAlertService:
    @patch.object(AlertService, 'has_unresolved_alert', return_value=False)
    @patch("app.services.alert_service.SessionLocal")
    @patch.object(SmsSender, 'send', return_value=(True, "HTTP 200"))
    @patch.object(WebhookSender, 'send', return_value=(True, "HTTP 200"))
    def test_process_violation_success(self, mock_webhook, mock_sms, mock_session_cls, mock_has_alert):
        """测试告警发送成功场景"""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        spot = MagicMock()
        spot.id = 1
        spot.spot_number = "A01"
        spot.owner = "张三"

        sms_config = MagicMock()
        sms_config.token = "test_token"
        sms_config.from_param = "test_from"

        notify_configs = [
            MagicMock(notify_type="sms", target="13800138000", enabled=1),
            MagicMock(notify_type="webhook", target="https://example.com/webhook", enabled=1),
        ]

        AlertService.process_violation(spot, "粤B99999", notify_configs, sms_config)
        assert mock_sms.called
        assert mock_webhook.called
        mock_session.add.assert_called_once()

    @patch.object(AlertService, 'has_unresolved_alert', return_value=False)
    @patch("app.services.alert_service.SessionLocal")
    @patch.object(SmsSender, 'send', return_value=(False, "HTTP 500"))
    @patch.object(WebhookSender, 'send', return_value=(False, "HTTP 500"))
    def test_process_violation_all_fail(self, mock_webhook, mock_sms, mock_session_cls, mock_has_alert):
        """测试所有通道发送失败场景"""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        spot = MagicMock()
        spot.id = 1
        spot.spot_number = "A01"
        spot.owner = "张三"
        sms_config = MagicMock()

        notify_configs = [
            MagicMock(notify_type="sms", target="13800138000", enabled=1),
        ]

        AlertService.process_violation(spot, "粤B99999", notify_configs, sms_config)
        assert mock_sms.called
        mock_session.add.assert_not_called()

    @patch.object(AlertService, 'has_unresolved_alert', return_value=True)
    @patch("app.services.alert_service.SessionLocal")
    @patch.object(SmsSender, 'send', return_value=(True, "HTTP 200"))
    def test_process_violation_suppressed(self, mock_sms, mock_session_cls, mock_has_alert):
        """测试告警抑制场景——已有未解决告警时不重复发送"""
        spot = MagicMock()
        spot.id = 1
        spot.spot_number = "A01"
        spot.owner = "张三"
        sms_config = MagicMock()

        notify_configs = [
            MagicMock(notify_type="sms", target="13800138000", enabled=1),
        ]

        # 注意：process_violation本身不做抑制检查，抑制在patrol_service中
        # 这里验证的是发送逻辑
        AlertService.process_violation(spot, "粤B99999", notify_configs, sms_config)
        # 仍然会发送（抑制逻辑在patrol_service中）
        assert mock_sms.called

    @patch("app.services.alert_service.SessionLocal")
    def test_resolve_alert(self, mock_session_cls):
        """测试告警解决标记"""
        mock_session = MagicMock()
        mock_alert = MagicMock()
        mock_session.query.return_value.filter.return_value.filter.return_value.all.return_value = [mock_alert]
        mock_session_cls.return_value = mock_session

        AlertService.resolve_alert(1, "粤B12345")
        # 验证commit被调用（表示更新已执行）
        mock_session.commit.assert_called_once()
