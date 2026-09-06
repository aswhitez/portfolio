import json
import logging
import sys
from decimal import Decimal
from pathlib import Path

from portfolio.calculations import calculate_portfolio
from portfolio.config import load_config
from portfolio.market_data import fetch_current_prices
from portfolio.models import PRICE_STATUS_OK
from portfolio.report import ReportGenerationError, generate_report
from portfolio.validation import PortfolioValidationError, validate_positions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("portfolio.cli")

POSITIONS_FILE = Path("positions.json")


def _format_decimal(val: Decimal | None, suffix: str = "") -> str:
    if val is None:
        return "N/A"
    return f"{val:.2f}{suffix}"


def main() -> None:
    config = load_config()

    print("=== Suivi de Portefeuille Investisseur ===")
    print(
        "Avertissement : Cette application est fournie à titre informatif "
        "et ne constitue pas un conseil financier.\n"
    )

    # 0. Chargement du fichier positions.json
    if not POSITIONS_FILE.exists():
        print(
            f"Erreur : Le fichier « {POSITIONS_FILE} » est introuvable à la racine du projet.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        with open(POSITIONS_FILE, "r", encoding="utf-8") as f:
            raw_positions = json.load(f)
    except (json.JSONDecodeError, OSError) as err:
        print(f"Erreur de lecture du fichier « {POSITIONS_FILE} » : {err}", file=sys.stderr)
        sys.exit(1)

    # 1. Validation des positions
    try:
        positions = validate_positions(raw_positions, config.default_currency)
    except PortfolioValidationError as err:
        logger.error("Erreur de validation des positions : %s", err)
        print(f"Erreur de données : {err}", file=sys.stderr)
        sys.exit(1)

    # 2. Récupération des cours
    print("Récupération des cours de marché...")
    prices = fetch_current_prices(positions, config.request_timeout)

    # 3. Calculs financiers
    try:
        summary = calculate_portfolio(positions, prices, config.default_currency)
    except PortfolioValidationError as err:
        logger.error("Erreur lors des calculs : %s", err)
        print(f"Erreur de calcul : {err}", file=sys.stderr)
        sys.exit(1)

    # 4. Affichage du bilan
    print(f"\nStatut des données : {summary.data_status.upper()}")
    print(
        f"Montant total investi : {_format_decimal(summary.total_invested)} {summary.currency}"
    )

    if summary.total_current_value is not None:
        print(
            f"Valeur actuelle : {_format_decimal(summary.total_current_value)} {summary.currency}"
        )
        print(
            f"Plus/Moins-value globale : {_format_decimal(summary.total_gain_loss)} {summary.currency} "
            f"({_format_decimal(summary.total_gain_loss_pct, '%')})"
        )
    else:
        print("Valeur globale indisponible (cours partiels ou absents).")

    print("\nDétail des positions :")
    for pos in summary.positions:
        if pos.price_status == PRICE_STATUS_OK:
            price_str = f"{_format_decimal(pos.current_price)} {pos.current_price_currency}"
            val_str = f"{_format_decimal(pos.current_value)} {summary.currency}"
            perf_str = _format_decimal(pos.gain_loss_pct, "%")
            print(
                f"  - {pos.ticker} : {pos.quantity} x {_format_decimal(pos.purchase_price)} {summary.currency} "
                f"| Cours : {price_str} | Valeur : {val_str} | Perf : {perf_str}"
            )
        else:
            print(
                f"  - {pos.ticker} : {pos.quantity} x {_format_decimal(pos.purchase_price)} {summary.currency} "
                f"| Cours : INDISPONIBLE"
            )

    # 5. Rapport LLM
    print("\nGénération du rapport d'analyse local...")
    try:
        report_text = generate_report(summary, config)
        print("\n--- RAPPORT DE SYNTHÈSE ---")
        print(report_text)
    except ReportGenerationError as err:
        logger.error("Échec de la génération du rapport LLM : %s", err)
        print(
            f"\nNote : Impossible de générer le rapport LLM ({err}).",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()