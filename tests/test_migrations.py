"""Tests for the schema migration runner.

The point of these is one promise: a `.db` file exported by an older release
still opens, still holds its rows, and gains whatever the current release needs.
Everything else here exists to protect that.
"""
# pylint: disable=redefined-outer-name  # pytest fixture pattern
import pytest
from sqlalchemy import inspect, text
from sqlmodel import create_engine

from finance_tracker.repositories.migrations import (
    LATEST_VERSION,
    _safe_column_ddl,
    _safe_identifier,
    MIGRATIONS,
    applied_migrations,
    current_version,
    is_up_to_date,
    run_migrations,
    )
from finance_tracker.repositories.sqlmodel_repo import init_db

# The v1.0.0 schema, by hand. Four tables, no `source` on valuation, none of the
# crypto or wallet tables. Written out rather than generated so the test keeps
# describing the old shape even as the models move on.
LEGACY_SCHEMA = (
    """CREATE TABLE product (
        id INTEGER PRIMARY KEY,
        name VARCHAR NOT NULL UNIQUE,
        type VARCHAR NOT NULL,
        quantity_unit VARCHAR,
        description VARCHAR,
        risk_level VARCHAR,
        fees_description VARCHAR,
        tax_info VARCHAR,
        created_at DATETIME
    )""",
    """CREATE TABLE "transaction" (
        id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        date DATETIME NOT NULL,
        type VARCHAR NOT NULL,
        amount_eur NUMERIC(12, 2),
        quantity NUMERIC(20, 8),
        note VARCHAR,
        created_at DATETIME
    )""",
    """CREATE TABLE valuation (
        id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        date DATETIME NOT NULL,
        total_value_eur NUMERIC(12, 2) NOT NULL,
        unit_price_eur NUMERIC(12, 2),
        created_at DATETIME
    )""",
    """CREATE TABLE rateschedule (
        id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        date_effective DATETIME NOT NULL,
        annual_rate NUMERIC(5, 4) NOT NULL,
        created_at DATETIME
    )""",
    )


@pytest.fixture()
def legacy_engine(tmp_path):
    """A database shaped like one written by v1.0.0, with rows in it."""
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as conn:
        for statement in LEGACY_SCHEMA:
            conn.execute(text(statement))
        conn.execute(text(
            "INSERT INTO product (name, type, quantity_unit) "
            "VALUES ('Livret A', 'CASH', 'NONE')"
            ))
        conn.execute(text(
            "INSERT INTO valuation (product_id, date, total_value_eur) "
            "VALUES (1, '2025-01-01', 12500.00)"
            ))
        conn.execute(text(
            'INSERT INTO "transaction" (product_id, date, type, amount_eur) '
            "VALUES (1, '2025-01-01', 'DEPOSIT', 500.00)"
            ))
    return engine


@pytest.fixture()
def fresh_engine(tmp_path):
    """An empty database, as a first-time user gets."""
    return create_engine(f"sqlite:///{tmp_path / 'fresh.db'}")


def test_migration_versions_are_unique_and_ordered():
    """Versions must be distinct and strictly increasing.

    A reused number would silently skip a migration on every database that
    already recorded it.
    """
    versions = [m.version for m in MIGRATIONS]
    assert versions == sorted(versions)
    assert len(versions) == len(set(versions))
    assert all(v > 0 for v in versions)


def test_legacy_database_reports_version_zero(legacy_engine):
    """A database written before migrations existed reads as version 0."""
    assert current_version(legacy_engine) == 0
    assert not is_up_to_date(legacy_engine)


def test_legacy_database_keeps_its_rows(legacy_engine):
    """The whole promise: migrating must not lose anything."""
    init_db(legacy_engine)

    with legacy_engine.connect() as conn:
        assert conn.execute(text("SELECT name FROM product")).scalar() == "Livret A"
        assert conn.execute(
            text("SELECT total_value_eur FROM valuation")).scalar() == 12500.00
        assert conn.execute(
            text('SELECT amount_eur FROM "transaction"')).scalar() == 500.00


