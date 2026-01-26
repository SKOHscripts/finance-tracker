"""Utilitaires dates."""
from datetime import datetime, date
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    """Retourne la date/heure actuelle en UTC avec timezone aware."""
    return datetime.now(ZoneInfo("UTC"))


def date_to_datetime(d: date) -> datetime:
    """Convertit une date en datetime (00:00:00 UTC)."""
    return datetime.combine(d, datetime.min.time()).replace(
        tzinfo=ZoneInfo("UTC")
    )


def datetime_to_date(dt: datetime) -> date:
    """Extrait la date d'un datetime."""
    return dt.date()
