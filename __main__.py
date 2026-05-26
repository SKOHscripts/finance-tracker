"""Point d'entrée module.

Permet d'exécuter la CLI via:
    python -m finance_tracker
"""

from finance_tracker.cli import app


def main() -> None:
    """Entry point for the finance-tracker CLI."""
    app()


if __name__ == "__main__":
    main()
