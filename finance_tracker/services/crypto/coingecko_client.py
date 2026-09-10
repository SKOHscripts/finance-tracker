"""CoinGecko access for the signal engine and the wallet importer.

One client for every market call the app makes: the ranking, per-asset price
history, historical prices used to reconstruct a cost basis, and the lookup
that turns a token contract into a listing.

Two things shape this module. The free plan is rate-limited, so calls are
spaced and retried with a backoff rather than fired in a loop. And Streamlit
Cloud sits behind an egress the API sometimes refuses, so requests carry a
browser-like fingerprint — the same workaround the Bitcoin price service has
needed since the app was first hosted.
"""
import time
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

import requests

from finance_tracker.config import COINGECKO_API_URL, COINGECKO_TIMEOUT

# HTTP statuses worth retrying: a rate limit, or the gateway having a bad
# moment. Anything else is a real answer and is raised immediately.
RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})

DEFAULT_RETRIES = 4
INITIAL_BACKOFF_SECONDS = 2.0

# Sent on every call. CoinGecko's edge rejects some datacentre traffic that
# does not look like a browser, which is what a hosted Streamlit app is.
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
    "Connection": "keep-alive",
    }

# CoinGecko platform identifiers, keyed by the app's Chain names. Used to turn
# a token contract address into a listing.
CONTRACT_PLATFORMS: dict[str, str] = {
    "ETHEREUM": "ethereum",
    "BASE": "base",
    "ARBITRUM": "arbitrum-one",
    "OPTIMISM": "optimistic-ethereum",
    "POLYGON": "polygon-pos",
    "BSC": "binance-smart-chain",
    "SOLANA": "solana",
    }


class CoinGeckoError(RuntimeError):
    """Raised when CoinGecko cannot be reached or answers with an error."""


@dataclass
class MarketRow:
    """One asset as CoinGecko ranks it, before any metric is computed.

    Parameters
    ----------
    id : str
        CoinGecko identifier.
    symbol : str
        Ticker in upper case.
    name : str
        Display name.
    rank : Optional[int]
        Market-capitalisation rank, None when unranked.
    price : Optional[float]
        Current price in the quote currency.
    market_cap : Optional[float]
        Market capitalisation in the quote currency.
    volume_24h : Optional[float]
        Traded volume over 24 hours, in the quote currency.
    """

    id: str
    symbol: str
    name: str
    rank: Optional[int] = None
    price: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None

    @classmethod
    def from_api(cls, payload: dict) -> "MarketRow":
        """Build a row from a ``/coins/markets`` entry."""
        return cls(
            id=payload["id"],
            symbol=str(payload.get("symbol", "")).upper(),
            name=payload.get("name", ""),
            rank=payload.get("market_cap_rank"),
            price=payload.get("current_price"),
            market_cap=payload.get("market_cap"),
            volume_24h=payload.get("total_volume"),
            )


@dataclass(frozen=True)
class Listing:
    """One CoinGecko listing, as a search returns it.

    Deliberately not a :class:`MarketRow`: a search answers "which asset do you
    mean", not "what is it worth". It carries no price, and pretending
    otherwise by reusing the market row would invite code to read a field that
    was never fetched.

    Parameters
    ----------
    id : str
        CoinGecko identifier — the key every later price call is made with.
    symbol : str
        Ticker in upper case.
    name : str
        Display name.
    rank : Optional[int]
        Market-capitalisation rank, None when unranked. The one signal a user
        has for telling a real asset from a namesake with the same ticker.
    """

    id: str
    symbol: str
    name: str
    rank: Optional[int] = None

    @classmethod
    def from_api(cls, payload: dict) -> "Listing":
        """Build a listing from a ``/search`` coin entry."""
        return cls(
            id=payload["id"],
            symbol=str(payload.get("symbol", "")).upper(),
            name=payload.get("name", ""),
            rank=payload.get("market_cap_rank"),
            )

    @property
    def label(self) -> str:
        """One line identifying the listing unambiguously."""
        rank = f"#{self.rank}" if self.rank else "—"
        return f"{self.name} ({self.symbol}) · {rank} · {self.id}"


