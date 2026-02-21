"""Service d'appel API pour prix BTC avec fallback."""

import requests
from decimal import Decimal
from finance_tracker.config import COINGECKO_API_URL, COINGECKO_TIMEOUT


class BTCPriceServiceError(Exception):
    """Exception service BTC."""
    pass


class BTCPriceService:
    """Service de récupération du prix BTC/EUR."""

    def __init__(self, base_url: str = COINGECKO_API_URL, timeout: int = COINGECKO_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        # Un User-Agent classique permet souvent de passer les sécurités anti-bots basiques
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FinanceTracker/1.0"
        }

    def get_btc_price_eur(self) -> Decimal:
        """
        Récupère le prix BTC/EUR depuis CoinGecko.
        Utilise l'API publique de Binance comme solution de secours (fallback).
        """
        try:
            return self._fetch_from_coingecko()
        except Exception as e_coingecko:
            print(f"Échec CoinGecko ({e_coingecko}), tentative avec Binance...")
            try:
                return self._fetch_from_binance()
            except Exception as e_binance:
                raise BTCPriceServiceError(
                    f"Toutes les API ont échoué.\nCoinGecko: {e_coingecko}\nBinance: {e_binance}"
                )

    def _fetch_from_coingecko(self) -> Decimal:
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
            raise BTCPriceServiceError("Prix BTC/EUR non trouvé dans la réponse CoinGecko")

        return Decimal(str(price))

    def _fetch_from_binance(self) -> Decimal:
        """Fallback sur l'API publique de Binance (ne nécessite pas de clé)."""
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {"symbol": "BTCEUR"}

        response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        price = data.get("price")

        if not price:
            raise BTCPriceServiceError("Prix BTCEUR non trouvé dans la réponse Binance")

        return Decimal(str(price))
