"""Domain models (SQLModel)."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Column, DateTime, Field, Numeric, SQLModel, UniqueConstraint

from .enums import (
    Chain,
    CostBasisConfidence,
    MarketRegime,
    ProductType,
    QuantityUnit,
    SignalVerdict,
    TransactionType,
    TransferDirection,
    TransferKind,
    ValuationSource,
    )


class Product(SQLModel, table=True):
    """Investment product model for portfolio tracking.

    Stores product details such as name, type, risk level, fees, and tax information.

    Parameters
    ----------
    id : Optional[int]
        Primary key, auto-generated if not provided.
    name : str
        Unique product name, indexed for fast lookup.
    type : ProductType
        Type of investment product (stock, crypto, SCPI, etc.).
    quantity_unit : QuantityUnit
        Unit for quantity (NONE for non-quantity products).
    description : str
        Optional product description.
    risk_level : str
        User-friendly risk level display (e.g., "Très faible", "Faible").
    fees_description : str
        Description of applicable fees.
    tax_info : str
        Tax-related information.
    created_at : datetime
        Timestamp of product creation, timezone-aware.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)  # Unique name prevents duplicates
    type: ProductType
    quantity_unit: QuantityUnit = QuantityUnit.NONE  # Default to NONE for non-quantity products
    description: str = ""
    risk_level: str = ""  # User-friendly display: "Très faible", "Faible", etc.
    fees_description: str = ""
    tax_info: str = ""
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),  # Store timezone-aware timestamps
        )


class Transaction(SQLModel, table=True):
    """
    Transaction model for database records.

    Tracks financial or quantity-based movements associated with products.

    Parameters
    ----------
    product_id : int
        Foreign key to the associated product.
    date : datetime
        Date and time of the transaction.
    type : TransactionType
        Type of transaction (e.g., buy, sell, deposit, withdrawal).
    amount_eur : Decimal, optional
        Transaction amount in EUR (max 10^10, 12 digits total, 2 decimal places).
    quantity : Decimal, optional
        Transaction quantity for asset-based transactions (up to 20 digits, 8 decimal places).
    note : str, optional
        Optional note or description for the transaction (default: empty string).
    created_at : datetime, optional
        Timestamp when the record was created (default: current UTC time).

    Returns
    -------
    Transaction
        SQLModel instance representing a transaction record in the database.

    Raises
    ------
    None
        This model does not raise exceptions; database constraints handle validation.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    date: datetime  # Date of the transaction
    type: TransactionType
    # EUR amount: max 10^10 (12 digits total, 2 after decimal) - covers billions
    amount_eur: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=12, scale=2)),
        )
    # Quantity: high precision for crypto (8 decimals) and large amounts (20 digits total)
    quantity: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=20, scale=8)),
        )
    note: str = ""
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


class Valuation(SQLModel, table=True):
    """Value snapshot at a specific date for portfolio tracking.

    Represents a historical record of portfolio or product valuation for
    financial tracking and analysis purposes.

    Parameters
    ----------
    id : Optional[int]
        Primary key, auto-generated if not provided.
    product_id : int
        Foreign key referencing the product being valued.
    date : datetime
        Date of the valuation snapshot.
    total_value_eur : Decimal
        Total portfolio value in EUR (precision: 12, scale: 2).
    unit_price_eur : Optional[Decimal]
        Unit price for per-unit priced products (e.g., SCPI shares, BTC).
        Null if not applicable.
    created_at : datetime
        Timestamp of record creation, defaults to UTC now.

    Returns
    -------
    Valuation
        A database model instance representing a valuation snapshot.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    date: datetime
    # Total portfolio value in EUR: sufficient for large portfolios
    total_value_eur: Decimal = Field(
        sa_column=Column(Numeric(precision=12, scale=2))
        )
    # Unit price for products priced per unit (SCPI shares, BTC, etc.)
    unit_price_eur: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=12, scale=2)),
        )
    # Where the figure came from. Lets a price refresh skip rows the user typed
    # by hand instead of silently overwriting a manual correction.
    source: ValuationSource = Field(default=ValuationSource.MANUAL)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


