from decimal import Decimal
import pytest

from portfolio.validation import PortfolioValidationError, validate_positions


def test_validate_positions_empty():
    assert validate_positions([], "USD") == []


def test_validate_positions_valid():
    raw = [
        {"ticker": "aapl", "quantite": "10", "prix_achat": "150.5", "devise": "usd"}
    ]
    res = validate_positions(raw, "USD")
    assert len(res) == 1
    assert res[0].ticker == "AAPL"
    assert res[0].quantity == Decimal("10")
    assert res[0].purchase_price == Decimal("150.5")
    assert res[0].currency == "USD"


def test_validate_positions_missing_key():
    raw = [{"ticker": "AAPL", "quantite": "10"}]
    with pytest.raises(PortfolioValidationError, match="Prix d'achat"):
        validate_positions(raw, "USD")


def test_validate_positions_invalid_quantity():
    raw = [{"ticker": "AAPL", "quantite": "abc", "prix_achat": "150"}]
    with pytest.raises(PortfolioValidationError, match="Quantité doit être un nombre"):
        validate_positions(raw, "USD")


def test_validate_positions_negative_number():
    raw = [{"ticker": "AAPL", "quantite": "-5", "prix_achat": "150"}]
    with pytest.raises(PortfolioValidationError, match="ne peut pas être négative"):
        validate_positions(raw, "USD")


def test_validate_positions_boolean_rejected():
    raw = [{"ticker": "AAPL", "quantite": True, "prix_achat": "150"}]
    with pytest.raises(PortfolioValidationError, match="Quantité manquante ou invalide"):
        validate_positions(raw, "USD")


def test_validate_positions_ticker_too_long():
    raw = [{"ticker": "A" * 21, "quantite": "10", "prix_achat": "150"}]
    with pytest.raises(PortfolioValidationError, match="Format de ticker non autorisé"):
        validate_positions(raw, "USD")


test_invalid_tickers = ["AAPL;DROP TABLE", "AAPL<script>", "AAPL\n"]


@pytest.mark.parametrize("invalid_ticker", test_invalid_tickers)
def test_validate_positions_forbidden_chars(invalid_ticker):
    raw = [{"ticker": invalid_ticker, "quantite": "10", "prix_achat": "150"}]
    with pytest.raises(PortfolioValidationError, match="Format de ticker non autorisé"):
        validate_positions(raw, "USD")


def test_validate_positions_invalid_currency():
    raw = [{"ticker": "AAPL", "quantite": "10", "prix_achat": "150", "devise": "USDOLLARS"}]
    with pytest.raises(PortfolioValidationError, match="Code de devise ISO invalide"):
        validate_positions(raw, "USD")