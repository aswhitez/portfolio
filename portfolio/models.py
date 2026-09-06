from dataclasses import dataclass
from decimal import Decimal

# Statuts de prix pour une position
PRICE_STATUS_OK = "ok"
PRICE_STATUS_UNAVAILABLE = "unavailable"

# Statuts globaux du portefeuille
DATA_STATUS_COMPLETE = "complete"
DATA_STATUS_PARTIAL = "partial"
DATA_STATUS_UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class Position:
    ticker: str
    quantity: Decimal
    purchase_price: Decimal
    currency: str


@dataclass(frozen=True)
class EnrichedPosition:
    ticker: str
    quantity: Decimal
    purchase_price: Decimal
    current_price: Decimal | None
    current_price_currency: str | None
    current_value: Decimal | None
    gain_loss: Decimal | None
    gain_loss_pct: Decimal | None
    price_status: str


@dataclass(frozen=True)
class PortfolioSummary:
    positions: list[EnrichedPosition]
    total_invested: Decimal
    total_current_value: Decimal | None
    total_gain_loss: Decimal | None
    total_gain_loss_pct: Decimal | None
    currency: str
    data_status: str


@dataclass(frozen=True)
class AppConfig:
    ollama_url: str
    ollama_model: str
    default_currency: str
    request_timeout: int