class RateSchedule(SQLModel, table=True):
    """Interest rate schedule for savings products such as term deposits or bonds.

    Stores effective dates and annual interest rates with four decimal precision.

    Parameters
    ----------
    id : Optional[int]
        Primary key, auto-generated if not provided.
    product_id : int
        Foreign key referencing the associated product.
    date_effective : datetime
        Date when the rate becomes effective.
    annual_rate : Decimal
        Annual interest rate with four decimal places (e.g., 0.0300 = 3%).
    created_at : datetime
        Timestamp of record creation, defaults to current UTC time.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    date_effective: datetime
    # Annual rate with 4 decimal places (e.g., 0.0300 = 3%)
    annual_rate: Decimal = Field(
        sa_column=Column(Numeric(precision=5, scale=4))
        )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Crypto signal — tables added by schema migration 001.
#
# These carry the state the rotation engine needs between two scans. In the
# standalone tool this state lived in JSON files next to the code; in the
# tracker it belongs to the user's database, which never leaves their machine.
# ═══════════════════════════════════════════════════════════════════════════════


class CryptoAsset(SQLModel, table=True):
    """Market identity of a product, so the signal engine can price it.

    A `Product` says what the user owns in accounting terms; a `CryptoAsset`
    says which CoinGecko listing that product maps to. Keeping the two apart
    means an existing Bitcoin product can join the arbitrage by gaining a row
    here, without touching the products table.

    Parameters
    ----------
    id : Optional[int]
        Primary key, auto-generated if not provided.
    product_id : int
        Foreign key to the product this market identity belongs to. Unique:
        a product maps to exactly one listing.
    coingecko_id : str
        CoinGecko asset identifier (e.g. "monero", "ethereum"). This is the
        key every price and history call is made with.
    symbol : str
        Ticker in upper case, cached for display (e.g. "XMR").
    manual_units : Optional[Decimal]
        Quantity typed by the user, which outranks every derived figure —
        the chain balance included. None means the automatic derivation
        applies. Exists because a chain can be read correctly and still be
        wrong about what is held: a balance sitting at an address the user
        does not watch, or one they do not control.
    manual_cost_basis_eur : Optional[Decimal]
        Total capital invested, typed by the user, outranking the ledger and
        any on-chain reconstruction. None means the automatic derivation
        applies. Stored as a total rather than a unit cost so that correcting
        the quantity does not silently move the money spent.
    gas_reserve_eur : Decimal
        Share of the position that is never proposed for a swap, for an asset
        that also pays chain fees. A position with nothing left above its
        reserve is reported but not arbitrated.
    arbitrated : bool
        Whether the engine may propose a move on this position. False keeps
        the asset priced and displayed but out of every verdict.
    created_at : datetime
        Timestamp of record creation, timezone-aware.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    # One market identity per product: a second row would give the engine two
    # prices for the same holding.
    product_id: int = Field(foreign_key="product.id", unique=True, index=True)
    coingecko_id: str = Field(index=True)
    symbol: str = ""
    manual_units: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=28, scale=8), nullable=True),
        )
    manual_cost_basis_eur: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=14, scale=2), nullable=True),
        )
    gas_reserve_eur: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        )
    arbitrated: bool = True
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


