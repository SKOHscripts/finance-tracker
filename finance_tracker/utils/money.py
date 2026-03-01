"""Money utilities"""
from decimal import Decimal, ROUND_HALF_UP


def format_eur(amount: Decimal | float) -> str:
    """Format a monetary amount in EUR.

    Parameters
    ----------
    amount : Decimal or float
        The amount to format.

    Returns
    -------
    str
        Formatted string in the format "1 234,56 €".
    """

    if isinstance(amount, float):
        amount = Decimal(str(amount))
    amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return f"{amount:,} €".replace(",", " ").replace(".", ",")


def to_decimal(value: str | float | int) -> Decimal:
    """Convert a value to Decimal safely.

    Parameters
    ----------
    value : str, float, or int
        The value to convert.

    Returns
    -------
    Decimal
        The converted Decimal value.
    """

    if isinstance(value, str):
        return Decimal(value)

    return Decimal(str(value))


def round_decimal(value: Decimal, places: int = 2):
    """Round a Decimal to the specified number of decimal places.

    Parameters
    ----------
    value : Decimal
        The Decimal value to round.
    places : int, optional
        Number of decimal places (default is 2).

    Returns
    -------
    Decimal
        The rounded Decimal value.
    """
    quantizer = Decimal(10) ** -places

    return value.quantize(quantizer, rounding=ROUND_HALF_UP)


def safe_divide(numerator: Decimal | int, denominator: Decimal | int, places: int = 2):
    """Perform safe division with Decimal.

    Parameters
    ----------
    numerator : Decimal or int
        The numerator.
    denominator : Decimal or int
        The denominator.
    places : int, optional
        Number of decimal places for rounding (default is 2).

    Returns
    -------
    Decimal
        The rounded result, or Decimal(0) if denominator is zero.
    """

    if denominator == 0:
        return Decimal(0)
    num = Decimal(str(numerator))
    denom = Decimal(str(denominator))

    return round_decimal(num / denom, places)
