import json
import logging
from decimal import Decimal, ROUND_HALF_UP
import requests

from portfolio.models import AppConfig, PortfolioSummary

logger = logging.getLogger(__name__)


class ReportGenerationError(Exception):
    """Exception levée en cas d'échec du service de rapport LLM."""
    pass


def _format_num(val: Decimal | None) -> float | None:
    """Arrondit proprement à 2 décimales pour le payload JSON transmis au LLM."""
    if val is None:
        return None
    return float(val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _summary_to_dict(summary: PortfolioSummary) -> dict[str, object]:
    return {
        "currency": summary.currency,
        "data_status": summary.data_status,
        "total_invested": _format_num(summary.total_invested),
        "total_current_value": _format_num(summary.total_current_value),
        "total_gain_loss": _format_num(summary.total_gain_loss),
        "total_gain_loss_pct": _format_num(summary.total_gain_loss_pct),
        "positions": [
            {
                "ticker": pos.ticker,
                "quantity": float(pos.quantity),
                "purchase_price": _format_num(pos.purchase_price),
                "current_price": _format_num(pos.current_price),
                "current_value": _format_num(pos.current_value),
                "gain_loss": _format_num(pos.gain_loss),
                "gain_loss_pct": _format_num(pos.gain_loss_pct),
                "price_status": pos.price_status,
            }
            for pos in summary.positions
        ],
    }


def generate_report(summary: PortfolioSummary, config: AppConfig) -> str:
    summary_data = _summary_to_dict(summary)
    payload_data = json.dumps(summary_data)

    system_prompt = (
        "Tu es un analyste financier privé factuel, clair et concis. "
        "Règles impératives :\n"
        "1. Utilise EXCLUSIVEMENT les données structurées fournies.\n"
        "2. Exprime TOUS les montants et pourcentages avec EXACTEMENT 2 décimales (ex: 319.97 USD, 42.60%).\n"
        "3. Ne qualifie jamais les cryptomonnaies (comme BTC) d'actions : utilise le terme 'actifs' ou 'unités'.\n"
        "4. Rédige une synthèse lisible en 3 ou 4 puces synthétiques maximum.\n"
        "5. Conclus OBLIGATOIREMENT par : 'Ce rapport est fourni à titre informatif et ne constitue pas un conseil financier.'"
    )

    payload = {
        "model": config.ollama_model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Bilan chiffré du portefeuille : {payload_data}"},
        ],
    }

    try:
        response = requests.post(
            config.ollama_url,
            json=payload,
            timeout=config.request_timeout,
        )
        response.raise_for_status()

        data = response.json()
        if not isinstance(data, dict):
            raise ReportGenerationError("Format de réponse d'Ollama invalide.")

        content = data.get("message", {}).get("content")
        if not content or not isinstance(content, str) or not content.strip():
            raise ReportGenerationError("Le rapport renvoyé par Ollama est vide.")

        return content.strip()

    except requests.exceptions.Timeout as err:
        logger.error("Timeout lors de l'appel à Ollama : %s", err)
        raise ReportGenerationError("Le service d'analyse local n'a pas répondu dans le délai imparti.") from err

    except requests.exceptions.RequestException as err:
        logger.error("Erreur réseau/HTTP avec Ollama : %s", err)
        raise ReportGenerationError("Impossible de joindre le service d'analyse Ollama.") from err

    except (json.JSONDecodeError, ValueError, KeyError, TypeError) as err:
        logger.error("Erreur de décodage de la réponse Ollama : %s", err)
        raise ReportGenerationError("Réponse du service d'analyse illisible.") from err