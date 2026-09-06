from decimal import Decimal
import pytest

from portfolio.calculations import calculate_portfolio
from portfolio.models import (
    DATA_STATUS_COMPLETE,
    DATA_STATUS_PARTIAL,
    DATA_STATUS_UNAVAILABLE,
    PRICE_STATUS_OK,
    PRICE_STATUS_UNAVAILABLE,
    Position,
)
from portfolio.validation import PortfolioValidationError


def test_calculate_empty_portfolio():
    summary = calculate_portfolio([], {}, "USD")
    assert summary.total_invested == Decimal("0")
    assert summary.data_status == DATA_STATUS_COMPLETE
    assert summary.positions == []


def test_calculate_all_prices_available():
    positions = [
        Position(ticker="AAPL", quantity=Decimal("2"), purchase_price=Decimal("100"), currency="USD")
    ]
    prices = {
        "AAPL": {"price": Decimal("150"), "currency": "USD", "status": PRICE_STATUS_OK}
    }
    summary = calculate_portfolio(positions, prices, "USD")

    assert summary.data_status == DATA_STATUS_COMPLETE
    assert summary.total_invested == Decimal("200")
    assert summary.total_current_value == Decimal("300")
    assert summary.total_gain_loss == Decimal("100")
    assert summary.total_gain_loss_pct == Decimal("50")


def test_calculate_missing_price():
    positions = [
        Position(ticker="AAPL", quantity=Decimal("2"), purchase_price=Decimal("100"), currency="USD")
    ]
    prices = {
        "AAPL": {"price": None, "currency": None, "status": PRICE_STATUS_UNAVAILABLE}
    }
    summary = calculate_portfolio(positions, prices, "USD")

    assert summary.data_status == DATA_STATUS_UNAVAILABLE
    assert summary.total_current_value is None
    assert summary.total_gain_loss is None
    assert summary.positions[0].price_status == PRICE_STATUS_UNAVAILABLE


def test_calculate_partial_prices():
    positions = [
        Position(ticker="AAPL", quantity=Decimal("2"), purchase_price=Decimal("100"), currency="USD"),
        Position(ticker="BTC", quantity=Decimal("1"), purchase_price=Decimal("50000"), currency="USD"),
    ]
    prices = {
        "AAPL": {"price": Decimal("150"), "currency": "USD", "status": PRICE_STATUS_OK},
        "BTC": {"price": None, "currency": None, "status": PRICE_STATUS_UNAVAILABLE},
    }
    summary = calculate_portfolio(positions, prices, "USD")

    assert summary.data_status == DATA_STATUS_PARTIAL
    assert summary.total_current_value is None
    assert summary.positions[0].price_status == PRICE_STATUS_OK
    assert summary.positions[1].price_status == PRICE_STATUS_UNAVAILABLE


def test_calculate_zero_purchase_price():
    positions = [
        Position(ticker="AIRDROP", quantity=Decimal("100"), purchase_price=Decimal("0"), currency="USD")
    ]
    prices = {
        "AIRDROP": {"price": Decimal("10"), "currency": "USD", "status": PRICE_STATUS_OK}
    }
    summary = calculate_portfolio(positions, prices, "USD")

    assert summary.positions[0].gain_loss_pct is None
    assert summary.total_gain_loss_pct is None


def test_calculate_unconverted_currency_rejection():
    positions = [
        Position(ticker="BMW", quantity=Decimal("5"), purchase_price=Decimal("90"), currency="EUR")
    ]
    with pytest.raises(PortfolioValidationError, match="diffère de la devise de référence"):
        calculate_portfolio(positions, {}, "USD")