class ScanRun(SQLModel, table=True):
    """One execution of the rotation engine, with its market-wide findings.

    The per-position outcomes hang off this row as `PositionVerdict` records.
    Persisting the run is not bookkeeping: the persistence gates count how many
    consecutive scans a candidate held up, so without this history no rotation
    or refuge move can ever complete.

    Parameters
    ----------
    id : Optional[int]
        Primary key, auto-generated if not provided.
    scan_date : datetime
        UTC timestamp of the scan, indexed for chronological reads.
    verdict : SignalVerdict
        Most engaging verdict present on any position. A summary, not a
        decision: each position carries its own.
    regime : MarketRegime
        Observed market state at scan time.
    candidate_coingecko_id : str
        Identifier of the ranked candidate every position was arbitrated
        against, empty when no candidate could be selected.
    candidate_symbol : str
        Ticker of that candidate, cached for display.
    quote_currency : str
        Currency every figure in this run is denominated in.
    regime_json : str
        Full regime detail as JSON (measures, thresholds, sufficiency).
    ranking_json : str
        Complete scored ranking as JSON, so a report can be re-rendered
        without calling the API again.
    discarded_json : str
        Higher-ranked assets skipped by the candidate fallback, with reasons.
    insufficient_history_json : str
        Symbols whose price history was too short to score reliably.
    created_at : datetime
        Timestamp of record creation, timezone-aware.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    scan_date: datetime = Field(index=True)
    verdict: SignalVerdict = SignalVerdict.CONSERVER
    regime: MarketRegime = MarketRegime.INCONNU
    candidate_coingecko_id: str = ""
    candidate_symbol: str = ""
    quote_currency: str = "EUR"
    # JSON blobs: read-only detail for rendering, never queried on.
    regime_json: str = ""
    ranking_json: str = ""
    discarded_json: str = ""
    insufficient_history_json: str = ""
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


class PositionVerdict(SQLModel, table=True):
    """Outcome of one scan for one position, with the figures behind it.

    Every position is arbitrated on its own: its own notional, therefore its
    own cost of moving, therefore possibly its own verdict. The two
    `*_gates_but_persistence` flags are what the next scan reads to count a
    streak, so they are stored as columns rather than buried in the JSON.

    Parameters
    ----------
    id : Optional[int]
        Primary key, auto-generated if not provided.
    scan_run_id : int
        Foreign key to the scan this verdict belongs to.
    product_id : int
        Foreign key to the product being arbitrated.
    coingecko_id : str
        Market identifier of the held asset at scan time. Kept denormalised so
        history survives a later re-mapping of the product.
    symbol : str
        Ticker of the held asset, cached for display.
    verdict : SignalVerdict
        Verdict for this position.
    arbitrated : bool
        False when the position was reported but excluded from arbitrage
        (gas reserve covering the whole line, or `arbitrated` turned off).
    notional_eur : Decimal
        Market value of the whole line at scan time.
    gas_reserve_eur : Decimal
        Untouchable share withheld from any swap.
    arbitrable_eur : Decimal
        Notional minus reserve: what a proposed move would actually carry.
    cost_basis_eur : Optional[Decimal]
        Capital invested in the line, None when it cannot be derived.
    unrealised_gain_pct : Optional[Decimal]
        Latent gain in percent, None without a cost basis.
    score_delta : Optional[Decimal]
        Candidate score minus held score, in standard deviations.
    round_trip_cost_pct : Optional[Decimal]
        Estimated cost of a two-leg move, as a percentage of the notional.
    required_edge_pct : Optional[Decimal]
        Momentum advantage the candidate had to clear for a rotation.
    streak_weeks : int
        Consecutive scans the rotation gates held, persistence excluded.
    rotation_gates_but_persistence : bool
        Whether every rotation gate but persistence passed this scan.
    temporisation_gates_but_persistence : bool
        Same, for the refuge gates.
    detail_json : str
        Gates, sub-mechanisms and swap plan as JSON, for rendering.
    created_at : datetime
        Timestamp of record creation, timezone-aware.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    scan_run_id: int = Field(foreign_key="scanrun.id", index=True)
    product_id: int = Field(foreign_key="product.id", index=True)
    coingecko_id: str = ""
    symbol: str = ""
    verdict: SignalVerdict = SignalVerdict.CONSERVER
    arbitrated: bool = True

    notional_eur: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        )
    gas_reserve_eur: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        )
    arbitrable_eur: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        )
    cost_basis_eur: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=12, scale=2)),
        )
    unrealised_gain_pct: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=9, scale=2)),
        )
    score_delta: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=9, scale=3)),
        )
    round_trip_cost_pct: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=9, scale=2)),
        )
    required_edge_pct: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=9, scale=2)),
        )

    # Read by the next scan to count consecutive weeks. Columns, not JSON.
    streak_weeks: int = 0
    rotation_gates_but_persistence: bool = False
    temporisation_gates_but_persistence: bool = False

    detail_json: str = ""
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


