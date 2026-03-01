"""App configuration"""
from pathlib import Path

# Project root is two levels up from this config file (config/ subdirectory)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "finance.db"
REPORTS_DIR = DATA_DIR / "reports"
DOCS_DIR = PROJECT_ROOT / "docs"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# SQLite URL format for SQLAlchemy
DATABASE_URL = f"sqlite:///{DB_PATH}"

# CoinGecko API configuration
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
COINGECKO_TIMEOUT = 10  # secondes

# Ensure data directories exist before first use
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)
