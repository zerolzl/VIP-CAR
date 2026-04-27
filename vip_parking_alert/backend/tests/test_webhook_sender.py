import pytest
from unittest.mock import patch, MagicMock
from app.services.webhook_sender import WebhookSender

class TestWebhookSender:
    @patch('app.services.webhook_sender.requests.post')
    def test_send_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp

        payload = {"msgtype": "markdown", "markdown": {"title": "test", "text": "test"}}
        success, detail = WebhookSender.send("https://example.com/webhook", payload)
        assert success is True

    @patch('app.services.webhook_sender.requests.post')
    def test_send_failure(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "error"
        mock_post.return_value = mock_resp

        payload = {"msgtype": "markdown", "markdown": {"title": "test", "text": "test"}}
        success, detail = WebhookSender.send("https://example.com/webhook", payload)
        assert success is False
