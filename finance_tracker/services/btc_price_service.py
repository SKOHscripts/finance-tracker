"""Service d'appel API pour le prix BTC avec fallback robuste pour le Cloud."""

import requests
from decimal import Decimal
from finance_tracker.config import COINGECKO_API_URL, COINGECKO_TIMEOUT


class BTCPriceServiceError(Exception):
    """Exception service BTC."""
    pass


class BTCPriceService:
    """Service to retrieve BTC/EUR price with anti-blocking mechanisms.

    Retrieves the BTC/EUR price using multiple fallback APIs to maximize
    success rate in hosted environments like Streamlit Cloud or Heroku.

    Parameters
    ----------
    base_url : str, optional
        Base URL for the CoinGecko API. Defaults to COINGECKO_API_URL.
    timeout : int, optional
        Request timeout in seconds. Defaults to COINGECKO_TIMEOUT.
    """

    def __init__(self, base_url: str = COINGECKO_API_URL, timeout: int = COINGECKO_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout

        # Mimic a real browser to bypass Cloudflare protection on Streamlit Cloud
        self.headers = {
            # Browser fingerprint to appear as a regular Chrome user
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            # Accept both JSON and plain text responses
            "Accept": "application/json, text/plain, */*",
            # Prefer English, fallback to French (common on Streamlit Cloud)
            "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
            # Keep connection alive to avoid repeated handshakes
            "Connection": "keep-alive"
            }

    def get_btc_price_eur(self) -> Decimal:
        """Fetches BTC/EUR price using multiple fallback APIs.

        Attempts to retrieve the BTC/EUR price through a cascade of APIs,
        ideal for hosted environments like Streamlit Cloud or Heroku.

        Returns
        -------
        Decimal
            The current BTC/EUR price.

        Raises
        ------
        BTCPriceServiceError
            If all API attempts fail.
        """
        errors = []

        # CoinGecko frequently blocks cloud requests without an API key
        try:
            return self._fetch_from_coingecko()
        except Exception as e:
            errors.append(f"CoinGecko: {str(e)}")

        # Kraken is lenient with datacenter IPs and has no aggressive Cloudflare protection
        try:
            return self._fetch_from_kraken()
        except Exception as e:
            errors.append(f"Kraken: {str(e)}")

        # Binance is reliable but may block entire AWS ranges
        try:
            return self._fetch_from_binance()
        except Exception as e:
            errors.append(f"Binance: {str(e)}")

        # All providers blocked the request - aggregate errors for debugging
        error_msg = "Toutes les APIs ont bloqué la requête depuis le serveur. Détails:\n" + "\n".join(errors)
        raise BTCPriceServiceError(error_msg)

    def _fetch_from_kraken(self) -> Decimal:
        """Fallback 1: Kraken API (excellent availability).

        Returns
        -------
        Decimal
            The current BTC/EUR price from Kraken.
        """
        url = "https://api.kraken.com/0/public/Ticker"
        params = {"pair": "XBTEUR"}

        response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()

        # Kraken returns API-level errors as an array, separate from HTTP status

        if data.get("error"):
            raise ValueError(str(data["error"]))

        # Kraken returns a deeply nested structure; "c" contains [price, volume] of last trade
        try:
            price = data["result"]["XXBTZEUR"]["c"][0]

            # Use Decimal for precise monetary calculations, avoiding float rounding issues

            return Decimal(str(price))
        except (KeyError, IndexError):
            raise ValueError("Structure de réponse Kraken inattendue")

    def _fetch_from_binance(self) -> Decimal:
        """Fallback 2: Binance API.

        Returns
        -------
        Decimal
            The current BTC/EUR price from Binance.
        """
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
        """Fallback 3: CoinGecko API (may return 429 from cloud).

        Returns
        -------
        Decimal
            The current BTC/EUR price from CoinGecko.
        """
        # CoinGecko free API endpoint for simple price queries
        url = f"{self.base_url}/simple/price"
        # Request BTC price in EUR (vs_currencies specifies the target currency)
        params = {
            "ids": "bitcoin",
            "vs_currencies": "eur"
            }

        # Include API key in headers if provided, and enforce timeout to avoid hanging
        response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
        # Raise exception for 4xx/5xx responses instead of returning HTTP error
        response.raise_for_status()

        data = response.json()
        # Navigate nested dict: data["bitcoin"]["eur"] - handle missing keys gracefully
        price = data.get("bitcoin", {}).get("eur")

        # Validate response contains expected data structure

        if price is None:
            raise ValueError("Prix BTC/EUR non trouvé dans la réponse CoinGecko")

        # Convert to Decimal to preserve precision for financial calculations

        return Decimal(str(price))
