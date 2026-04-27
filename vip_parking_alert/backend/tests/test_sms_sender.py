import pytest
from unittest.mock import patch, MagicMock
from app.services.sms_sender import SmsSender

class TestSmsSender:
    @patch('app.services.sms_sender.requests.get')
    def test_send_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "ok"
        mock_get.return_value = mock_resp

        sms_config = MagicMock()
        sms_config.url = "https://sms.example.com/send"
        sms_config.token = "test_token"
        sms_config.from_param = "VIP"

        success, detail = SmsSender.send("13800138000", "测试短信", sms_config)
        assert success is True
        assert "200" in detail

    @patch('app.services.sms_sender.requests.get')
    def test_send_failure(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "error"
        mock_get.return_value = mock_resp

        sms_config = MagicMock()
        sms_config.url = "https://sms.example.com/send"
        sms_config.token = "test_token"
        sms_config.from_param = "VIP"

        success, detail = SmsSender.send("13800138000", "测试短信", sms_config)
        assert success is False

    @patch('app.services.sms_sender.requests.get', side_effect=Exception("timeout"))
    def test_send_timeout(self, mock_get):
        sms_config = MagicMock()
        sms_config.url = "https://sms.example.com/send"
        sms_config.token = "test_token"
        sms_config.from_param = "VIP"

        success, detail = SmsSender.send("13800138000", "测试短信", sms_config)
        assert success is False
