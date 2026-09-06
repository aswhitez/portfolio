import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import yfinance as yf

from portfolio.models import Position, PRICE_STATUS_OK, PRICE_STATUS_UNAVAILABLE

logger = logging.getLogger(__name__)

SUPPORTED_CRYPTO_ALIASES = {
    "BTC": "BTC-EUR",
    "ETH": "ETH-EUR",
}


def fetch_current_prices(
    positions: list[Position],
    timeout: int,
) -> dict[str, dict[str, object]]:
    prices_info: dict[str, dict[str, object]] = {}

    for pos in positions:
        ticker_symbol = pos.ticker
        fetch_symbol = SUPPORTED_CRYPTO_ALIASES.get(ticker_symbol, ticker_symbol)

        try:
            ticker_obj = yf.Ticker(fetch_symbol)
            fast_info = ticker_obj.fast_info

            raw_price = fast_info.get("lastPrice") or fast_info.get("regularMarketPrice")

            if raw_price is None:
                logger.warning("Cours indisponible sur Yahoo Finance pour %s", fetch_symbol)
                prices_info[ticker_symbol] = {
                    "price": None,
                    "currency": None,
                    "status": PRICE_STATUS_UNAVAILABLE,
                    "source": "Yahoo Finance",
                    "timestamp": None,
                }
                continue

            prices_info[ticker_symbol] = {
                "price": Decimal(str(raw_price)),
                "currency": fast_info.get("currency", pos.currency),
                "status": PRICE_STATUS_OK,
                "source": "Yahoo Finance",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except (KeyError, ValueError, TypeError, InvalidOperation) as err:
            logger.error("Erreur lors du traitement du cours pour %s : %s", fetch_symbol, err)
            prices_info[ticker_symbol] = {
                "price": None,
                "currency": None,
                "status": PRICE_STATUS_UNAVAILABLE,
                "source": "Yahoo Finance",
                "timestamp": None,
            }
        except RuntimeError as err:
            logger.error("Échec de connexion ou d'exécution yfinance pour %s : %s", fetch_symbol, err)
            prices_info[ticker_symbol] = {
                "price": None,
                "currency": None,
                "status": PRICE_STATUS_UNAVAILABLE,
                "source": "Yahoo Finance",
                "timestamp": None,
            }

    return prices_info