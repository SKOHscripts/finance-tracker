"""Dtae utilities"""
from datetime import datetime, date
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    """Get current UTC datetime with timezone information.

    Returns
    -------
    datetime
        Current datetime in UTC with timezone awareness.
    """

    return datetime.now(ZoneInfo("UTC"))


def date_to_datetime(d: date) -> datetime:
    """Convert a date to datetime at midnight UTC.

    Parameters
    ----------
    d : date
        Date object to convert.

    Returns
    -------
    datetime
        Datetime at 00:00:00 UTC.
    """

    return datetime.combine(d, datetime.min.time()).replace(
        tzinfo=ZoneInfo("UTC")
        )


def datetime_to_date(dt: datetime) -> date:
    """Extract date component from datetime.

    Parameters
    ----------
    dt : datetime
        Datetime object to extract date from.

    Returns
    -------
    date
        Date component of the datetime.
    """

    return dt.date()
