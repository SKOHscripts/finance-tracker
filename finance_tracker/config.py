"""Configuration de l'application."""
from pathlib import Path

# Chemins
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "finance.db"
REPORTS_DIR = DATA_DIR / "reports"
DOCS_DIR = PROJECT_ROOT / "docs"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# URL de base de données
DATABASE_URL = f"sqlite:///{DB_PATH}"

# API
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
COINGECKO_TIMEOUT = 10  # secondes

# Création automatique des répertoires
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)
