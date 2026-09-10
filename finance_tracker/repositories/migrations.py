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
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    func,
    inspect,
    select,
    text,
    )
from sqlalchemy.engine import Connection, Engine
from sqlmodel import SQLModel

# Bare table name, no ORM model: this table must be readable before any model
# is known to be valid, including on a database written by an older release.
SCHEMA_VERSION_TABLE = "schema_version"

# Its own MetaData, deliberately separate from SQLModel's: this table is
# bookkeeping about the schema, not part of it, and `create_all()` has no
# business creating or dropping it alongside the domain tables.
_VERSION_METADATA = MetaData()
SCHEMA_VERSION = Table(
    SCHEMA_VERSION_TABLE,
    _VERSION_METADATA,
    Column("version", Integer, primary_key=True),
    Column("name", String(100), nullable=False),
    Column("applied_at", String(40), nullable=False),
    )

# SQL cannot bind a table or column name as a parameter, so identifiers have to
# be interpolated into the statement. Every identifier used here is a literal
# written in this module — but "written by a developer" is a convention, and a
# convention is not a guarantee. These patterns turn it into one: anything that
# is not a plain identifier, or not a plain type-and-constraints fragment, is
# refused before it can reach a statement.
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")
_COLUMN_DDL_RE = re.compile(r"^[A-Za-z0-9_ ()',.\-]{1,120}$")

# The character class above is not enough on its own: `TEXT DEFAULT (SELECT
# name FROM product)` is made entirely of letters, spaces and parentheses. A
# column definition is a type and its constraints, so any word that starts or
# joins a statement has no business in one. SQLite would refuse a subquery in
# ADD COLUMN anyway; this refuses it one layer earlier, where the message is
# useful.
_FORBIDDEN_IN_DDL = frozenset({
    "select", "insert", "update", "delete", "drop", "alter", "create",
    "attach", "detach", "pragma", "union", "from", "join", "where", "exec",
    })

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


def _safe_identifier(name: str, kind: str = "identifiant") -> str:
    """Return *name* if it is a plain SQL identifier, else raise.

    Parameters
    ----------
    name : str
        Table or column name destined for a statement.
    kind : str, optional
        What is being named, for the error message.

    Returns
    -------
    str
        The unchanged name.

    Raises
    ------
    ValueError
        When the name is not a bare identifier. Refusing is the point: a
        migration cannot be written that interpolates something arbitrary,
        even by accident.
    """
    if not _IDENTIFIER_RE.match(name or ""):
        raise ValueError(
            f"{kind.capitalize()} SQL invalide : {name!r}. "
            "Seules les lettres, chiffres et underscores sont acceptés."
            )
    return name


def _safe_column_ddl(ddl: str) -> str:
    """Return *ddl* if it is a plain type-and-constraints fragment, else raise.

    Parameters
    ----------
    ddl : str
        Fragment such as ``VARCHAR(20) NOT NULL DEFAULT 'MANUAL'``.

    Returns
    -------
    str
        The unchanged fragment.

    Raises
    ------
    ValueError
        When the fragment contains anything a column definition has no reason
        to contain — a semicolon, a comment marker, a nested statement.
    """
    if not _COLUMN_DDL_RE.match(ddl or ""):
        raise ValueError(
            f"Définition de colonne invalide : {ddl!r}. "
            "Un type et ses contraintes, rien de plus."
            )

    words = set(re.findall(r"[A-Za-z_]+", ddl.lower()))
    smuggled = words & _FORBIDDEN_IN_DDL
    if smuggled:
        raise ValueError(
            f"Définition de colonne invalide : {ddl!r}. "
            f"Mot-clé de requête interdit dans une définition de colonne : "
            f"{', '.join(sorted(smuggled))}."
            )
    return ddl


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

    # Validated, not merely trusted: see _safe_identifier.
    table = _safe_identifier(table, "nom de table")
    column = _safe_identifier(column, "nom de colonne")
    ddl = _safe_column_ddl(ddl)

    # The only raw SQL left in this module, and the only one that has to be:
    # SQLAlchemy Core has no construct for ALTER TABLE, which is what Alembic
    # exists to provide. Both interpolated values passed through the guards
    # above, so nothing reaches this line unvalidated.
    statement = f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"  # nosec B608
    conn.execute(text(statement))  # nosemgrep: avoid-sqlalchemy-text
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
    SCHEMA_VERSION.create(conn, checkfirst=True)


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
            select(func.max(SCHEMA_VERSION.c.version))  # pylint: disable=not-callable
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
            conn.execute(SCHEMA_VERSION.insert().values(
                version=migration.version,
                name=migration.name,
                applied_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                ))
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
        rows = conn.execute(
            select(
                SCHEMA_VERSION.c.version,
                SCHEMA_VERSION.c.name,
                SCHEMA_VERSION.c.applied_at,
                ).order_by(SCHEMA_VERSION.c.version)
            ).all()
    return [{"version": r[0], "name": r[1], "applied_at": r[2]} for r in rows]