def test_legacy_database_gains_the_new_column(legacy_engine):
    """`valuation.source` is added, and existing rows are backfilled to MANUAL.

    MANUAL is right, not merely convenient: every row written before this
    release was typed by a human.
    """
    init_db(legacy_engine)

    with legacy_engine.connect() as conn:
        columns = {c["name"] for c in inspect(conn).get_columns("valuation")}
        assert "source" in columns
        assert conn.execute(text("SELECT source FROM valuation")).scalar() == "MANUAL"


def test_legacy_database_gains_the_new_tables(legacy_engine):
    """Every crypto and wallet table exists after migrating."""
    init_db(legacy_engine)

    with legacy_engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())

    for expected in (
        "cryptoasset", "scanrun", "positionverdict", "profittaken", "swapexecution",
        "wallet", "walletholding", "wallettransfer", "costbasisestimate",
        "providercredential", "signalsetting",
        ):
        assert expected in tables, f"table manquante : {expected}"


def test_the_correction_columns_arrive_empty(legacy_engine):
    """`cryptoasset` gains its two correction columns, holding nothing.

    Null is the point of them being nullable: it means "no correction", which
    is not the same claim as zero. Nothing is backfilled because nothing was
    corrected — a migration must never invent a figure the user did not type.
    """
    init_db(legacy_engine)

    with legacy_engine.connect() as conn:
        columns = {c["name"]: c for c in inspect(conn).get_columns("cryptoasset")}
        for name in ("manual_units", "manual_cost_basis_eur"):
            assert name in columns, f"colonne manquante : {name}"
            assert columns[name]["nullable"], f"{name} doit accepter NULL"


def test_a_database_already_at_version_two_only_gains_the_third(legacy_engine):
    """The common upgrade path: someone who installed the previous release."""
    init_db(legacy_engine)  # brings it fully up to date

    # Roll the stamp back to 2, as a database from that release would read.
    with legacy_engine.begin() as conn:
        conn.execute(text("DELETE FROM schema_version WHERE version > 2"))

    assert current_version(legacy_engine) == 2

    applied = run_migrations(legacy_engine)
    assert [m.version for m in applied] == [3]
    assert current_version(legacy_engine) == LATEST_VERSION


def test_migration_is_recorded(legacy_engine):
    """Applied migrations are stamped, so they never run twice."""
    applied = init_db(legacy_engine)

    assert [m.version for m in applied] == [m.version for m in MIGRATIONS]
    assert current_version(legacy_engine) == LATEST_VERSION
    assert is_up_to_date(legacy_engine)

    log = applied_migrations(legacy_engine)
    assert len(log) == len(MIGRATIONS)
    assert log[0]["name"] == MIGRATIONS[0].name
    assert log[0]["applied_at"]


def test_running_twice_is_a_no_op(legacy_engine):
    """A second call changes nothing and reports nothing applied."""
    init_db(legacy_engine)
    assert not init_db(legacy_engine)
    assert not run_migrations(legacy_engine)


def test_fresh_database_ends_up_at_the_same_version(fresh_engine):
    """A new database and a migrated old one land on the same schema."""
    init_db(fresh_engine)

    assert current_version(fresh_engine) == LATEST_VERSION
    with fresh_engine.connect() as conn:
        columns = {c["name"] for c in inspect(conn).get_columns("valuation")}
        assert "source" in columns


def test_fresh_and_migrated_schemas_match(fresh_engine, legacy_engine):
    """The two paths must produce the same tables and columns.

    Divergence here is the bug this whole module exists to prevent: an app that
    works for new users and breaks for anyone restoring a backup.
    """
    init_db(fresh_engine)
    init_db(legacy_engine)

    def shape(engine):
        with engine.connect() as conn:
            inspector = inspect(conn)
            return {
                table: {c["name"] for c in inspector.get_columns(table)}
                for table in sorted(inspector.get_table_names())
                }

    assert shape(fresh_engine) == shape(legacy_engine)