class ProfitTaken(SQLModel, table=True):
    """Record that the invested capital was recovered on a position.

    The profit-taking rule fires at most once per line, so it needs a durable
    trace. One row here is what stops the same line from being trimmed again
    at every scan.

    Parameters
    ----------
    id : Optional[int]
        Primary key, auto-generated if not provided.
    product_id : int
        Foreign key to the trimmed product.
    coingecko_id : str
        Market identifier at the time of the trim.
    scan_date : datetime
        Date of the scan that proposed the trim.
    fraction : Decimal
        Share of the line the proposal covered, between 0 and 1.
    amount_eur : Decimal
        Value of that share at scan time.
    cost_basis_eur : Optional[Decimal]
        Capital the trim was meant to recover.
    created_at : datetime
        Timestamp of record creation, timezone-aware.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id", index=True)
    coingecko_id: str = ""
    scan_date: datetime
    fraction: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(precision=6, scale=4), nullable=False, server_default="0"),
        )
    amount_eur: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        )
    cost_basis_eur: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=12, scale=2)),
        )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


class SwapExecution(SQLModel, table=True):
    """A swap the user actually executed, linked back to what was proposed.

    The engine proposes and never executes. This row is how a proposal that
    was carried out re-enters the tracker: it references the SELL and BUY
    transactions written alongside it, so cost basis and portfolio value stay
    consistent with the rest of the app.

    Parameters
    ----------
    id : Optional[int]
        Primary key, auto-generated if not provided.
    position_verdict_id : Optional[int]
        Foreign key to the verdict this execution followed, None for a swap
        recorded without a matching proposal.
    from_product_id : int
        Foreign key to the product sold.
    to_product_id : Optional[int]
        Foreign key to the product bought, None while it has not been created.
    to_coingecko_id : str
        Market identifier of the asset bought.
    executed_at : datetime
        When the swap was executed.
    amount_eur : Decimal
        Value moved, before fees.
    units_received : Optional[Decimal]
        Units of the bought asset actually received.
    fees_eur : Decimal
        Total fees paid, all legs included.
    sell_transaction_id : Optional[int]
        Foreign key to the SELL transaction written for this swap.
    buy_transaction_id : Optional[int]
        Foreign key to the BUY transaction written for this swap.
    note : str
        Free-form note (route used, provider, anything worth remembering).
    created_at : datetime
        Timestamp of record creation, timezone-aware.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    position_verdict_id: Optional[int] = Field(
        default=None, foreign_key="positionverdict.id", index=True)
    from_product_id: int = Field(foreign_key="product.id", index=True)
    to_product_id: Optional[int] = Field(default=None, foreign_key="product.id")
    to_coingecko_id: str = ""
    executed_at: datetime
    amount_eur: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        )
    units_received: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=20, scale=8)),
        )
    fees_eur: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        )
    # The two legs written into the ledger, so the swap is auditable from the
    # transactions page as well as from here.
    sell_transaction_id: Optional[int] = Field(default=None, foreign_key="transaction.id")
    buy_transaction_id: Optional[int] = Field(default=None, foreign_key="transaction.id")
    note: str = ""
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Wallet import — tables added by schema migration 001.
#
# A watched address turns a portfolio the user retypes into one the tool reads.
# Two limits are structural and are surfaced everywhere these rows are shown:
# a chain records movements, never a purchase price, so any cost basis derived
# here is an estimate; and querying a public indexer discloses the address to
# a third party, which is why every wallet is opt-in and can be synced off.
# ═══════════════════════════════════════════════════════════════════════════════


class Wallet(SQLModel, table=True):
    """A watched address, read-only.

    The tool never holds a key and never signs anything: it reads balances and
    transfer history from a public indexer. `auto_sync` exists so an address
    can be kept in the database without ever being sent to a third party.

    Parameters
    ----------
    id : Optional[int]
        Primary key, auto-generated if not provided.
    label : str
        User-facing name for the wallet.
    chain : Chain
        Blockchain the address belongs to; picks the connector.
    address : str
        Public address, stored as entered and matched case-insensitively on
        EVM chains.
    auto_sync : bool
        Whether the tool may query an indexer for this wallet. False keeps the
        row entirely local.
    derive_cost_basis : bool
        Whether transfer history should be fetched and priced to estimate a
        cost basis. Costs extra API calls, so it can be turned off.
    last_synced_at : Optional[datetime]
        When the last successful sync completed, None if never.
    last_sync_error : str
        Message from the last failed sync, empty when the last one succeeded.
    created_at : datetime
        Timestamp of record creation, timezone-aware.
    """

    __table_args__ = (UniqueConstraint("chain", "address", name="uq_wallet_chain_address"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    label: str = ""
    chain: Chain
    address: str = Field(index=True)
    # Opt-in: an address is only disclosed to an indexer once the user says so.
    auto_sync: bool = True
    derive_cost_basis: bool = True
    last_synced_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True)),
        )
    last_sync_error: str = ""
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


