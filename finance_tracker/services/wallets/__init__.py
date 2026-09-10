"""Reading watched addresses.

Balances and transfer history, pulled from public indexers, so a portfolio can
be followed without being retyped. Read-only throughout: the app never holds a
key, never signs, and never broadcasts anything.

Two limits are structural rather than temporary, and every screen built on this
package says so:

* **A chain records movements, not prices.** A cost basis derived from one is a
  reconstruction — see :mod:`finance_tracker.services.wallets.cost_basis` for
  the method and its failure modes.
* **Querying an indexer discloses the address** to whoever runs it. That is why
  syncing is opt-in per wallet and can be turned off without deleting anything.
"""
