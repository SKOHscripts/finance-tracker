"""Service d'appel API pour le prix BTC avec fallback robuste pour le Cloud."""

import requests
from decimal import Decimal
from finance_tracker.config import COINGECKO_API_URL, COINGECKO_TIMEOUT


class BTCPriceServiceError(Exception):
    """Exception service BTC."""
    pass


class BTCPriceService:
    """Service de récupération du prix BTC/EUR avec mécanismes anti-blocage."""

    def __init__(self, base_url: str = COINGECKO_API_URL, timeout: int = COINGECKO_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout

        # En-têtes essentiels pour contourner les protections Cloudflare des APIs depuis Streamlit Cloud
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
            "Connection": "keep-alive"
        }

    def get_btc_price_eur(self) -> Decimal:
        """
        Tente de récupérer le prix BTC/EUR via plusieurs APIs en cascade.
        Idéal pour les environnements hébergés type Streamlit Cloud/Heroku.
        """
        errors = []

        # Tentative 1 : Kraken (Très permissif sur les IP de datacenters, pas de Cloudflare agressif)
        try:
            return self._fetch_from_kraken()
        except Exception as e:
            errors.append(f"Kraken: {str(e)}")

        # Tentative 2 : Binance Publique (Robuste, mais bloque parfois des plages AWS entières)
        try:
            return self._fetch_from_binance()
        except Exception as e:
            errors.append(f"Binance: {str(e)}")

        # Tentative 3 : CoinGecko (Souvent bloqué depuis le cloud sans clé API)
        try:
            return self._fetch_from_coingecko()
        except Exception as e:
            errors.append(f"CoinGecko: {str(e)}")

        # Si tout a échoué
        error_msg = "Toutes les APIs ont bloqué la requête depuis le serveur. Détails:\n" + "\n".join(errors)
        raise BTCPriceServiceError(error_msg)

    def _fetch_from_kraken(self) -> Decimal:
        """Fallback 1: Kraken API (Excellente disponibilité)."""
        url = "https://api.kraken.com/0/public/Ticker"
        params = {"pair": "XBTEUR"}

        response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()

        if data.get("error"):
            raise ValueError(str(data["error"]))

        # Kraken renvoie une liste complexe, le prix actuel (dernier trade) est dans data["result"]["XXBTZEUR"]["c"][0]
        try:
            price = data["result"]["XXBTZEUR"]["c"][0]

            return Decimal(str(price))
        except (KeyError, IndexError):
            raise ValueError("Structure de réponse Kraken inattendue")

    def _fetch_from_binance(self) -> Decimal:
        """Fallback 2: Binance API."""
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {"symbol": "BTCEUR"}

        response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        price = data.get("price")

        if not price:
            raise ValueError("Prix BTCEUR non trouvé dans la réponse Binance")

        return Decimal(str(price))

    def _fetch_from_coingecko(self) -> Decimal:
        """Fallback 3: CoinGecko API (Risque de 'Max Retries' ou 429 depuis le Cloud)."""
        url = f"{self.base_url}/simple/price"
        params = {
            "ids": "bitcoin",
            "vs_currencies": "eur"
        }

        response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        price = data.get("bitcoin", {}).get("eur")

        if price is None:
            raise ValueError("Prix BTC/EUR non trouvé dans la réponse CoinGecko")

        return Decimal(str(price))
