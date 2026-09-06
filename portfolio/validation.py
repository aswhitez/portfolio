import re
from decimal import Decimal, InvalidOperation
from portfolio.models import Position

class PortfolioValidationError(ValueError):
    """Exception levée lorsque les données d'entrée du portefeuille sont invalides."""
    pass


_TICKER_REGEX = re.compile(r"^[A-Z0-9.-]+$")
_CURRENCY_REGEX = re.compile(r"^[A-Z]{3}$")
_MAX_TICKER_LENGTH = 20
_MAX_DECIMAL_VALUE = Decimal("1000000000000")  # Limite anti-dépassement (1 000 milliards)


def validate_positions(
    positions: list[dict[str, object]],
    default_currency: str,
) -> list[Position]:
    if not isinstance(positions, list):
        raise PortfolioValidationError("Le portefeuille doit être transmis sous forme de liste.")

    validated_positions: list[Position] = []

    for index, item in enumerate(positions):
        if not isinstance(item, dict):
            raise PortfolioValidationError(f"Élément invalide à l'index {index}.")

        # Normalisation des champs FR/EN
        raw_ticker = item.get("ticker")
        raw_quantity = item.get("quantite", item.get("quantity"))
        raw_price = item.get("prix_achat", item.get("purchase_price"))
        raw_currency = item.get("devise", item.get("currency", default_currency))

        # Validation du ticker
        if not isinstance(raw_ticker, str):
            raise PortfolioValidationError(f"Ticker manquant ou invalide à l'index {index}.")

        # Rejet explicite si le ticker contient des espaces ou retours à la ligne
        if raw_ticker != raw_ticker.strip():
            raise PortfolioValidationError(f"Format de ticker non autorisé à l'index {index}.")

        ticker = raw_ticker.upper()
        if (
            not ticker
            or len(ticker) > _MAX_TICKER_LENGTH
            or not _TICKER_REGEX.match(ticker)
        ):
            raise PortfolioValidationError(f"Format de ticker non autorisé à l'index {index}.")

        # Validation numérique (les booléens sont rejetés explicitement car hérités de int)
        quantity = _parse_positive_decimal(raw_quantity, "Quantité", index)
        purchase_price = _parse_positive_decimal(raw_price, "Prix d'achat", index)

        # Validation de la devise
        if not isinstance(raw_currency, str):
            raise PortfolioValidationError(f"Devise invalide à l'index {index}.")

        currency = raw_currency.strip().upper()
        if not _CURRENCY_REGEX.match(currency):
            raise PortfolioValidationError(f"Code de devise ISO invalide à l'index {index}.")

        validated_positions.append(
            Position(
                ticker=ticker,
                quantity=quantity,
                purchase_price=purchase_price,
                currency=currency,
            )
        )

    return validated_positions


def _parse_positive_decimal(value: object, field_name: str, index: int) -> Decimal:
    if value is None or isinstance(value, bool):
        raise PortfolioValidationError(f"{field_name} manquante ou invalide à l'index {index}.")

    try:
        dec = Decimal(str(value).strip())
    except (InvalidOperation, TypeError, ValueError):
        raise PortfolioValidationError(f"{field_name} doit être un nombre valide à l'index {index}.")

    if dec.is_nan() or dec.is_infinite():
        raise PortfolioValidationError(f"{field_name} contient une valeur non finie à l'index {index}.")

    if dec < 0:
        raise PortfolioValidationError(f"{field_name} ne peut pas être négative à l'index {index}.")

    if dec > _MAX_DECIMAL_VALUE:
        raise PortfolioValidationError(f"{field_name} dépasse la valeur maximale autorisée à l'index {index}.")

    return dec