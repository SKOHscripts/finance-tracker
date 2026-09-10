"""Tests for looking a listing up by name or ticker.

The manual-asset form asks CoinGecko "which asset do you mean" and stores the
identifier the user picks. That identifier is then the key of every price call
for as long as the position exists, so a wrong one does not fail loudly — it
quietly prices something else at every scan afterwards. These tests cover the
two ways it can go wrong: a shape the parser mishandles, and a name that does
not exist.

The HTTP layer is stubbed rather than called: the point is the parsing and the
refusals, and a test that reaches the real API would be rate-limited into
flaking.
"""
# pylint: disable=redefined-outer-name  # pytest fixture pattern
# pylint: disable=too-few-public-methods  # the stubs mirror requests' surface
# pylint: disable=unused-argument  # FakeSession.get mirrors requests' signature
import pytest

from finance_tracker.services.crypto.coingecko_client import (
    CoinGeckoClient,
    CoinGeckoError,
    Listing,
    )

# One `/search` answer, trimmed to the keys the client reads. XMR is the case
# the feature exists for; the two others share a ticker on purpose.
SEARCH_XMR = {
    "coins": [
        {"id": "monero", "name": "Monero", "symbol": "XMR", "market_cap_rank": 30},
        {"id": "monero-classic", "name": "Monero Classic", "symbol": "XMC",
         "market_cap_rank": None},
        ],
    "exchanges": [{"id": "should-be-ignored"}],
    }


class FakeResponse:
    """Enough of a requests response for the client to read it."""

    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class FakeSession:
    """A requests session that answers from a script and records its calls."""

    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):  # noqa: D102
        self.calls.append((url, params or {}))
        return FakeResponse(self.payload, self.status_code)


def client_for(payload, status_code=200):
    """A client wired to a scripted session, with the throttle switched off."""
    session = FakeSession(payload, status_code)
    client = CoinGeckoClient(request_delay=0.0, session=session)
    return client, session


class TestSearch:
    """Turning free text into listings the user can choose between."""

    def test_a_ticker_finds_the_asset(self):
        client, session = client_for(SEARCH_XMR)

        hits = client.search("xmr")

        assert [h.id for h in hits] == ["monero", "monero-classic"]
        assert session.calls[0][1] == {"query": "xmr"}

    def test_the_symbol_is_upper_cased(self):
        client, _ = client_for({"coins": [{"id": "monero", "symbol": "xmr"}]})
        assert client.search("monero")[0].symbol == "XMR"

    def test_only_coins_are_returned(self):
        """The endpoint also answers with exchanges and categories."""
        client, _ = client_for(SEARCH_XMR)
        assert all(isinstance(h, Listing) for h in client.search("xmr"))

    def test_hits_are_capped(self):
        client, _ = client_for({"coins": [{"id": f"c{i}"} for i in range(50)]})
        assert len(client.search("c", limit=5)) == 5

    def test_an_entry_without_an_identifier_is_dropped(self):
        """Nothing can be priced with it, so offering it would be a trap."""
        client, _ = client_for({"coins": [{"name": "Ghost"}, {"id": "monero"}]})
        assert [h.id for h in client.search("x")] == ["monero"]

    def test_no_match_is_an_answer_not_a_failure(self):
        client, _ = client_for({"coins": []})
        assert client.search("zzzz") == []

    def test_a_missing_coins_key_is_survived(self):
        client, _ = client_for({})
        assert client.search("zzzz") == []

    @pytest.mark.parametrize("query", ["", "   ", None])
    def test_an_empty_query_makes_no_call(self, query):
        """No point spending a rate-limited call on nothing."""
        client, session = client_for(SEARCH_XMR)
        assert client.search(query) == []
        assert not session.calls

    def test_an_api_failure_is_raised(self):
        """The view catches this to tell the user, rather than showing zero hits."""
        client, _ = client_for({}, status_code=404)
        with pytest.raises(CoinGeckoError):
            client.search("monero")


class TestListingLabel:
    """The one line the user picks from."""

    def test_the_label_carries_what_distinguishes_two_namesakes(self):
        """Name and ticker are not enough: the rank and the id are the tiebreak."""
        label = Listing(id="monero", symbol="XMR", name="Monero", rank=30).label
        assert "Monero" in label
        assert "XMR" in label
        assert "#30" in label
        assert "monero" in label

    def test_an_unranked_listing_says_so_rather_than_claiming_a_rank(self):
        assert "#" not in Listing(id="x", symbol="X", name="X").label


class TestResolveId:
    """Confirming an identifier before it is stored."""

    def test_a_real_identifier_comes_back(self):
        client, _ = client_for({
            "id": "monero", "symbol": "xmr", "name": "Monero", "market_cap_rank": 30,
            })

        listing = client.resolve_id("Monero")

        assert listing is not None
        assert listing.id == "monero"
        assert listing.symbol == "XMR"

    def test_an_unknown_identifier_is_none_not_an_error(self):
        """A typo is a normal outcome here, not an exception."""
        client, _ = client_for({}, status_code=404)
        assert client.resolve_id("no-such-coin") is None

    def test_an_answer_without_an_id_is_none(self):
        client, _ = client_for({"error": "coin not found"})
        assert client.resolve_id("no-such-coin") is None

    @pytest.mark.parametrize("value", ["", "   ", None])
    def test_an_empty_identifier_makes_no_call(self, value):
        client, session = client_for({"id": "monero"})
        assert client.resolve_id(value) is None
        assert not session.calls
