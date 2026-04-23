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
    "app.no_db_warning": "Please import or create a database to get started.",
    "app.nav_label": "Navigation",
    "app.doc_link_btn": "📖 Documentation (README)",
    "app.donate_btn": "☕ Buy me a Bitcoffee",
    "app.sidebar_version": "Finance Tracker v1.0.0",
    "app.sidebar_description": "Portfolio tracking tool with support for SCPI, Bitcoin, savings and more.",

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
    "products.advanced_delete_tip": "Tip: use the Transactions / Valuations page, filter by product, check 🗑️ and apply.",
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
        "| 3 | Update valuations | 📈 **My Valuations** |\n"
        "| 4 | View the dashboard | 📊 **Dashboard** |"
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
        "**Tip #2:** Update your **📈 Valuations** regularly (monthly minimum).\n\n"
        "**Tip #3:** Use the **🔮 Simulator** to plan your future investments.\n\n"
        "**Tip #4:** Back up your database regularly via the sidebar."
    ),
    "documentation.card_read_more": "Read full documentation →",
    "documentation.file_not_found": "⚠️ File {filename} not found.",
    "documentation.file_load_error": "❌ Error loading file: {error}",
}
