"""Unit tests for the Akash health check validation script."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the script module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/infra"))
import validate_health


def test_validate_health_success():
    """Test successful health check."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}
    
    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = validate_health.validate_health("https://example.com", retries=1, delay=0)
    
    assert result is True


def test_validate_health_failure():
    """Test failed health check."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    
    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = validate_health.validate_health("https://example.com", retries=2, delay=0)
    
    assert result is False


def test_validate_health_wrong_status():
    """Test health check with wrong status value."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "unhealthy"}
    
    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = validate_health.validate_health("https://example.com", retries=1, delay=0)
    
    assert result is False


def test_validate_health_adds_scheme():
    """Test that URL without scheme gets https:// added."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}
    
    with patch("httpx.Client") as mock_client:
        mock_instance = mock_client.return_value.__enter__.return_value
        mock_instance.get.return_value = mock_response
        
        validate_health.validate_health("example.com", retries=1, delay=0)
        
        # Verify the URL was called with https://
        mock_instance.get.assert_called_once()
        called_url = mock_instance.get.call_args[0][0]
        assert called_url == "https://example.com/healthz"


def test_validate_health_connection_error():
    """Test health check with connection error."""
    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.side_effect = Exception("Connection refused")
        result = validate_health.validate_health("https://example.com", retries=1, delay=0)
    
    assert result is False


def test_validate_health_retries():
    """Test that health check retries on failure."""
    mock_response_fail = MagicMock()
    mock_response_fail.status_code = 503
    
    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.json.return_value = {"status": "ok"}
    
    with patch("httpx.Client") as mock_client:
        mock_instance = mock_client.return_value.__enter__.return_value
        # First call fails, second succeeds
        mock_instance.get.side_effect = [mock_response_fail, mock_response_success]
        
        result = validate_health.validate_health("https://example.com", retries=2, delay=0)
    
    assert result is True
    assert mock_instance.get.call_count == 2
