"""Utilitaires monétaires."""
from decimal import Decimal, ROUND_HALF_UP


def format_eur(amount: Decimal | float) -> str:
    """Formate un montant en EUR.

    Args:
        amount: Montant en Decimal ou float

    Returns:
        Chaîne formatée "1 234,56 €"
    """

    if isinstance(amount, float):
        amount = Decimal(str(amount))
    amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return f"{amount:,} €".replace(",", " ").replace(".", ",")


def to_decimal(value: str | float | int) -> Decimal:
    """Convertit une valeur en Decimal de manière sûre.

    Args:
        value: Valeur à convertir

    Returns:
        Decimal
    """

    if isinstance(value, str):
        return Decimal(value)

    return Decimal(str(value))


def round_decimal(value: Decimal, places: int = 2):
    """Arrondit un Decimal au nombre de décimales demandé.

    Args:
        value: Decimal à arrondir
        places: Nombre de décimales

    Returns:
        Decimal arrondi
    """
    quantizer = Decimal(10) ** -places

    return value.quantize(quantizer, rounding=ROUND_HALF_UP)


def safe_divide(numerator: Decimal | int, denominator: Decimal | int, places: int = 2):
    """Division sûre avec Decimal.

    Args:
        numerator: Numérateur
        denominator: Dénominateur
        places: Décimales pour arrondi

    Returns:
        Résultat arrondi, ou Decimal(0) si dénominateur nul
    """

    if denominator == 0:
        return Decimal(0)
    num = Decimal(str(numerator))
    denom = Decimal(str(denominator))

    return round_decimal(num / denom, places)