class CoinGeckoClient:
    """Rate-limited CoinGecko client with retries and an in-process cache.

    Parameters
    ----------
    api_key : str, optional
        Demo API key. Optional everywhere: without one the free tier applies,
        which is enough for a weekly scan. Nothing ships with the app — the
        key, when there is one, comes from the user's own settings.
    base_url : str, optional
        Endpoint override, for a proxy or a paid host.
    timeout : int, optional
        Per-request timeout in seconds.
    request_delay : float, optional
        Minimum spacing between two calls, in seconds. The free tier drops
        bursts, so the scan paces itself rather than retrying its way through.
    session : requests.Session, optional
        Session to reuse. One is created when omitted.
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = COINGECKO_API_URL,
        timeout: int = COINGECKO_TIMEOUT,
        request_delay: float = 2.5,
        session: Optional[requests.Session] = None,
        ) -> None:
        self.api_key = api_key or ""
        self.base_url = (base_url or COINGECKO_API_URL).rstrip("/")
        self.timeout = timeout
        self.request_delay = max(request_delay, 0.0)
        self._session = session or requests.Session()
        self._last_call_at = 0.0
        # Historical prices never change, so one call per (asset, day) is
        # enough however many transfers land on that day.
        self._history_cache: dict[tuple[str, str, str], Optional[float]] = {}

    # ── transport ─────────────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        headers = dict(_BROWSER_HEADERS)
        if self.api_key:
            headers["x-cg-demo-api-key"] = self.api_key
        return headers

    def _throttle(self) -> None:
        """Sleep just long enough to keep calls ``request_delay`` apart."""
        if self.request_delay <= 0:
            return
        elapsed = time.monotonic() - self._last_call_at
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)

    def get(self, path: str, params: Optional[dict] = None,
            retries: int = DEFAULT_RETRIES) -> Any:
        """GET *path* and return the decoded JSON.

        Parameters
        ----------
        path : str
            Path below the API root, starting with a slash.
        params : dict, optional
            Query parameters.
        retries : int, optional
            Total attempts before giving up.

        Returns
        -------
        Any
            Decoded JSON.

        Raises
        ------
        CoinGeckoError
            On a non-retryable status, an undecodable body, or once the
            retries are spent.
        """
        url = f"{self.base_url}{path}"
        delay = INITIAL_BACKOFF_SECONDS
        last_error = ""

        for attempt in range(retries):
            self._throttle()
            try:
                response = self._session.get(
                    url, params=params or {}, headers=self._headers(), timeout=self.timeout
                    )
                self._last_call_at = time.monotonic()

                if response.status_code in RETRYABLE_STATUSES:
                    last_error = f"HTTP {response.status_code}"
                    if attempt < retries - 1:
                        time.sleep(delay)
                        delay *= 2
                        continue
                    raise CoinGeckoError(
                        f"CoinGecko a répondu {response.status_code} sur {path} "
                        f"après {retries} tentatives. Le quota du plan gratuit est "
                        "probablement atteint : réessaie dans quelques minutes."
                        )

                if response.status_code >= 400:
                    raise CoinGeckoError(
                        f"CoinGecko a répondu {response.status_code} sur {path}."
                        )
                return response.json()

            except requests.exceptions.RequestException as exc:
                last_error = str(exc)
                self._last_call_at = time.monotonic()
                if attempt < retries - 1:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise CoinGeckoError(
                    f"Réseau indisponible sur {path} : {last_error}"
                    ) from exc
            except ValueError as exc:  # JSON decoding
                raise CoinGeckoError(
                    f"Réponse illisible de CoinGecko sur {path} : {exc}"
                    ) from exc

        raise CoinGeckoError(f"Échec après {retries} tentatives sur {path} : {last_error}")

    # ── market data ───────────────────────────────────────────────────────────

    def top_markets(self, vs_currency: str, depth: int) -> list[MarketRow]:
        """Return the *depth* largest assets by market capitalisation.

        Parameters
        ----------
        vs_currency : str
            Quote currency, lower case (e.g. ``"eur"``).
        depth : int
            How many entries to request. Ask for more than the ranking needs:
            stablecoins and wrappers get filtered out afterwards.

        Returns
        -------
        list[MarketRow]
            Rows in descending market-cap order.
        """
        payload = self.get("/coins/markets", {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": depth,
            "page": 1,
            "sparkline": "false",
            })
        return [MarketRow.from_api(row) for row in payload]

    def markets_by_ids(self, ids: list[str], vs_currency: str) -> dict[str, MarketRow]:
        """Return market rows for specific identifiers, keyed by identifier.

        Parameters
        ----------
        ids : list[str]
            CoinGecko identifiers. An empty list returns an empty mapping
            without calling the API.
        vs_currency : str
            Quote currency, lower case.

        Returns
        -------
        dict[str, MarketRow]
            Only the identifiers CoinGecko recognised. A caller must treat a
            missing key as "unknown asset", not as a zero.
        """
        if not ids:
            return {}
        payload = self.get("/coins/markets", {
            "vs_currency": vs_currency,
            "ids": ",".join(sorted(set(ids))),
            })
        return {row["id"]: MarketRow.from_api(row) for row in payload}

    def price_series(self, coin_id: str, vs_currency: str, days: int) -> list[list[float]]:
        """Return the raw ``[[timestamp_ms, price], ...]`` history.

        Parameters
        ----------
        coin_id : str
            CoinGecko identifier.
        vs_currency : str
            Quote currency, lower case.
        days : int
            History depth in days.

        Returns
        -------
        list[list[float]]
            Timestamp/price pairs, empty when the asset has no history.
        """
        payload = self.get(f"/coins/{coin_id}/market_chart", {
            "vs_currency": vs_currency,
            "days": days,
            "interval": "daily",
            })
        return payload.get("prices", [])

    def price_on(self, coin_id: str, day: date, vs_currency: str) -> Optional[float]:
        """Return the closing price of *coin_id* on *day*, or None.

        This is what turns an on-chain transfer into a euro amount. The free
        plan only serves the last 365 days; beyond that the endpoint returns
        no market data, and None is reported rather than a guess.

        Parameters
        ----------
        coin_id : str
            CoinGecko identifier.
        day : date
            Day to price, interpreted in UTC.
        vs_currency : str
            Quote currency, lower case.

        Returns
        -------
        float or None
            The price, or None when CoinGecko has no figure for that day.
        """
        cache_key = (coin_id, day.isoformat(), vs_currency.lower())
        if cache_key in self._history_cache:
            return self._history_cache[cache_key]

        try:
            payload = self.get(f"/coins/{coin_id}/history", {
                "date": day.strftime("%d-%m-%Y"),
                "localization": "false",
                })
        except CoinGeckoError:
            # A missing price must not abort a whole wallet import: the
            # transfer is recorded unpriced and counted as uncovered.
            self._history_cache[cache_key] = None
            return None

        price = (
            (payload or {})
            .get("market_data", {})
            .get("current_price", {})
            .get(vs_currency.lower())
            )
        value = float(price) if price is not None else None
        self._history_cache[cache_key] = value
        return value

    def search(self, query: str, limit: int = 12) -> list[Listing]:
        """Find listings matching a name or a ticker.

        The lookup for an asset no address can reveal — Monero being the case
        this exists for. A ticker is not unique on CoinGecko: several tokens
        answer to the same three letters, so every hit keeps its rank and its
        identifier and the caller is expected to make the user choose rather
        than take the first.

        Parameters
        ----------
        query : str
            Free text: a name ("monero") or a ticker ("xmr").
        limit : int, optional
            Most hits to return. Results arrive ranked by relevance.

        Returns
        -------
        list of Listing
            Matching listings, best first. Empty when nothing matches — which
            is an answer, not a failure.

        Raises
        ------
        CoinGeckoError
            When the API cannot be reached or refuses the call.
        """
        text = (query or "").strip()
        if not text:
            return []

        payload = self.get("/search", {"query": text}, retries=2)
        coins = (payload or {}).get("coins") or []
        return [Listing.from_api(c) for c in coins[:limit] if c.get("id")]

    def resolve_id(self, coin_id: str) -> Optional[Listing]:
        """Confirm that *coin_id* is a real listing.

        Used to check an identifier before it is stored: a typo saved here
        would fail silently at every later scan, as an asset that never
        prices.

        Returns
        -------
        Listing or None
            The listing, or None when CoinGecko does not know the identifier.
        """
        wanted = (coin_id or "").strip().lower()
        if not wanted:
            return None
        try:
            payload = self.get(
                f"/coins/{wanted}",
                {"localization": "false", "tickers": "false",
                 "market_data": "false", "community_data": "false",
                 "developer_data": "false"},
                retries=2,
                )
        except CoinGeckoError:
            return None
        if not payload or "id" not in payload:
            return None
        return Listing(
            id=payload["id"],
            symbol=str(payload.get("symbol", "")).upper(),
            name=payload.get("name", ""),
            rank=payload.get("market_cap_rank"),
            )

    def resolve_contract(self, chain: str, contract_address: str) -> Optional[dict]:
        """Look up the listing for a token contract.

        Parameters
        ----------
        chain : str
            App chain name (e.g. ``"BASE"``).
        contract_address : str
            Token contract address.

        Returns
        -------
        dict or None
            ``{"id", "symbol", "name"}`` when the token is listed, None when
            the chain is unsupported or the token is unknown — which is the
            normal outcome for an airdropped token nobody trades.
        """
        platform = CONTRACT_PLATFORMS.get(chain.upper())
        if not platform or not contract_address:
            return None
        try:
            payload = self.get(
                f"/coins/{platform}/contract/{contract_address.lower()}",
                {"localization": "false"},
                retries=2,
                )
        except CoinGeckoError:
            return None
        if not payload or "id" not in payload:
            return None
        return {
            "id": payload["id"],
            "symbol": str(payload.get("symbol", "")).upper(),
            "name": payload.get("name", ""),
            }
