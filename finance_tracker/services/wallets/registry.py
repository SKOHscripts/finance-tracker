"""Picking a connector, and the credentials it runs with.

Credentials live in the user's own database, never in the repository and never
in an environment variable baked into a deployment: the hosted app is shared,
so a key committed anywhere would be everyone's key. Each provider is usable
without one wherever the chain allows it.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlmodel import Session

from finance_tracker.domain.enums import EVM_CHAIN_IDS, Chain
from finance_tracker.domain.models import ProviderCredential

from .base import UnsupportedChainError, WalletProvider
from .bitcoin import BitcoinProvider
from .evm import EvmProvider
from .solana import SolanaProvider

# Provider identifiers as stored in ``ProviderCredential.provider``.
ETHERSCAN = "ETHERSCAN"
COINGECKO = "COINGECKO"
SOLANA_RPC = "SOLANA_RPC"
MEMPOOL = "MEMPOOL"

#: Which chains need a key to work at all, and which merely benefit from one.
KEY_REQUIRED: frozenset[Chain] = frozenset(EVM_CHAIN_IDS)


@dataclass
class Credential:
    """One provider's optional key and endpoint override."""

    provider: str
    api_key: str = ""
    base_url: str = ""

    @property
    def configured(self) -> bool:
        """Whether the user has supplied anything for this provider."""
        return bool(self.api_key or self.base_url)


def get_credential(session: Session, provider: str) -> Credential:
    """Read a provider's credential, or an empty one when unset."""
    row = session.exec(
        select(ProviderCredential).where(ProviderCredential.provider == provider)
        ).scalars().first()
    if row is None:
        return Credential(provider=provider)
    return Credential(provider=provider, api_key=row.api_key or "", base_url=row.base_url or "")


def set_credential(
    session: Session, provider: str, api_key: str = "", base_url: str = ""
    ) -> ProviderCredential:
    """Create or update a provider's credential.

    Parameters
    ----------
    session : Session
        Open database session. Committed here.
    provider : str
        Provider identifier.
    api_key : str, optional
        The key. An empty string clears it.
    base_url : str, optional
        Endpoint override. An empty string restores the default.

    Returns
    -------
    ProviderCredential
        The stored row.
    """
    row = session.exec(
        select(ProviderCredential).where(ProviderCredential.provider == provider)
        ).scalars().first()

    if row is None:
        row = ProviderCredential(provider=provider)
        session.add(row)

    row.api_key = (api_key or "").strip()
    row.base_url = (base_url or "").strip()
    row.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(row)
    return row


def provider_for(chain: Chain, session: Optional[Session] = None) -> WalletProvider:
    """Build the connector for *chain*, configured from stored credentials.

    Parameters
    ----------
    chain : Chain
        Chain to read.
    session : Session, optional
        Session used to look up credentials. Without one the connector runs
        anonymously, which works for Bitcoin and Solana but not for EVM.

    Returns
    -------
    WalletProvider
        A ready connector.

    Raises
    ------
    UnsupportedChainError
        When no connector covers *chain*.
    """
    if chain is Chain.BITCOIN:
        credential = get_credential(session, MEMPOOL) if session else Credential(MEMPOOL)
        return BitcoinProvider(base_url=credential.base_url or None)

    if chain is Chain.SOLANA:
        credential = get_credential(session, SOLANA_RPC) if session else Credential(SOLANA_RPC)
        return SolanaProvider(base_url=credential.base_url or None)

    if chain in EVM_CHAIN_IDS:
        credential = get_credential(session, ETHERSCAN) if session else Credential(ETHERSCAN)
        return EvmProvider(
            chain=chain,
            api_key=credential.api_key,
            base_url=credential.base_url or None,
            )

    raise UnsupportedChainError(
        f"Aucun connecteur pour {chain.value}. Chaînes supportées : "
        f"{', '.join(c.value for c in Chain)}."
        )


def missing_requirements(session: Session, chain: Chain) -> Optional[str]:
    """Return what is missing before *chain* can be synced, or None.

    Checked before a sync so the user gets a sentence naming the setting to
    fill in, rather than an explorer's rejection message.
    """
    if chain in KEY_REQUIRED and not get_credential(session, ETHERSCAN).api_key:
        return (
            "Les chaînes EVM demandent une clé d'API d'explorateur, gratuite et "
            "personnelle. Renseigne-la dans les réglages du signal crypto ; elle est "
            "stockée dans ta base et n'est jamais envoyée ailleurs qu'à l'explorateur."
            )
    return None
