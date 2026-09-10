"""English UI strings."""

STRINGS: dict[str, str] = {
    # ── Navigation ─────────────────────────────────────────────────────────────
    "nav.documentation": "📖 Documentation",
    "nav.dashboard": "📊 Dashboard",
    "nav.simulation": "🔮 Long-Term Simulation",
    "nav.products": "🏷️ My Products",
    "nav.transactions": "💸 My Transactions",
    "nav.valuations": "📈 My Valuations",
    "nav.bitcoin": "₿ Bitcoin Space",

    # ── App / Sidebar ───────────────────────────────────────────────────────────
    "app.lang_selector": "🌐 Language / Langue",
    "app.db_section": "Data Management",
    "app.import_label": "Import your backup (.db)",
    "app.create_portfolio_btn": "Create a new portfolio",
    "app.db_loaded_msg": "Database loaded!",
    "app.db_init_with_products": "✅ Database initialised with {n} default products",
    "app.db_init": "✅ Database initialised",
    "app.export_btn": "📥 Save database (PC)",
    "app.sidebar_hint": "Open menu",
    "app.nav_label": "Navigation",
    "app.doc_link_btn": "📖 Documentation (README)",
    "app.donate_btn": "☕ Buy me a Bitcoffee",
    "app.sidebar_version": "Finance Tracker v1.1.0",
    "app.sidebar_description": "Portfolio tracking tool: SCPI, Bitcoin, savings, crypto and a rotation signal. Educational tool, not investment advice.",

    # ── Dashboard ───────────────────────────────────────────────────────────────
    "dashboard.title": "Dashboard",
    "dashboard.caption": "Global overview and performance of your investment portfolio.",
    "dashboard.load_error": "Unable to load portfolio: {e}",
    "dashboard.section_overview": "Overview",
    "dashboard.metric_total_value": "Total Value",
    "dashboard.metric_total_invested": "Total Invested",
    "dashboard.metric_gains": "Gains",
    "dashboard.metric_cash": "Available Cash",
    "dashboard.section_allocation": "Portfolio Allocation",
    "dashboard.empty_portfolio": "Your portfolio is empty. Add valuations in the corresponding tab.",
    "dashboard.section_detail": "Per-product detail",
    "dashboard.section_exports": "Exports & Reports",
    "dashboard.prepare_pdf": "Prepare PDF report",
    "dashboard.generating_pdf": "⏳ Generating PDF report...",
    "dashboard.download_pdf": "⬇️ Download PDF",
    "dashboard.pdf_filename": "portfolio_report.pdf",
    "dashboard.prepare_json": "Prepare JSON export",
    "dashboard.generating_json": "⏳ Structuring data...",
    "dashboard.download_json": "⬇️ Download JSON",
    "dashboard.json_filename": "dashboard_data.json",
    "dashboard.refresh_exports": "Refresh export data",
    "dashboard.error": "❌ Error: {e}",
    # Bitcoin expander
    "dashboard.btc_refresh_btn": "Refresh price",
    "dashboard.btc_connecting": "Connecting to APIs...",
    "dashboard.btc_offline": "**Offline** — Network unreachable. Enter the price manually below.",
    "dashboard.btc_metric_value": "Current value",
    "dashboard.btc_metric_qty": "Quantity",
    "dashboard.btc_metric_pru": "Avg. cost",
    "dashboard.btc_metric_pnl": "Unrealised P&L",
    "dashboard.btc_price_history": "Price history (snapshots)",
    "dashboard.btc_new_snapshot": "New Snapshot",
    "dashboard.btc_date_label": "Date",
    "dashboard.btc_full_price_label": "Price of one full BTC (EUR)",
    "dashboard.btc_qty_label": "Quantity (in Satoshis)",
    "dashboard.btc_qty_help": "1 BTC = 100,000,000 Sats",
    "dashboard.btc_computed_value": "Computed value: **{v}**",
    "dashboard.btc_save_snapshot": "Save snapshot",
    "dashboard.btc_qty_error": "Quantity (in sats) and price must both be > 0.",
    "dashboard.btc_snapshot_saved": "✅ Snapshot saved — Value: {v}",
    "dashboard.btc_error": "❌ Error: {e}",
    # Table columns
    "dashboard.col_date": "Date",
    "dashboard.col_btc_price": "BTC Price (€)",
    "dashboard.col_sats": "Satoshis",
    "dashboard.col_total_value": "Total value (€)",
    # Allocation chart
    "dashboard.chart_weight_pct": "Weight (%)",
    "dashboard.chart_product": "Product",

    # ── Simulation ─────────────────────────────────────────────────────────────
    "simulation.title": "Long-Term Simulation",
    "simulation.no_product_warning": "Add at least one product in 'Add Products' before running a simulation.",
    "simulation.section_global_params": "Global parameters",
    "simulation.param_duration": "Duration (years)",
    "simulation.param_income": "Gross annual income Y (€)",
    "simulation.param_income_growth": "Income growth / year (%)",
    "simulation.param_living_costs": "Annual living costs (€)",
    "simulation.param_initial_tax": "Tax due Y-1 payable in year 1 (€)",
    "simulation.section_tax": "Taxation (progressive brackets)",
    "simulation.tax_caption": "Annual brackets — leave `up_to` empty for the last bracket.",
    "simulation.std_deduction": "Standard deduction (%)",
    "simulation.section_per": "PER — Deductible cap",
    "simulation.per_rate": "% of prior-year income",
    "simulation.per_min": "Minimum PER cap (€/year)",
    "simulation.per_max": "Maximum PER cap (€/year, 0 = unlimited)",
    "simulation.section_product_params": "Per-product parameters",
    "simulation.product_params_caption": "Only relevant parameters are shown based on the category defined above.",
    "simulation.scpi_caption": "For a SCPI, contributions are defined via **'Shares bought / year'** below.",
    "simulation.cash_required_error": "⚠️ At least one product of category 'cash' is required.",
    "simulation.submit_hint": "Submit the form to run the simulation.",
    "simulation.section_summary": "Final summary",
    "simulation.metric_final_value": "Final value",
    "simulation.metric_real_value": "Real value (inflation-adjusted)",
    "simulation.metric_invested": "Total invested (excl. cash)",
    "simulation.metric_tax_due": "Tax due Y payable in Y+1",
    "simulation.section_tables": "Data tables",
    "simulation.tab_by_period": "By period",
    "simulation.tab_by_product": "By product (long)",
    "simulation.section_charts": "Charts",
    "simulation.section_exports": "Exports",
    "simulation.prepare_pdf": "Prepare PDF report",
    "simulation.section_inflation": "Inflation profile",
    "simulation.section_categories": "Product categories",
    "simulation.pdf_error": "Error generating PDF: {e}",

    # ── Products ────────────────────────────────────────────────────────────────
    "products.title": "My Products",
    "products.caption": "Create, edit and delete your products. (Deletion may fail if transactions/valuations exist.)",
    "products.add_expander": "Add a product",
    "products.field_name": "Name *",
    "products.field_type": "Type",
    "products.field_unit": "Unit",
    "products.field_risk": "Risk level (optional)",
    "products.field_description": "Description",
    "products.field_fees": "Fees",
    "products.field_tax": "Taxation",
    "products.create_btn": "Create",
    "products.name_required": "Name is required.",
    "products.name_duplicate": "A product named '{name}' already exists.",
    "products.created_success": "✅ Product created.",
    "products.error": "❌ Error: {e}",
    "products.empty": "No products yet.",
    "products.list_title": "Products (editable)",
    "products.col_id": "ID",
    "products.col_name": "Name",
    "products.col_type": "Type",
    "products.col_unit": "Unit",
    "products.col_risk": "Risk",
    "products.col_description": "Description",
    "products.col_fees": "Fees",
    "products.col_tax": "Taxation",
    "products.col_created_at": "Created",
    "products.col_delete": "🗑️ Delete",
    "products.advanced_delete_expander": "Deletion tools (advanced)",
    "products.advanced_delete_help": "If product deletion fails, delete associated transactions/valuations first.",
    "products.advanced_delete_tip": "Tip: use the Transactions page or the Dashboard (product detail) to delete associated valuations.",
    "products.apply_btn": "Apply changes",
    "products.name_empty_error": "All products (not deleted) must have a name.",
    "products.name_unique_error": "Product names must be unique (at least among non-deleted rows).",
    "products.applied_success": "✅ Changes applied.",
    "products.reload_btn": "Reload from DB",

    # ── Transactions ────────────────────────────────────────────────────────────
    "transactions.title": "My Transactions",
    "transactions.caption": "Add, edit and delete directly from the list.",
    "transactions.no_products": "No products. Create a product first before adding transactions.",
    "transactions.add_expander": "Add a transaction",
    "transactions.field_product": "Product",
    "transactions.field_type": "Type",
    "transactions.field_date": "Date",
    "transactions.field_amount": "Amount EUR (optional)",
    "transactions.field_qty_sats": "Quantity (in Satoshis)",
    "transactions.field_qty_units": "Quantity (Shares / Units)",
    "transactions.field_qty_help_btc": "Reminder: 1 BTC = 100,000,000 Sats",
    "transactions.field_note": "Note",
    "transactions.add_btn": "Add",
    "transactions.added_success": "✅ Transaction added.",
    "transactions.error": "❌ Error: {e}",
    "transactions.filter_product": "Filter product",
    "transactions.filter_type": "Filter type",
    "transactions.filter_all": "All",
    "transactions.sort_label": "Sort",
    "transactions.sort_date_desc": "Date descending",
    "transactions.sort_date_asc": "Date ascending",
    "transactions.sort_id_desc": "ID descending",
    "transactions.empty_filter": "No transactions for this filter.",
    "transactions.list_title": "History (editable)",
    "transactions.btc_qty_info": "ℹ️ Bitcoin quantities are displayed and stored in **Satoshis** (integers). Other products use standard units.",
    "transactions.col_id": "ID",
    "transactions.col_date": "Date",
    "transactions.col_product": "Product",
    "transactions.col_type": "Type",
    "transactions.col_amount": "Amount EUR",
    "transactions.col_qty": "Quantity (Sats or Units)",
    "transactions.col_note": "Note",
    "transactions.col_delete": "🗑️ Delete",
    "transactions.apply_btn": "Apply changes",
    "transactions.invalid_product": "Invalid product: {name}",
    "transactions.applied_success": "✅ Changes applied.",
    "transactions.reload_btn": "Reload from DB",

    # ── Valuations ──────────────────────────────────────────────────────────────
    "valuations.title": "My Valuations",
    "valuations.caption": "Value snapshots: add, edit and delete from a single table.",
    "valuations.no_products": "No products. Create a product before adding valuations.",
    "valuations.add_expander": "Add a valuation",
    "valuations.field_product": "Product",
    "valuations.field_date": "Date",
    "valuations.field_total": "Total value EUR",
    "valuations.field_unit_price_btc": "Price of one full BTC (EUR)",
    "valuations.field_unit_price": "Unit price (EUR, optional)",
    "valuations.add_btn": "Add",
    "valuations.total_positive_error": "Total value must be > 0.",
    "valuations.added_success": "✅ Valuation added.",
    "valuations.error": "❌ Error: {e}",
    "valuations.filter_product": "Filter product",
    "valuations.filter_all": "All",
    "valuations.sort_label": "Sort",
    "valuations.sort_date_desc": "Date descending",
    "valuations.sort_date_asc": "Date ascending",
    "valuations.sort_id_desc": "ID descending",
    "valuations.empty_filter": "No valuations for this filter.",
    "valuations.list_title": "History (editable)",
    "valuations.col_id": "ID",
    "valuations.col_date": "Date",
    "valuations.col_product": "Product",
    "valuations.col_total": "Total value EUR",
    "valuations.col_unit_price": "Unit price EUR",
    "valuations.col_delete": "🗑️ Delete",
    "valuations.apply_btn": "Apply changes",
    "valuations.invalid_product": "Invalid product: {name}",
    "valuations.total_positive_update_error": "Total value must be > 0.",
    "valuations.applied_success": "✅ Changes applied.",
    "valuations.reload_btn": "Reload from DB",

    # ── Bitcoin ─────────────────────────────────────────────────────────────────
    "bitcoin.title": "₿ Bitcoin Space",
    "bitcoin.redirect_info": (
        "**This page has been merged into the Dashboard.**\n\n"
        "All Bitcoin features are now available from "
        "**📊 Dashboard → Per-product detail → Bitcoin**:\n\n"
        "- Live BTC/EUR price with LIVE / OFFLINE badge\n"
        "- Quantity in Satoshis\n"
        "- Avg. cost and unrealised P&L\n"
        "- Price history (snapshots)\n"
        "- New snapshot form\n"
        "- Recent snapshots table"
    ),
    "bitcoin.redirect_link": "Head to **📊 Dashboard** to access your Bitcoin space.",

    # ── Documentation ───────────────────────────────────────────────────────────
    "documentation.title": "Documentation",
    "documentation.subtitle": "Complete guide to using and understanding Finance Tracker",
    "documentation.tab_home": "Home",
    "documentation.tab_concepts": "Concepts",
    "documentation.tab_calculs": "Calculations",
    "documentation.tab_interface": "Web Interface",
    "documentation.tab_database": "Database",
    "documentation.tab_install": "Installation",
    "documentation.tab_help": "Help",
    # Home tab
    "documentation.home_title": "Welcome to Finance Tracker",
    "documentation.home_intro": (
        "**Finance Tracker** is a comprehensive investment portfolio management application,\n"
        "designed for privacy-conscious investors."
    ),
    "documentation.home_features_title": "Key Features",
    "documentation.home_feature_tracking": "**📊 Complete Tracking**\n- Multi-asset portfolio\n- SCPI, Bitcoin, Savings\n- Life insurance, PER",
    "documentation.home_feature_analysis": "**📈 Advanced Analytics**\n- MWRR performance\n- Compound interest\n- Long-term projections",
    "documentation.home_feature_privacy": "**🔒 Privacy**\n- Local data only\n- No cloud required\n- Easy export/import",
    "documentation.home_quickstart_title": "Quick Start",
    "documentation.home_quickstart_table": (
        "| Step | Action | Page |\n"
        "|------|--------|------|\n"
        "| 1 | Create your products | 🏷️ **My Products** |\n"
        "| 2 | Add transactions | 💸 **My Transactions** |\n"
        "| 3 | Update valuations & view performance | 📊 **Dashboard** |"
    ),
    "documentation.home_explore_title": "Explore the Documentation",
    "documentation.home_explore_text": "Use the **tabs above** to access the different documentation sections.",
    "documentation.home_tip": (
        "**Tip:** Start with the **Concepts** tab to understand the 3 pillars\n"
        "of the system (Products, Transactions, Valuations) before using the app."
    ),
    # Concepts tab
    "documentation.concepts_title": "Fundamental Concepts",
    "documentation.concepts_intro": (
        "Finance Tracker is built on **three essential pillars**. Understanding these concepts\n"
        "is the key to using the application effectively."
    ),
    "documentation.concepts_products_title": "1. Products",
    "documentation.concepts_transactions_title": "2. Transactions (Movements)",
    "documentation.concepts_valuations_title": "3. Valuations (Snapshots)",
    "documentation.full_doc_link": "**[Read full documentation: {title}]({url})**",
    "documentation.expand_full_doc": "View full document",
    # Calculs tab
    "documentation.calculs_title": "Formulas & Calculations",
    "documentation.calculs_intro": (
        "All the mathematical formulas used by Finance Tracker to compute\n"
        "performance, gains and projections."
    ),
    "documentation.calculs_key_metrics": "Key Indicators",
    "documentation.calculs_compound": "Compound Interest",
    "documentation.calculs_bitcoin_title": "₿ Special Case: Bitcoin",
    # Inflation tab
    "documentation.tab_inflation": "Inflation",
    "documentation.inflation_title": "📊 Configurable Inflation",
    "documentation.inflation_intro": (
        "The long-term simulator offers four predefined inflation profiles, "
        "plus a custom option."
    ),
    "documentation.inflation_profiles_title": "Inflation Profiles",
    "documentation.inflation_how_title": "How it works?",
    "documentation.inflation_how": (
        "In the simulator, replaces the simple *Annual Inflation (%)* field with a profile "
        "selector. The corresponding rate is automatically applied to all projections "
        "and appears in the exported PDF report."
    ),
    "documentation.inflation_sources": (
        "**Sources:** INSEE IPC long-term series, "
        "rent reference indices ([IRL — ANIL](https://www.anil.org/outils/indices-et-plafonds/tableau-de-lirl/)) "
        "and [IGEDD/Friggit](https://www.cgedd.fr/prix-immobilier-friggit.pdf) work on real estate price evolution."
    ),
    # Interface tab
    "documentation.interface_title": "Web Interface Guide",
    "documentation.interface_intro": "Complete page-by-page guide to the Streamlit interface.",
    "documentation.interface_architecture": "Application Architecture",
    "documentation.interface_workflow": "Recommended Workflow",
    "documentation.interface_tx_types": "Transaction Types",
    # Installation tab
    "documentation.install_title": "Installation & Development",
    "documentation.install_intro": "Guides for installing, configuring and contributing to the project.",
    "documentation.install_quickstart": "Quick Start (Developer)",
    "documentation.install_architecture": "Project Architecture",
    "documentation.install_dev_docs": "Developer Documentation",
    # Database tab
    "documentation.database_title": "Database Structure",
    "documentation.database_intro": (
        "Finance Tracker uses **SQLite** with **SQLModel** for data persistence."
    ),
    "documentation.database_tables": "Main Tables",
    "documentation.database_relations": "Relations",
    # Help tab
    "documentation.help_title": "Help & Support",
    "documentation.help_faq_title": "FAQ",
    "documentation.help_resources_title": "Resources",
    "documentation.help_resources_official": "**Official Links**",
    "documentation.help_resources_web": "[Web Application](https://finance-tracker-skohscripts.streamlit.app/)",
    "documentation.help_resources_github": "[GitHub](https://github.com/SKOHscripts/finance-tracker)",
    "documentation.help_resources_support": "**Support**",
    "documentation.help_resources_bug": "[Report a bug](https://github.com/SKOHscripts/finance-tracker/issues)",
    "documentation.help_resources_feature": "[Suggest a feature](https://github.com/SKOHscripts/finance-tracker/discussions)",
    "documentation.help_resources_docs": "**Documentation**",
    "documentation.help_resources_readme": "[Full README]({url}/README.md)",
    "documentation.help_resources_roadmap": "[Roadmap]({url}/ROADMAP.md)",
    "documentation.help_tips_title": "Usage Tips",
    "documentation.help_tips": (
        "**Tip #1:** Start by reading **Concepts** to understand the 3 pillars of the system.\n\n"
        "**Tip #2:** Update your valuations regularly from the **📊 Dashboard** (monthly minimum).\n\n"
        "**Tip #3:** Use the **🔮 Simulator** to plan your future investments.\n\n"
        "**Tip #4:** Back up your database regularly via the sidebar."
    ),
    "documentation.card_read_more": "Read full documentation →",
    "documentation.file_not_found": "⚠️ File {filename} not found.",
    "documentation.file_load_error": "❌ Error loading file: {error}",

    # ── Disclaimer ──────────────────────────────────────────────────────────────
    "disclaimer.title": "⚠️ This is not investment advice",
    "disclaimer.body": (
        "This tool is educational. It is not an investment adviser, not a financial "
        "intermediary, and is not registered with any market authority. What it shows "
        "describes what has already happened in the market: nothing here predicts a price. "
        "Crypto-assets are extremely volatile and you can lose everything you put in. "
        "The tool executes nothing: deciding and acting remain entirely yours."
    ),
    "disclaimer.compact": (
        "Parameters to carry out by hand, not a recommendation. Educational tool, "
        "no investment advice."
    ),
    "disclaimer.more_title": "📄 Scope and limits of this tool",
    "disclaimer.long": (
        "**What it does.** It applies rules written in advance to retrospective metrics — "
        "past returns, observed volatility, decline from a peak. When every barrier of a "
        "mechanism passes, it proposes a move and works out its parameters.\n\n"
        "**What it does not.** It predicts no price, and knows nothing of your situation, "
        "goals, horizon or risk tolerance. It executes nothing, holds no key, signs no "
        "transaction.\n\n"
        "**Limits you need to know.**\n\n"
        "- The metrics describe the past. An asset that held up well can collapse the day "
        "after the scan.\n"
        "- The thresholds are choices, not truths. They live in `config/signal_rules.toml` "
        "and you can change them.\n"
        "- A cost basis reconstructed from a blockchain is an estimate. A chain records "
        "movements, never a purchase price.\n"
        "- Swap costs are estimated from averages. Your actual quote may differ "
        "substantially.\n\n"
        "**Tax.** A swap is generally a taxable event. This tool computes no tax and produces "
        "no tax document.\n\n"
        "**Plainly:** if you follow a proposal from this tool, it is your decision and your "
        "risk."
    ),

    # ── Verdicts ────────────────────────────────────────────────────────────────
    "verdict.conserver": "Hold",
    "verdict.temporiser": "Wait it out",
    "verdict.rotation": "Rotate",
    "verdict.alleger": "Take profit",
    "verdict.sortie_stop": "Stop exit",

    # ── Gates ───────────────────────────────────────────────────────────────────
    "gate.ecart_de_score": "Score gap",
    "gate.avantage_momentum_vs_cout": "Momentum edge vs cost",
    "gate.volatilite_candidat": "Candidate volatility",
    "gate.drawdown_candidat": "Candidate drawdown",
    "gate.liquidite_candidat": "Candidate liquidity",
    "gate.regime_favorable": "Market regime",
    "gate.persistance": "Persistence",
    "gate.position_en_gain": "Position in profit",
    "gate.repli_depuis_le_haut": "Pullback from the high",
    "gate.plus_value": "Latent gain",
    "gate.montant_vendu_suffisant": "Proceeds large enough",
    "gate.jamais_pris": "Stake never recovered",
    "gate.momentum_actif_detenu": "Held asset momentum",
    "gate.drawdown_actif_detenu": "Held asset drawdown",
    "gate.regime_marche": "Market degraded",
    "gate.baisse_vs_cout": "Decline vs exit cost",
    "gate.liquidite_refuge": "Refuge liquidity",

    # ── Cost basis confidence ───────────────────────────────────────────────────
    "confidence.high": "high",
    "confidence.medium": "medium",
    "confidence.low": "low",
    "confidence.none": "none",

    # ── Crypto signal ───────────────────────────────────────────────────────────
    "signal.title": "📡 Crypto Signal",
    "signal.caption": (
        "Arbitrates your crypto positions against the market ranking, one position at a "
        "time, on rules written in advance."
    ),
    "signal.rules_error": "❌ Invalid rules configuration: {e}",
    "signal.section_inputs": "What will be arbitrated",
    "signal.inputs_help": (
        "Check these figures before running a scan: a verdict is only worth as much as its "
        "inputs."
    ),
    "signal.no_positions": (
        "No crypto position. Add a wallet to watch, or map an existing product to a market "
        "identifier from the Wallets page."
    ),
    "signal.col_asset": "Asset",
    "signal.col_units": "Units",
    "signal.col_units_source": "Units from",
    "signal.col_cost_basis": "Invested capital",
    "signal.col_cost_source": "Basis from",
    "signal.col_reserve": "Fee reserve",
    "signal.col_arbitrated": "Arbitrated",
    "signal.col_value": "Value",
    "signal.col_gain": "Gain",
    "signal.col_cost_of_move": "Round-trip cost",
    "signal.cost_of_move_help": (
        "Two spreads, two commissions and chain fees, against the size of the line. "
        "A small line carries them less well."
    ),
    "signal.missing_cost_basis": (
        "Invested capital unknown on: {assets}. The trailing stop and profit taking stay "
        "inactive on those lines."
    ),
    "signal.source_wallet": "chain",
    "signal.source_transactions": "transactions",
    "signal.source_manual": "corrected",
    "signal.source_onchain": "estimated (chain)",
    "signal.source_valuation": "valuation",
    "signal.source_none": "—",
    "signal.run_btn": "🔍 Run a scan",
    "signal.persist_opt": "Record this scan in the history",
    "signal.persist_help": (
        "The persistence gates count consecutive scans. An unrecorded scan advances no "
        "streak."
    ),
    "signal.scanning": "Scanning…",
    "signal.scan_error": "❌ Scan failed: {e}",
    "signal.scan_done": "✅ Scan complete — overall verdict: {verdict}",
    "signal.section_market": "Market state",
    "signal.regime": "Regime",
    "signal.regime_reference": "{symbol} > {days}d average",
    "signal.regime_breadth": "Ranking breadth",
    "signal.candidate_line": "**Candidate:** {symbol} — {name} (score {score})",
    "signal.no_candidate": "No candidate: every ranked asset is already held.",
    "signal.discarded_title": "Higher-ranked candidates skipped",
    "signal.discarded_help": (
        "The engine walks down the ranking to the first asset clearing volatility, drawdown "
        "and volume. These are the ones it skipped, and why."
    ),
    "signal.insufficient_history": "History too short to score reliably: {assets}.",
    "signal.section_positions": "Verdict per position",
    "signal.not_arbitrated": "This line was not arbitrated.",
    "signal.not_evaluated": "Mechanism not evaluated in this scan.",
    "signal.mech_rotation": "Rotation",
    "signal.mech_stop": "Trailing stop",
    "signal.mech_profit": "Profit taking",
    "signal.mech_temporisation": "Wait it out",
    "signal.gate": "Barrier",
    "signal.gate_status": "State",
    "signal.gate_value": "Measured",
    "signal.gate_threshold": "Threshold",
    "signal.gate_unit": "Unit",
    "signal.plan_title": "Swap plan",
    "signal.plan_from": "From",
    "signal.plan_to": "To",
    "signal.plan_amount": "Amount",
    "signal.plan_units": "Units at reference price",
    "signal.plan_min_units": "Minimum acceptable",
    "signal.plan_min_units_help": (
        "Below this many units the quote no longer matches what the scan measured: that is "
        "the point to call it off. Margin used: {pct} %."
    ),
    "signal.plan_quotes": "Providers to compare:",
    "signal.ranking_title": "Full ranking",
    "signal.col_score": "Score",
    "signal.col_mom_slow": "Slow momentum",
    "signal.col_mom_fast": "Fast momentum",
    "signal.col_vol": "30d volatility",
    "signal.col_dd": "90d drawdown",
    "signal.section_last": "Last recorded scan",
    "signal.last_scan": "Scan of {date} — overall verdict: {verdict}",
    "signal.col_verdict": "Verdict",
    "signal.col_streak": "Streak",
    "signal.col_date": "Date",
    "signal.col_candidate": "Candidate",
    "signal.history_title": "Scan history",
    "signal.history_help": (
        "This series feeds the persistence gates: a move only fires if the conditions hold "
        "for several consecutive scans."
    ),
    "signal.never_scanned": "No scan recorded yet. Run one to get a first verdict.",

    # ── Watched wallets ─────────────────────────────────────────────────────────
    "wallets.title": "👛 Crypto Wallets",
    "wallets.caption": (
        "Add a public address: the tool reads balances, reconstructs a cost basis where the "
        "chain allows it, and feeds the signal."
    ),
    "wallets.settings_title": "⚙️ API keys and endpoints",
    "wallets.settings_help": (
        "All optional except for EVM chains. Nothing ships with the app: everyone brings "
        "their own quota."
    ),
    "wallets.key_storage_warning": (
        "These keys are stored in your database. They travel with the file when you export "
        "it: do not share a backup that contains them."
    ),
    "wallets.etherscan_key": "EVM explorer key",
    "wallets.etherscan_help": (
        "Free from etherscan.io. One key covers Ethereum, Base, Arbitrum, Optimism, Polygon "
        "and BSC."
    ),
    "wallets.coingecko_key": "CoinGecko key (optional)",
    "wallets.coingecko_help": "Without a key, the free tier is enough for a weekly scan.",
    "wallets.mempool_url": "Bitcoin indexer",
    "wallets.mempool_help": (
        "Leave blank for mempool.space. Point it at your own node if you would rather not "
        "expose your addresses to a third party."
    ),
    "wallets.solana_url": "Solana RPC node",
    "wallets.solana_help": "Leave blank for the public endpoint, which rate-limits heavily.",
    "wallets.save_settings": "Save",
    "wallets.settings_saved": "✅ Settings saved",
    "wallets.add_title": "Add a wallet",
    "wallets.privacy_notice": (
        "Querying an indexer reveals this address to whoever runs it. Syncing can be turned "
        "on and off per wallet, and an address saved without syncing is never sent "
        "anywhere.\n\n"
        "**Monero cannot be read** from an address alone: that is the point of the protocol. "
        "Those positions are entered by hand."
    ),
    "wallets.field_label": "Name",
    "wallets.field_chain": "Chain",
    "wallets.field_address": "Public address",
    "wallets.field_derive": "Reconstruct the cost basis",
    "wallets.derive_help": (
        "Fetches transfer history and prices it at the rate on the day of each movement. "
        "Slower, and impossible on Solana."
    ),
    "wallets.field_autosync": "Allow syncing",
    "wallets.autosync_help": (
        "Unchecked, the address is kept but never sent to an indexer."
    ),
    "wallets.add_btn": "Add",
    "wallets.address_required": "The address is required.",
    "wallets.duplicate": "This address is already watched on this chain.",
    "wallets.added": "✅ Wallet added",
    "wallets.empty": (
        "No wallet watched. Add one, or keep entering positions by hand from the Products "
        "page."
    ),
    "wallets.section_wallets": "Watched wallets",
    "wallets.col_label": "Name",
    "wallets.col_chain": "Chain",
    "wallets.col_address": "Address",
    "wallets.col_sync": "Sync",
    "wallets.col_last": "Last sync",
    "wallets.col_error": "Last issue",
    "wallets.manage_title": "Manage wallets",
    "wallets.toggle_sync": "Sync",
    "wallets.delete": "Delete",
    "wallets.sync_btn": "🔄 Sync",
    "wallets.basis_btn": "💶 Recompute cost bases",
    "wallets.sync_ok": "✅ {label}: {balances} balance(s), {transfers} movement(s) added",
    "wallets.sync_failed": "❌ {label}: {error}",
    "wallets.basis_done": "✅ {n} cost basis recomputed",
    "wallets.basis_nothing": "No product is fed by a watched wallet.",
    "wallets.section_holdings": "Discovered balances",
    "wallets.no_holdings": "Nothing discovered yet. Run a sync.",
    "wallets.col_asset": "Asset",
    "wallets.col_units": "Units",
    "wallets.col_listing": "Listing",
    "wallets.col_product": "Product",
    "wallets.unlisted_note": (
        "Unlisted, so neither priceable nor arbitrable: {assets}. That is the normal case "
        "for an airdropped token that trades nowhere."
    ),
    "wallets.map_title": "Map balances to products",
    "wallets.map_help": (
        "A balance mapped to a product feeds its units and its cost basis. A mapping "
        "survives later syncs."
    ),
    "wallets.map_to": "Map to",
    "wallets.map_none": "— unmapped —",
    "wallets.create_product": "Create",
    "wallets.product_created": "✅ Product “{name}” created and mapped",
    "wallets.ignore": "Ignore",
    "wallets.section_basis": "Cost basis",
    "wallets.no_basis": (
        "No cost basis reconstructed. Map a balance to a product, then recompute."
    ),
    "wallets.basis_estimate_warning": (
        "These amounts are **estimates**. A blockchain records movements, never a purchase "
        "price: a token received from a swap is priced at the rate on the day, and a transfer "
        "from one of your own unwatched wallets counts as a purchase. Correct them by hand as "
        "soon as you know your real price."
    ),
    "wallets.col_unit_cost": "Unit cost",
    "wallets.col_total": "Total capital",
    "wallets.col_confidence": "Confidence",
    "wallets.col_uncovered": "Unexplained units",
    "wallets.override_title": "Correct a cost basis",
    "wallets.override_help": (
        "Your figure replaces the estimate everywhere, including in the signal engine. "
        "Clear the field to fall back to the reconstructed value."
    ),
    "wallets.override_field": "Unit price",
    "wallets.override_placeholder": "e.g. 1250.50",
    "wallets.override_save": "Save",
    "wallets.override_invalid": "Amount could not be read.",
    "wallets.override_saved": "✅ Cost basis of “{name}” updated",

    # ── Manually declared asset (no address) ────────────────────────────────────
    "wallets.manual_title": "Add an asset without an address",
    "wallets.manual_help": (
        "For a holding no address can reveal: Monero, whose balance cannot be read "
        "without its view key, an exchange balance, or an asset you would rather "
        "not expose to an indexer. Units and cost basis are recorded as a purchase, "
        "so they stay editable in the Transactions page like any other product."
        ),
    "wallets.manual_search": "Search for the listing",
    "wallets.manual_search_placeholder": "e.g. monero, or XMR",
    "wallets.manual_search_btn": "🔍 Search",
    "wallets.manual_query_required": "Type a name or a symbol to search for.",
    "wallets.manual_search_failed": "Search failed: {error}",
    "wallets.manual_no_hit": (
        "No listing matches. Try the full name rather than the ticker."
        ),
    "wallets.manual_listing": "Listing",
    "wallets.manual_name": "Product name",
    "wallets.manual_name_help": "As it will appear throughout the app. Must be unique.",
    "wallets.manual_units": "Units held",
    "wallets.manual_units_placeholder": "e.g. 12.5",
    "wallets.manual_units_help": (
        "In the asset's native units (XMR, BTC, ETH…), not satoshis or wei. "
        "Leave empty to create the line and enter your purchases afterwards."
        ),
    "wallets.manual_units_invalid": "Unreadable quantity.",
    "wallets.manual_date": "Position date",
    "wallets.manual_cost_mode": "Cost basis given as",
    "wallets.manual_cost_unit": "Unit price",
    "wallets.manual_cost_total": "Total invested",
    "wallets.manual_cost": "Amount (€)",
    "wallets.manual_cost_placeholder": "e.g. 142.30",
    "wallets.manual_cost_help": (
        "Leave empty if the asset has no purchase price — an airdrop, mining. "
        "The engine then treats the cost basis as unknown and disables the trailing "
        "stop on that line, rather than reading the absence as a total gain."
        ),
    "wallets.manual_cost_invalid": "Unreadable amount.",
    "wallets.manual_reserve": "Fee reserve (€)",
    "wallets.manual_reserve_help": (
        "Share never proposed for a swap, for an asset that also pays chain fees."
        ),
    "wallets.manual_reserve_invalid": "Unreadable reserve.",
    "wallets.manual_arbitrated": "Arbitrate this line",
    "wallets.manual_arbitrated_help": (
        "Unchecked, the asset stays tracked and displayed but the engine proposes "
        "no move on it."
        ),
    "wallets.manual_add_btn": "Add the asset",
    "wallets.manual_added": "✅ “{name}” added and mapped to listing {listing}",

    # ── Navigation and database ─────────────────────────────────────────────────
    "nav.crypto_signal": "📡 Crypto Signal",
    "nav.crypto_wallets": "👛 Crypto Wallets",
    "app.db_migrated": (
        "🔄 Database updated: {n} migration(s) applied (schema v{old} → v{new})"
    ),
    "app.db_migrate_error": (
        "❌ Migration failed: {e}. Export your database before doing anything else."
    ),

    # ── Rotation parameters ─────────────────────────────────────────────────
    "section.universe": "Universe",
    "sectionhelp.universe": (
        "What the ranking looks at, and how fast it may ask."
        ),
    "section.signal": "Composite score",
    "sectionhelp.signal": (
        "How an asset is scored, before any barrier applies."
        ),
    "section.costs": "Cost of a move",
    "sectionhelp.costs": (
        "What a swap really costs — the figure the advantage has to beat."
        ),
    "section.gates": "Rotation barriers",
    "sectionhelp.gates": (
        "The six conditions that must all pass for a rotation to be proposed."
        ),
    "section.regime": "Market regime",
    "sectionhelp.regime": (
        "The market's observed state. A description, never a forecast."
        ),
    "section.temporisation": "Wait in a refuge",
    "sectionhelp.temporisation": (
        "Leaving for a stablecoin to wait, when no rotation passes and the regime is degraded."
        ),
    "section.profit_taking": "Profit taking",
    "sectionhelp.profit_taking": (
        "Recover the stake once, then let the rest run."
        ),
    "section.trailing_stop": "Trailing stop",
    "sectionhelp.trailing_stop": (
        "Full exit when a winning line gives back too much of its peak."
        ),

    "param.universe.top_n": "Ranking depth",
    "paramhelp.universe.top_n": (
        "How many assets the ranking looks at, by market capitalisation. Higher opens the field to less liquid lines; lower keeps it on the more established ones."
        ),
    "param.universe.request_delay_seconds": "Delay between calls",
    "paramhelp.universe.request_delay_seconds": (
        "Wait between two CoinGecko calls. The free plan drops bursts, so going too low makes the scan fail rather than run faster."
        ),
    "param.signal.fast_window_days": "Fast window",
    "paramhelp.signal.fast_window_days": (
        "Short momentum window. It catches recent movement, so it reacts quickly and is wrong more often."
        ),
    "param.signal.slow_window_days": "Slow window",
    "paramhelp.signal.slow_window_days": (
        "Long momentum window, the underlying trend. It must stay strictly longer than the fast window, or the score counts the same measurement twice."
        ),
    "param.signal.weight_slow_momentum": "Weight of the underlying trend",
    "paramhelp.signal.weight_slow_momentum": (
        "Weight of the underlying trend in the composite score. The dominant term by default."
        ),
    "param.signal.weight_fast_momentum": "Weight of recent movement",
    "paramhelp.signal.weight_fast_momentum": (
        "Weight of recent movement. Raising it makes the ranking twitchier, and rotations more frequent."
        ),
    "param.signal.weight_volatility": "Weight of the volatility penalty",
    "paramhelp.signal.weight_volatility": (
        "Weight of the volatility penalty, subtracted from the score. At equal momentum, it separates the asset that got there more calmly."
        ),
    "param.costs.swap_spread_pct": "Spread per leg",
    "paramhelp.costs.swap_spread_pct": (
        "Observed gap between the quoted price and the price obtained, per swap leg. It counts towards the cost the advantage has to beat."
        ),
    "param.costs.provider_fee_pct": "Provider fee per leg",
    "paramhelp.costs.provider_fee_pct": (
        "Fee the provider advertises, per swap leg. Adds to the spread."
        ),
    "param.costs.network_fees_total": "Chain fees, round trip",
    "paramhelp.costs.network_fees_total": (
        "Chain fees for a round trip, in euros. A flat amount, so it weighs proportionally far more on a small line — which is exactly why a small position is harder to justify moving."
        ),
    "param.costs.max_extra_slippage_pct": "Accepted slippage",
    "paramhelp.costs.max_extra_slippage_pct": (
        "Gap accepted between the quote and the execution. It sets the minimum number of units below which the swap must be called off."
        ),
    "param.gates.min_score_delta": "Minimum score gap",
    "paramhelp.gates.min_score_delta": (
        "How far the candidate must beat the held asset, in standard deviations. Below this, the gap is indistinguishable from noise."
        ),
    "param.gates.cost_margin_multiple": "Cost margin",
    "paramhelp.gates.cost_margin_multiple": (
        "How many times the expected advantage must be worth the round-trip cost. At 2, a gain that merely covers the fees is not enough."
        ),
    "param.gates.max_candidate_vol_pct": "Maximum candidate volatility",
    "paramhelp.gates.max_candidate_vol_pct": (
        "Annualised 30-day volatility above which a candidate is discarded. Higher, and the expected gain owes more to the day it was measured than to the asset."
        ),
    "param.gates.max_candidate_drawdown_pct": "Maximum candidate drawdown",
    "paramhelp.gates.max_candidate_drawdown_pct": (
        "Largest 90-day drawdown tolerated in a candidate. Filters out what climbs hard after having fallen harder."
        ),
    "param.gates.min_volume_24h": "Minimum 24 h volume",
    "paramhelp.gates.min_volume_24h": (
        "Minimum 24-hour traded volume for a candidate, in euros. Below this, getting back out of the position costs more than getting in."
        ),
    "param.gates.required_consecutive_weeks": "Consecutive scans required",
    "paramhelp.gates.required_consecutive_weeks": (
        "How many consecutive scans the same candidate must hold up for. This is what avoids paying two legs for a one-week signal."
        ),
    "param.gates.use_fallback_candidate": "Fall back to the next candidate",
    "paramhelp.gates.use_fallback_candidate": (
        "On, the engine walks down the ranking to the first asset that passes volatility, drawdown and volume. Off, it only ever looks at the top-ranked one — and an over-volatile leader then blocks every rotation, week after week."
        ),
    "param.regime.enabled": "Regime detection",
    "paramhelp.regime.enabled": (
        "Reading of the market's state. Off, rotations are no longer suspended in a falling market and the refuge exit never fires."
        ),
    "param.regime.long_average_days": "Reference moving average",
    "paramhelp.regime.long_average_days": (
        "Length of the reference asset's moving average. Above it the reading is favourable; below it, not."
        ),
    "param.regime.min_breadth_pct": "Minimum market breadth",
    "paramhelp.regime.min_breadth_pct": (
        "Share of the ranking with positive 90-day momentum from which the second reading is favourable. Two favourable readings give BULL, one MIXED, none BEAR."
        ),
    "param.temporisation.enabled": "Wait in a refuge",
    "paramhelp.temporisation.enabled": (
        "A third possible verdict: leave for a stablecoin and wait. Off, a deteriorating position has only the trailing stop left to exit on."
        ),
    "param.temporisation.max_held_slow_momentum_pct": "Maximum slow momentum of the line",
    "paramhelp.temporisation.max_held_slow_momentum_pct": (
        "Slow momentum of the held asset below which deterioration is established. Must be negative or zero: it describes a fall, not a rise."
        ),
    "param.temporisation.min_held_drawdown_pct": "Minimum drawdown of the line",
    "paramhelp.temporisation.min_held_drawdown_pct": (
        "90-day drawdown of the held asset from which deterioration is established."
        ),
    "param.temporisation.min_bearish_share_pct": "Minimum bearish share",
    "paramhelp.temporisation.min_bearish_share_pct": (
        "Share of the ranking with negative slow momentum from which the market as a whole is judged degraded, not just your line."
        ),
    "param.temporisation.cost_margin_multiple": "Cost margin",
    "paramhelp.temporisation.cost_margin_multiple": (
        "How many times the observed fall must be worth the one-way cost into the refuge. Lower than for a rotation, because one leg costs less than two."
        ),
    "param.temporisation.required_consecutive_weeks": "Consecutive scans required",
    "paramhelp.temporisation.required_consecutive_weeks": (
        "How many consecutive scans of deterioration before moving into a refuge."
        ),
    "param.profit_taking.enabled": "Profit taking",
    "paramhelp.profit_taking.enabled": (
        "Recover the stake once, then let the rest run. Answers the risk of never selling."
        ),
    "param.profit_taking.trigger_gain_pct": "Trigger threshold",
    "paramhelp.profit_taking.trigger_gain_pct": (
        "Unrealised gain on the line from which the stake recovery fires."
        ),
    "param.profit_taking.max_fraction": "Maximum fraction sold",
    "paramhelp.profit_taking.max_fraction": (
        "Largest share of the line this mechanism may sell. It recovers the capital invested net of fees, never the whole position."
        ),
    "param.profit_taking.min_notional": "Minimum notional",
    "paramhelp.profit_taking.min_notional": (
        "Amount below which a partial sale is not worth its fees."
        ),
    "param.profit_taking.once_only": "Once per position only",
    "paramhelp.profit_taking.once_only": (
        "One recovery per position. Off, the line can be trimmed each time the threshold is crossed again."
        ),
    "param.trailing_stop.enabled": "Trailing stop",
    "paramhelp.trailing_stop.enabled": (
        "Full exit into the refuge when the price gives back too much of its peak."
        ),
    "param.trailing_stop.max_drawdown_pct": "Tolerated give-back",
    "paramhelp.trailing_stop.max_drawdown_pct": (
        "Give-back from the window's peak beyond which the position is closed."
        ),
    "param.trailing_stop.window_days": "Peak window",
    "paramhelp.trailing_stop.window_days": (
        "Window the peak is measured over. The longer it is, the harder the stop is to trigger."
        ),
    "param.trailing_stop.min_gain_pct": "Minimum gain required",
    "paramhelp.trailing_stop.min_gain_pct": (
        "Minimum gain above the cost basis for the stop to act. At zero it never touches a losing position — the refuge exit decides there instead."
        ),

    # ── Position editor and settings panel ──────────────────────────────────
    "editor.title": "Correct a line's figures",
    "editor.help": (
        "One column shows the derived figure and where it came from; the \u201ccorrected\u201d "
        "column beside it stays empty until you touch it. What you write there outranks "
        "everything, the chain included. Clearing the cell returns the line to its "
        "automatic source."
        ),
    "editor.cost_mode": "Enter the corrected capital as",
    "editor.cost_mode_total": "Total invested",
    "editor.cost_mode_unit": "Unit cost",
    "editor.col_asset": "Asset",
    "editor.col_units_auto": "Units (auto)",
    "editor.col_units_auto_help": (
        "Quantity derived automatically, followed by its source: chain, transactions, "
        "or a correction already in place."
        ),
    "editor.col_units_fix": "Corrected units",
    "editor.col_units_fix_help": (
        "In the asset's native units. Outranks both the chain and the ledger. "
        "Empty = automatic; zero = a line genuinely emptied."
        ),
    "editor.col_cost_auto": "Invested (auto)",
    "editor.col_cost_auto_help": (
        "Capital derived automatically, followed by its source: transactions, on-chain "
        "estimate, or a correction already in place."
        ),
    "editor.col_cost_fix_total": "Corrected capital (€)",
    "editor.col_cost_fix_unit": "Corrected unit cost (€)",
    "editor.col_cost_fix_help": (
        "Empty = automatic. With no capital invested, neither the trailing stop nor "
        "profit taking can fire on this line."
        ),
    "editor.col_reserve": "Reserve (€)",
    "editor.col_reserve_help": (
        "Share never proposed for a swap, for an asset that also pays chain fees."
        ),
    "editor.col_arbitrated": "Arbitrate",
    "editor.col_arbitrated_help": (
        "Unchecked, the line stays tracked and displayed but the engine proposes no "
        "move on it."
        ),
    "editor.apply": "Apply corrections",
    "editor.applied": "✅ {n} line(s) updated",
    "editor.nothing_changed": "Nothing changed.",
    "editor.reset_all": "Return everything to automatic",
    "editor.reset_done": "✅ Every correction has been removed",
    "editor.unreadable": "Unreadable figure: \u201c{value}\u201d.",
    "editor.divergence": (
        "⚠️ {symbol}: your correction says {manual} while the watched addresses report "
        "{chain}. It may well be right — a balance held elsewhere, an address you do not "
        "watch — but the gap is surfaced rather than hidden."
        ),

    "settings.title": "Rotation parameters",
    "settings.help": (
        "These thresholds decide when the engine proposes a move. Each is explained "
        "under its field. What you leave alone follows the value shipped with the tool "
        "and will pick up its future corrections; what you change is kept and marked."
        ),
    "settings.moved_count": "✍️ {n} parameter(s) moved away from the shipped value.",
    "settings.default_is": "shipped value: {value}",
    "settings.save_section": "Save this section",
    "settings.saved": "✅ Parameters saved",
    "settings.reset_all": "Return every parameter to its default",
    "settings.reset_done": "✅ {n} parameter(s) returned to the shipped value",
    "settings.reset_nothing": "No parameter had been changed.",
    "settings.on": "on",
    "settings.off": "off",
    "signal.settings_error": (
        "A stored threshold makes the rule set incoherent: {e} "
        "The shipped values apply meanwhile — fix it in the parameters panel."
        ),
}
