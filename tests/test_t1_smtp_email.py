import sys
import os
import pytest
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import send_email_gmail, send_email


def test_send_email_missing_credentials():
    """Verify send_email logs draft and returns informative message when SMTP credentials are absent."""
    with patch.dict(os.environ, {}, clear=True):
        res = send_email("test@example.com", "Test Subject", "Test Body")
        assert "SMTP credentials not configured" in res or "Simulated" in res or "To: test@example.com" in res


def test_send_email_smtp_mock():
    """Verify send_email executes SMTP TLS connection and message delivery when credentials are set."""
    env = {
        "SMTP_USER": "testuser@gmail.com",
        "SMTP_PASS": "secretpass123",
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": "587"
    }
    with patch.dict(os.environ, env), patch("smtplib.SMTP") as mock_smtp:
        mock_server = mock_smtp.return_value.__enter__.return_value
        res = send_email("recipient@example.com", "Test Subject", "Hello World")
        assert "Email successfully sent" in res
        assert mock_server.starttls.called
        assert mock_server.login.called
        assert mock_server.send_message.called
