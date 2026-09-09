"""Versioned schema migrations for the Finance Tracker database.

Why this exists
---------------
Until now the schema was created by ``SQLModel.metadata.create_all()`` alone.
That call adds *missing tables*, so it carries a database forward whenever a
release only adds tables — but it never touches a table that already exists.
The moment a release adds a column to ``valuation``, every ``.db`` file a user
exported before that release would open fine and then fail on the first query
mentioning the new column.

So each schema change gets a number, a name, and a function. Applied versions
are recorded in ``schema_version``; a database opened by a newer release runs
whatever it is missing, in order, once.

Idempotence
-----------
Every migration here is written to be safe to run twice: it checks for the
table or column before creating it. That is deliberate. A database created
fresh by ``create_all()`` already has the latest shape, and it still walks the
same migration list — so the guards are what let one code path serve both a
brand-new database and one written by an older release, with no "is this file
legacy?" guesswork.

A future migration that cannot be made idempotent (a data backfill, say) may
rely on the recorded version instead: it will not be re-run once stamped.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection, Engine
from sqlmodel import SQLModel

# Bare table name, no ORM model: this table must be readable before any model
# is known to be valid, including on a database written by an older release.
SCHEMA_VERSION_TABLE = "schema_version"

# Tables introduced by migration 001. Named explicitly rather than derived from
# metadata so that adding a model later does not silently change what an old
# migration does.
_CRYPTO_TABLES = (
    "cryptoasset",
    "scanrun",
    "positionverdict",
    "profittaken",
    "swapexecution",
)
_WALLET_TABLES = (
    "wallet",
    "walletholding",
    "wallettransfer",
    "costbasisestimate",
    "providercredential",
)


@dataclass(frozen=True)
class Migration:
    """One numbered schema change.

    Parameters
    ----------
    version : int
        Monotonic version number. Applied in ascending order, never reused.
    name : str
        Short identifier, recorded alongside the version and shown to the user.
    apply : Callable[[Connection], None]
        Function performing the change. Must tolerate being run against a
        database that already has the change.
    description : str
        One line explaining what the migration does and why.
    """

    version: int
    name: str
    apply: Callable[[Connection], None]
    description: str = ""


# ── Introspection helpers ──────────────────────────────────────────────────────


def _table_exists(conn: Connection, table: str) -> bool:
    """Return whether *table* exists in the database behind *conn*."""
    return inspect(conn).has_table(table)


def _column_exists(conn: Connection, table: str, column: str) -> bool:
    """Return whether *table* has a column named *column*.

    Returns False when the table itself is missing, so a caller can guard a
    column addition without also checking for the table.
    """
    if not _table_exists(conn, table):
        return False
    return any(col["name"] == column for col in inspect(conn).get_columns(table))


def _add_column(conn: Connection, table: str, column: str, ddl: str) -> bool:
    """Add *column* to *table* unless it is already there.

    Parameters
    ----------
    conn : Connection
        Open connection, inside the caller's transaction.
    table : str
        Table to alter. Missing tables are skipped, not created: a table that
        does not exist yet will be created at the latest shape by
        ``create_all()`` and needs no column patch.
    column : str
        Column name.
    ddl : str
        Type and constraints, e.g. ``VARCHAR(20) NOT NULL DEFAULT 'MANUAL'``.
        SQLite only accepts a constant default in ``ADD COLUMN``.

    Returns
    -------
    bool
        True when the column was added, False when it was already present or
        the table was missing.
    """
    if not _table_exists(conn, table) or _column_exists(conn, table, column):
        return False
    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
    return True


def _create_tables(conn: Connection, names: tuple[str, ...]) -> None:
    """Create the named tables from SQLModel metadata if they are missing.

    Only the named tables are considered, so a migration cannot accidentally
    create tables introduced by a later release.
    """
    tables = [SQLModel.metadata.tables[n] for n in names if n in SQLModel.metadata.tables]
    if tables:
        SQLModel.metadata.create_all(conn, tables=tables, checkfirst=True)


# ── Migrations ─────────────────────────────────────────────────────────────────


def _m001_crypto_and_wallet_tables(conn: Connection) -> None:
    """Add the crypto signal and wallet import tables.

    Pure additions: no existing table is touched, so a database written by
    v1.0.0 keeps every row it had and simply gains empty tables.
    """
    _create_tables(conn, _CRYPTO_TABLES + _WALLET_TABLES)


def _m002_valuation_source(conn: Connection) -> None:
    """Give ``valuation`` a ``source`` column, defaulting to MANUAL.

    Rows written before this release were all typed by a human, so MANUAL is
    the correct value for every one of them — which is exactly what the column
    default backfills. The column is what stops an automatic price refresh
    from overwriting a figure the user corrected by hand.
    """
    _add_column(conn, "valuation", "source", "VARCHAR(20) NOT NULL DEFAULT 'MANUAL'")


MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        version=1,
        name="crypto_and_wallet_tables",
        apply=_m001_crypto_and_wallet_tables,
        description="Tables du signal crypto et de l'import de wallets.",
        ),
    Migration(
        version=2,
        name="valuation_source",
        apply=_m002_valuation_source,
        description="Origine d'une valorisation : saisie manuelle ou cours récupéré.",
        ),
    )

LATEST_VERSION = max(m.version for m in MIGRATIONS)


# ── Runner ─────────────────────────────────────────────────────────────────────


def _ensure_version_table(conn: Connection) -> None:
    """Create ``schema_version`` if the database does not have it yet."""
    conn.execute(text(
        f"CREATE TABLE IF NOT EXISTS {SCHEMA_VERSION_TABLE} ("
        "  version INTEGER PRIMARY KEY,"
        "  name VARCHAR(100) NOT NULL,"
        "  applied_at VARCHAR(40) NOT NULL"
        ")"
        ))


def current_version(engine: Engine) -> int:
    """Return the highest schema version recorded for this database.

    Parameters
    ----------
    engine : Engine
        Engine pointing at the database to inspect.

    Returns
    -------
    int
        The recorded version, or 0 when nothing has been recorded — which is
        the case both for a database written before migrations existed and for
        one that has just been created.
    """
    with engine.connect() as conn:
        if not _table_exists(conn, SCHEMA_VERSION_TABLE):
            return 0
        row = conn.execute(
            text(f"SELECT MAX(version) FROM {SCHEMA_VERSION_TABLE}")
            ).scalar()
        return int(row or 0)


def is_up_to_date(engine: Engine) -> bool:
    """Return whether the database already carries every known migration."""
    return current_version(engine) >= LATEST_VERSION


def run_migrations(engine: Engine) -> list[Migration]:
    """Bring the database up to the latest schema version.

    Applies every migration numbered above the recorded version, in order,
    each in its own transaction so a failure leaves the recorded version
    matching what actually got applied.

    Parameters
    ----------
    engine : Engine
        Engine pointing at the database to migrate.

    Returns
    -------
    list[Migration]
        The migrations that ran, in the order they ran. Empty when the
        database was already current.

    Raises
    ------
    Exception
        Whatever the failing migration raises. The migrations applied before
        it stay applied and stay recorded.
    """
    with engine.begin() as conn:
        _ensure_version_table(conn)

    version = current_version(engine)
    applied: list[Migration] = []

    for migration in sorted(MIGRATIONS, key=lambda m: m.version):
        if migration.version <= version:
            continue
        # One transaction per migration: a later failure does not roll back an
        # earlier success, and the recorded version stays truthful.
        with engine.begin() as conn:
            migration.apply(conn)
            conn.execute(
                text(
                    f"INSERT INTO {SCHEMA_VERSION_TABLE} (version, name, applied_at) "
                    "VALUES (:v, :n, :t)"
                    ),
                {
                    "v": migration.version,
                    "n": migration.name,
                    "t": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    },
                )
        applied.append(migration)

    return applied


def applied_migrations(engine: Engine) -> list[dict]:
    """Return the migration log recorded in the database, oldest first.

    Parameters
    ----------
    engine : Engine
        Engine pointing at the database to inspect.

    Returns
    -------
    list[dict]
        One entry per applied migration with keys ``version``, ``name`` and
        ``applied_at``. Empty when the database has no migration table.
    """
    with engine.connect() as conn:
        if not _table_exists(conn, SCHEMA_VERSION_TABLE):
            return []
        rows = conn.execute(text(
            f"SELECT version, name, applied_at FROM {SCHEMA_VERSION_TABLE} ORDER BY version"
            )).all()
    return [{"version": r[0], "name": r[1], "applied_at": r[2]} for r in rows]
