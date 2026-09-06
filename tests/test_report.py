from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
import requests

from portfolio.models import AppConfig, PortfolioSummary
from portfolio.report import ReportGenerationError, generate_report


@pytest.fixture
def sample_config():
    return AppConfig(
        ollama_url="http://localhost:11434/api/chat",
        ollama_model="phi4-mini",
        default_currency="USD",
        request_timeout=5,
    )


@pytest.fixture
def sample_summary():
    return PortfolioSummary(
        positions=[],
        total_invested=Decimal("1000"),
        total_current_value=Decimal("1200"),
        total_gain_loss=Decimal("200"),
        total_gain_loss_pct=Decimal("20"),
        currency="USD",
        data_status="complete",
    )


@patch("requests.post")
def test_generate_report_success(mock_post, sample_summary, sample_config):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "message": {"content": "Rapport synthétique généré avec succès."}
    }
    mock_post.return_value = mock_resp

    result = generate_report(sample_summary, sample_config)
    assert "Rapport synthétique" in result
    mock_post.assert_called_once()


@patch("requests.post")
def test_generate_report_http_error(mock_post, sample_summary, sample_config):
    mock_post.side_effect = requests.exceptions.HTTPError("500 Server Error")
    with pytest.raises(ReportGenerationError, match="Impossible de joindre le service"):
        generate_report(sample_summary, sample_config)


@patch("requests.post")
def test_generate_report_timeout(mock_post, sample_summary, sample_config):
    mock_post.side_effect = requests.exceptions.Timeout("Timeout expiré")
    with pytest.raises(ReportGenerationError, match="n'a pas répondu dans le délai"):
        generate_report(sample_summary, sample_config)


@patch("requests.post")
def test_generate_report_invalid_json(mock_post, sample_summary, sample_config):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.side_effect = ValueError("JSON invalide")
    mock_post.return_value = mock_resp

    with pytest.raises(ReportGenerationError, match="illisible"):
        generate_report(sample_summary, sample_config)


@patch("requests.post")
def test_generate_report_empty_content(mock_post, sample_summary, sample_config):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"message": {"content": "   "}}
    mock_post.return_value = mock_resp

    with pytest.raises(ReportGenerationError, match="vide"):
        generate_report(sample_summary, sample_config)