class TestIdentifierGuards:
    """SQL identifiers are validated before interpolation.

    A table or column name cannot be a bound parameter, so it has to be
    interpolated. Every name used here is a literal written in this module —
    but "written by a developer" is a convention, and these guards are what
    turn it into a guarantee for the migrations nobody has written yet.
    """

    def test_a_plain_identifier_passes_through(self):
        assert _safe_identifier("schema_version") == "schema_version"
        assert _safe_identifier("valuation") == "valuation"

    @pytest.mark.parametrize("bad", [
        "",
        "1abc",                       # cannot start with a digit
        "drop table",                 # a space is not part of a name
        "users; DROP TABLE product",  # a second statement
        "col--comment",               # a comment marker
        "tab'le",                     # a quote
        "a" * 64,                     # implausibly long
        ])
    def test_anything_else_is_refused(self, bad):
        with pytest.raises(ValueError, match="invalide"):
            _safe_identifier(bad)

    def test_a_column_definition_passes_through(self):
        assert _safe_column_ddl("VARCHAR(20) NOT NULL DEFAULT 'MANUAL'")
        assert _safe_column_ddl("NUMERIC(12, 2)")

    @pytest.mark.parametrize("bad", [
        "",
        "VARCHAR(20); DROP TABLE product",
        "TEXT /* comment */",
        "TEXT DEFAULT (SELECT name FROM product)",
        ])
    def test_a_smuggled_statement_is_refused(self, bad):
        with pytest.raises(ValueError, match="invalide"):
            _safe_column_ddl(bad)

    def test_the_version_table_name_is_itself_a_valid_identifier(self):
        """The guard would be theatre if the module's own constant failed it."""
        from finance_tracker.repositories.migrations import SCHEMA_VERSION_TABLE
        assert _safe_identifier(SCHEMA_VERSION_TABLE)


class TestVersionTableCompatibility:
    """The bookkeeping table survives how it was created.

    Early builds created `schema_version` with a raw CREATE TABLE; it is now
    declared as a SQLAlchemy Table so every read and write goes through Core.
    A database written by either has to stay readable by the other — otherwise
    the migration runner would fail on exactly the databases it exists to
    rescue.
    """

    @staticmethod
    def _raw_version_table(engine, version, name):
        """Create and stamp the table the way the raw-SQL version did."""
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS schema_version ("
                "  version INTEGER PRIMARY KEY,"
                "  name VARCHAR(100) NOT NULL,"
                "  applied_at VARCHAR(40) NOT NULL)"
                ))
            conn.execute(text(
                "INSERT INTO schema_version (version, name, applied_at) "
                "VALUES (:v, :n, :t)"
                ), {"v": version, "n": name, "t": "2026-01-01T00:00:00+00:00"})

    def test_a_raw_created_table_is_read_by_core(self, legacy_engine):
        self._raw_version_table(legacy_engine, 1, MIGRATIONS[0].name)
        assert current_version(legacy_engine) == 1

    def test_only_the_missing_migrations_are_applied(self, legacy_engine):
        """Version 1 already stamped: only what comes after it should run."""
        self._raw_version_table(legacy_engine, 1, MIGRATIONS[0].name)

        applied = init_db(legacy_engine)

        assert [m.version for m in applied] == [
            m.version for m in MIGRATIONS if m.version > 1
            ]
        assert current_version(legacy_engine) == LATEST_VERSION

    def test_the_earlier_stamp_survives(self, legacy_engine):
        """The pre-existing row keeps its own timestamp, unrewritten."""
        self._raw_version_table(legacy_engine, 1, MIGRATIONS[0].name)
        init_db(legacy_engine)

        log = applied_migrations(legacy_engine)
        assert log[0]["applied_at"] == "2026-01-01T00:00:00+00:00"
        assert len(log) == len(MIGRATIONS)