class WalletHolding(SQLModel, table=True):
    """A token balance discovered at a watched address.

    Rows are refreshed wholesale on each sync: the chain is the source of
    truth for units, so a holding that disappeared on-chain disappears here.
    Only the user's own edits — the product mapping and the `ignored` flag —
    survive a refresh.

    Parameters
    ----------
    id : Optional[int]
        Primary key, auto-generated if not provided.
    wallet_id : int
        Foreign key to the wallet the balance was found at.
    contract_address : str
        Token contract, empty string for the chain's native coin.
    symbol : str
        Ticker as reported by the chain, upper case.
    name : str
        Token name as reported by the chain.
    decimals : int
        Token decimals, used to scale raw on-chain amounts.
    units : Decimal
        Balance in whole units, already scaled.
    coingecko_id : str
        Resolved market identifier, empty when the token could not be matched
        to a listing and therefore cannot be priced.
    product_id : Optional[int]
        Tracker product this holding feeds, None while unmapped.
    ignored : bool
        User flag for dust and airdropped spam, excluded from every total.
    last_seen_at : datetime
        Timestamp of the sync that last saw this balance.
    created_at : datetime
        Timestamp of record creation, timezone-aware.
    """

    __table_args__ = (
        UniqueConstraint("wallet_id", "contract_address", name="uq_holding_wallet_contract"),
        )

    id: Optional[int] = Field(default=None, primary_key=True)
    wallet_id: int = Field(foreign_key="wallet.id", index=True)
    # Empty string, not NULL: it takes part in a unique constraint, and SQLite
    # treats NULLs as distinct, which would let duplicates through.
    contract_address: str = ""
    symbol: str = ""
    name: str = ""
    decimals: int = 18
    # Scaled units. 18 decimals covers every EVM token without rounding.
    units: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(precision=38, scale=18), nullable=False, server_default="0"),
        )
    coingecko_id: str = ""
    product_id: Optional[int] = Field(default=None, foreign_key="product.id", index=True)
    ignored: bool = False
    last_seen_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


class WalletTransfer(SQLModel, table=True):
    """One movement of one asset in or out of a watched address.

    This is the raw material the cost-basis estimate is built from. `kind` is
    the tool's reading of the movement and `unit_price_eur` the market price
    at the block's timestamp; both are recorded so the estimate can be audited
    line by line rather than taken on trust.

    Parameters
    ----------
    id : Optional[int]
        Primary key, auto-generated if not provided.
    wallet_id : int
        Foreign key to the wallet the movement was seen at.
    tx_hash : str
        Transaction hash on the chain.
    log_index : int
        Position within the transaction, so several transfers in one
        transaction stay distinct.
    timestamp : datetime
        Block time, in UTC.
    direction : TransferDirection
        Whether units entered or left the wallet.
    contract_address : str
        Token contract, empty string for the native coin.
    symbol : str
        Ticker of the asset moved.
    units : Decimal
        Amount moved, in whole units.
    counterparty : str
        The other address in the movement.
    kind : TransferKind
        How this movement is treated for cost basis.
    unit_price_eur : Optional[Decimal]
        Market price at `timestamp`, None when no price could be obtained.
    value_eur : Optional[Decimal]
        `units` times `unit_price_eur`, None when unpriced.
    price_source : str
        Where the price came from, empty when unpriced.
    created_at : datetime
        Timestamp of record creation, timezone-aware.
    """

    __table_args__ = (
        UniqueConstraint("wallet_id", "tx_hash", "log_index", name="uq_transfer_identity"),
        )

    id: Optional[int] = Field(default=None, primary_key=True)
    wallet_id: int = Field(foreign_key="wallet.id", index=True)
    tx_hash: str = Field(index=True)
    log_index: int = 0
    timestamp: datetime = Field(index=True)
    direction: TransferDirection
    contract_address: str = ""
    symbol: str = ""
    units: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(precision=38, scale=18), nullable=False, server_default="0"),
        )
    counterparty: str = ""
    kind: TransferKind = TransferKind.UNKNOWN
    unit_price_eur: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=20, scale=8)),
        )
    value_eur: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=14, scale=2)),
        )
    price_source: str = ""
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


