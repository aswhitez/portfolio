# Portfolio App
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Package Manager](https://img.shields.io/badge/uv-enabled-purple)
Application Python locale de suivi de portefeuille d'investissement avec calculs déterministes et synthèse rédigée par le LLM local `phi4-mini` via **Ollama**.

## Architecture et Sécurité

- **Confidentialité totale :** Les données financières ne quittent jamais votre machine.
- **Précision financière :** Utilisation systématique du type `Decimal` pour éviter les imprécisions d'arrondis des flottants.
- **Validation stricte :** Contrôle des types, formats et limites numériques sur toutes les entrées utilisateur avant traitement.
- **Données de marché en direct :** Récupération via `yfinance` avec gestion explicite des cours indisponibles.
- **Cotations natives en Euros :** Prise en charge directe des tickers des places européennes (`.PA`, `.DE`) et paires crypto EUR (`BTC-EUR`) pour éviter les taux de conversion dynamiques.

## Prérequis

- **Python** `>= 3.10`
- **uv** (gestionnaire de paquets et d'environnements virtuels)
- **Ollama** en cours d'exécution avec le modèle `phi4-mini` (`ollama pull phi4-mini`)

## Installation

Installez l'environnement et les dépendances :

```bash
uv sync
```

## Configuration

Créez un fichier `positions.json` à la racine du projet avec vos actifs libellés en EUR :

```json
[
  {
    "ticker": "APC.DE",
    "quantite": "12",
    "prix_achat": "140.0",
    "devise": "EUR"
  },
  {
    "ticker": "BTC",
    "quantite": "0.45",
    "prix_achat": "52000.0",
    "devise": "EUR"
  }
]
```

### Variables d'environnement optionnelles

- `DEFAULT_CURRENCY` : Devise de référence globale (défaut : `EUR`).
- `REQUEST_TIMEOUT` : Délai d'attente réseau en secondes (défaut : `30`, recommandé `90` sur CPU).
- `OLLAMA_URL` : Point d'accès de l'API Ollama (défaut : `http://localhost:11434/api/chat`).
- `OLLAMA_MODEL` : Nom du modèle local (défaut : `phi4-mini`).

## Exécution

Lancer l'interface en ligne de commande :

```bash
uv run python -m portfolio.cli
```

## Validation et Tests

Lancer la suite complète de tests unitaires :

```bash
uv run pytest
```

Vérifier la sécurité des dépendances et la compilation du code :

```bash
uv audit
uv run python -m compileall portfolio
```

## Avertissement Légal

Cette application est fournie à titre purement informatif et ne constitue pas un conseil en investissement financier.
