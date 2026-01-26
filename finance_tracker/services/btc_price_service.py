"""Service d'appel API CoinGecko pour prix BTC."""
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

    def get_btc_price_eur(self):
        """Récupère le prix BTC/EUR depuis CoinGecko.

        Returns:
            Prix BTC en EUR (Decimal)

        Raises:
            BTCPriceServiceError: En cas d'erreur réseau ou API
        """
        try:
            url = f"{self.base_url}/simple/price"
            params = {
                "ids": "bitcoin",
                "vs_currencies": "eur",
            }
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            price = data.get("bitcoin", {}).get("eur")

            if price is None:
                raise BTCPriceServiceError("Prix BTC/EUR non trouvé dans la réponse")

            return Decimal(str(price))

        except requests.exceptions.RequestException as e:
            raise BTCPriceServiceError(f"Erreur lors de l'appel API CoinGecko: {e}")
        except (KeyError, ValueError, TypeError) as e:
            raise BTCPriceServiceError(f"Erreur lors du parsing de la réponse: {e}")