class CostBasisEstimate(SQLModel, table=True):
    """Derived unit cost for a product, and how much of it is actually known.

    A chain never records a purchase price, so this is a reconstruction:
    priced acquisitions in, proportional reductions on disposals out. The
    uncovered figures are part of the result, not a footnote — they say how
    much of the position the number fails to explain. `manual_unit_cost_eur`
    always wins when set, because the user knows things the chain does not.

    Parameters
    ----------
    id : Optional[int]
        Primary key, auto-generated if not provided.
    product_id : int
        Foreign key to the product this estimate applies to. Unique.
    units : Decimal
        Units the estimate was computed over.
    cost_basis_eur : Decimal
        Total capital attributed to those units.
    unit_cost_eur : Optional[Decimal]
        Derived average cost per unit, None when nothing could be derived.
    manual_unit_cost_eur : Optional[Decimal]
        User-supplied unit cost. When set, it overrides the derived one
        everywhere, including in the signal engine.
    uncovered_units : Decimal
        Units whose origin could not be priced.
    confidence : CostBasisConfidence
        Coverage band of the estimate.
    method : str
        Identifier of the derivation method, for reproducibility.
    computed_at : datetime
        When the estimate was last recomputed.
    note : str
        Free-form explanation shown next to the figure.
    created_at : datetime
        Timestamp of record creation, timezone-aware.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id", unique=True, index=True)
    units: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(precision=38, scale=18), nullable=False, server_default="0"),
        )
    cost_basis_eur: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(precision=14, scale=2), nullable=False, server_default="0"),
        )
    unit_cost_eur: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=20, scale=8)),
        )
    # The user's own figure. Set, it wins over everything derived below.
    manual_unit_cost_eur: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(precision=20, scale=8)),
        )
    uncovered_units: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(precision=38, scale=18), nullable=False, server_default="0"),
        )
    confidence: CostBasisConfidence = CostBasisConfidence.NONE
    method: str = ""
    computed_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )
    note: str = ""
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


class ProviderCredential(SQLModel, table=True):
    """An optional API key or endpoint override for one data provider.

    Nothing here ships with the app: the public repository carries no key, and
    each user brings their own quota. Keys live in the user's database, which
    means they travel inside an exported `.db` file — the settings page says
    so where the key is entered.

    Parameters
    ----------
    id : Optional[int]
        Primary key, auto-generated if not provided.
    provider : str
        Provider identifier (e.g. "ETHERSCAN", "COINGECKO", "SOLANA_RPC").
        Unique.
    api_key : str
        The key, empty when the provider is used anonymously.
    base_url : str
        Endpoint override, empty to use the built-in default. Lets a user
        point at their own node instead of a public one.
    updated_at : datetime
        When the credential was last changed.
    created_at : datetime
        Timestamp of record creation, timezone-aware.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str = Field(unique=True, index=True)
    api_key: str = ""
    base_url: str = ""
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )


class SignalSetting(SQLModel, table=True):
    """One rotation threshold the user has moved away from its shipped value.

    The thresholds themselves live in `config/signal_rules.toml`, which is part
    of the repository and the same for everyone. This table holds only the
    *deviations*: a row exists solely for a setting the user has changed.

    Storing deviations rather than a full copy is what keeps a hosted release
    useful. A user who never touched a threshold picks up an improved default
    on the next deploy; one who deliberately tightened a barrier keeps their
    figure. A full snapshot would freeze both, and the second kind of user
    would never learn the first kind of change had happened.

    The value is text, and the type it should become is read from the rules
    dataclass field it maps to. A column per threshold would mean a migration
    for every new setting, on a table whose whole purpose is to change.

    Parameters
    ----------
    id : Optional[int]
        Primary key, auto-generated if not provided.
    key : str
        Dotted path of the setting, e.g. "gates.min_score_delta". Unique:
        one deviation per setting.
    value : str
        The user's value, serialised as text and coerced back on load.
    updated_at : datetime
        When the deviation was last written.
    created_at : datetime
        Timestamp of record creation, timezone-aware.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True)
    value: str = ""
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True)),
        )
