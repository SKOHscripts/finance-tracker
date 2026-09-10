"""App configuration"""
from pathlib import Path

# Project root is two levels up from this config file (config/ subdirectory)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "finance.db"
REPORTS_DIR = DATA_DIR / "reports"
DOCS_DIR = PROJECT_ROOT / "docs"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
CONFIG_DIR = PROJECT_ROOT / "config"

# Signal thresholds. Rules only: the portfolio lives in the database, which
# is what lets this file be public.
SIGNAL_RULES_PATH = CONFIG_DIR / "signal_rules.toml"

# SQLite URL format for SQLAlchemy
DATABASE_URL = f"sqlite:///{DB_PATH}"

# CoinGecko API configuration
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
COINGECKO_TIMEOUT = 10  # secondes

# Block explorers used by the wallet importer. Each is optional: a wallet is
# only ever queried once the user turns its sync on.
# Etherscan V2 serves every supported EVM chain from one host, keyed by chainid.
ETHERSCAN_API_URL = "https://api.etherscan.io/v2/api"
MEMPOOL_API_URL = "https://mempool.space/api"
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
WALLET_HTTP_TIMEOUT = 20  # secondes

# Ensure data directories exist before first use
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)
