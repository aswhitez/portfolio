from decimal import Decimal
from portfolio.models import (
    Position,
    EnrichedPosition,
    PortfolioSummary,
    PRICE_STATUS_OK,
    PRICE_STATUS_UNAVAILABLE,
    DATA_STATUS_COMPLETE,
    DATA_STATUS_PARTIAL,
    DATA_STATUS_UNAVAILABLE,
)
from portfolio.validation import PortfolioValidationError


def calculate_portfolio(
    positions: list[Position],
    prices: dict[str, dict[str, object]],
    default_currency: str,
) -> PortfolioSummary:
    if not positions:
        return PortfolioSummary(
            positions=[],
            total_invested=Decimal("0"),
            total_current_value=Decimal("0"),
            total_gain_loss=Decimal("0"),
            total_gain_loss_pct=Decimal("0"),
            currency=default_currency,
            data_status=DATA_STATUS_COMPLETE,
        )

    enriched_positions: list[EnrichedPosition] = []
    total_invested = Decimal("0")
    total_current_value_acc = Decimal("0")
    available_prices_count = 0

    for pos in positions:
        # Rejet des positions dans une autre devise si aucune conversion n'est configurée
        if pos.currency != default_currency:
            raise PortfolioValidationError(
                f"La position {pos.ticker} est en {pos.currency}, ce qui diffère "
                f"de la devise de référence ({default_currency}). La conversion multi-devise n'est pas active."
            )

        purchase_value = pos.quantity * pos.purchase_price
        total_invested += purchase_value

        price_info = prices.get(pos.ticker, {})
        raw_price = price_info.get("price")
        price_status = str(price_info.get("status", PRICE_STATUS_UNAVAILABLE))

        if price_status == PRICE_STATUS_OK and raw_price is not None:
            available_prices_count += 1
            current_price = Decimal(str(raw_price))
            current_value = pos.quantity * current_price
            gain_loss = current_value - purchase_value

            gain_loss_pct = (
                (gain_loss / purchase_value) * Decimal("100")
                if purchase_value > Decimal("0")
                else None
            )

            total_current_value_acc += current_value

            enriched_positions.append(
                EnrichedPosition(
                    ticker=pos.ticker,
                    quantity=pos.quantity,
                    purchase_price=pos.purchase_price,
                    current_price=current_price,
                    current_price_currency=str(price_info.get("currency", pos.currency)),
                    current_value=current_value,
                    gain_loss=gain_loss,
                    gain_loss_pct=gain_loss_pct,
                    price_status=PRICE_STATUS_OK,
                )
            )
        else:
            enriched_positions.append(
                EnrichedPosition(
                    ticker=pos.ticker,
                    quantity=pos.quantity,
                    purchase_price=pos.purchase_price,
                    current_price=None,
                    current_price_currency=None,
                    current_value=None,
                    gain_loss=None,
                    gain_loss_pct=None,
                    price_status=PRICE_STATUS_UNAVAILABLE,
                )
            )

    # Évaluation du statut global du portefeuille
    total_positions = len(positions)
    if available_prices_count == total_positions:
        data_status = DATA_STATUS_COMPLETE
        total_current_value: Decimal | None = total_current_value_acc
        total_gain_loss: Decimal | None = total_current_value - total_invested
        total_gain_loss_pct: Decimal | None = (
            (total_gain_loss / total_invested) * Decimal("100")
            if total_invested > Decimal("0")
            else None
        )
    elif available_prices_count > 0:
        data_status = DATA_STATUS_PARTIAL
        total_current_value = None
        total_gain_loss = None
        total_gain_loss_pct = None
    else:
        data_status = DATA_STATUS_UNAVAILABLE
        total_current_value = None
        total_gain_loss = None
        total_gain_loss_pct = None

    return PortfolioSummary(
        positions=enriched_positions,
        total_invested=total_invested,
        total_current_value=total_current_value,
        total_gain_loss=total_gain_loss,
        total_gain_loss_pct=total_gain_loss_pct,
        currency=default_currency,
        data_status=data_status,
    )