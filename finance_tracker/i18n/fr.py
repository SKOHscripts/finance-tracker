"""French UI strings."""

STRINGS: dict[str, str] = {
    # ── Navigation ─────────────────────────────────────────────────────────────
    "nav.documentation": "📖 Documentation",
    "nav.dashboard": "📊 Tableau de Bord",
    "nav.simulation": "🔮 Simulation Long Terme",
    "nav.products": "🏷️ Mes Produits",
    "nav.transactions": "💸 Mes Transactions",
    "nav.valuations": "📈 Mes Valorisations",
    "nav.bitcoin": "₿ Espace Bitcoin",

    # ── App / Sidebar ───────────────────────────────────────────────────────────
    "app.lang_selector": "🌐 Language / Langue",
    "app.db_section": "Gestion des Données",
    "app.import_label": "Importer votre sauvegarde (.db)",
    "app.create_portfolio_btn": "Créer un nouveau portefeuille",
    "app.db_loaded_msg": "Base de données chargée !",
    "app.db_init_with_products": "✅ Base initialisée avec {n} produits par défaut",
    "app.db_init": "✅ Base initialisée",
    "app.export_btn": "📥 Sauvegarder la base (PC)",
    "app.no_db_warning": "Veuillez importer ou créer une base pour commencer.",
    "app.nav_label": "Navigation",
    "app.doc_link_btn": "📖 Documentation (README)",
    "app.donate_btn": "☕ Buy me a Bitcoffee",
    "app.sidebar_version": "Finance Tracker v1.0.0",
    "app.sidebar_description": "Outil de suivi de portefeuille avec support SCPI, Bitcoin, épargne et plus.",

    # ── Dashboard ───────────────────────────────────────────────────────────────
    "dashboard.title": "Tableau de bord",
    "dashboard.caption": "Aperçu global et performances de votre portefeuille d'investissement.",
    "dashboard.load_error": "Impossible de charger le portefeuille : {e}",
    "dashboard.section_overview": "Vue d'ensemble",
    "dashboard.metric_total_value": "Valeur Totale",
    "dashboard.metric_total_invested": "Total Investi",
    "dashboard.metric_gains": "Plus-values",
    "dashboard.metric_cash": "Cash disponible",
    "dashboard.section_allocation": "Répartition du portefeuille",
    "dashboard.empty_portfolio": "Votre portefeuille est vide. Ajoutez des valorisations dans l'onglet correspondant.",
    "dashboard.section_detail": "Détail par produit",
    "dashboard.section_exports": "Exports & Rapports",
    "dashboard.prepare_pdf": "Préparer le rapport PDF",
    "dashboard.generating_pdf": "⏳ Génération du rapport PDF...",
    "dashboard.download_pdf": "⬇️ Télécharger le PDF",
    "dashboard.pdf_filename": "rapport_portefeuille.pdf",
    "dashboard.prepare_json": "Préparer l'export JSON",
    "dashboard.generating_json": "⏳ Structuration des données...",
    "dashboard.download_json": "⬇️ Télécharger le JSON",
    "dashboard.json_filename": "dashboard_data.json",
    "dashboard.refresh_exports": "Rafraîchir les données d'export",
    "dashboard.error": "❌ Erreur : {e}",
    # Bitcoin expander
    "dashboard.btc_refresh_btn": "Actualiser le cours",
    "dashboard.btc_connecting": "Connexion aux APIs...",
    "dashboard.btc_offline": "**Hors ligne** — Réseau inaccessible. Saisissez le prix manuellement ci-dessous.",
    "dashboard.btc_metric_value": "Valeur actuelle",
    "dashboard.btc_metric_qty": "Quantité",
    "dashboard.btc_metric_pru": "PRU",
    "dashboard.btc_metric_pnl": "P&L Latente",
    "dashboard.btc_price_history": "Historique des prix (snapshots)",
    "dashboard.btc_new_snapshot": "Nouveau Snapshot",
    "dashboard.btc_date_label": "Date",
    "dashboard.btc_full_price_label": "Prix d'un BTC plein (EUR)",
    "dashboard.btc_qty_label": "Quantité (en Satoshis)",
    "dashboard.btc_qty_help": "1 BTC = 100 000 000 Sats",
    "dashboard.btc_computed_value": "Valeur calculée : **{v}**",
    "dashboard.btc_save_snapshot": "Enregistrer le snapshot",
    "dashboard.btc_qty_error": "La quantité (en sats) et le prix doivent être > 0.",
    "dashboard.btc_snapshot_saved": "✅ Snapshot enregistré — Valeur : {v}",
    "dashboard.btc_error": "❌ Erreur : {e}",
    # Table columns
    "dashboard.col_date": "Date",
    "dashboard.col_btc_price": "Prix BTC (€)",
    "dashboard.col_sats": "Satoshis",
    "dashboard.col_total_value": "Valeur totale (€)",
    # Allocation chart
    "dashboard.chart_weight_pct": "Poids (%)",
    "dashboard.chart_product": "Produit",

    # ── Simulation ─────────────────────────────────────────────────────────────
    "simulation.title": "Simulation Long Terme",
    "simulation.no_product_warning": "Ajoute au moins un produit dans 'Ajouter Produits' avant de simuler.",
    "simulation.section_global_params": "Paramètres globaux",
    "simulation.param_duration": "Durée (années)",
    "simulation.param_income": "Revenu brut annuel N (€)",
    "simulation.param_income_growth": "Augmentation revenu / an (%)",
    "simulation.param_living_costs": "Dépenses annuelles (€)",
    "simulation.param_initial_tax": "Impôt dû N-1 à payer en année 1 (€)",
    "simulation.section_tax": "Fiscalité (barème progressif)",
    "simulation.tax_caption": "Tranches annuelles — laisse `up_to` vide pour la dernière tranche.",
    "simulation.std_deduction": "Abattement forfaitaire (%)",
    "simulation.section_per": "PER — Plafond déductible",
    "simulation.per_rate": "% du revenu N-1",
    "simulation.per_min": "Plafond PER minimum (€/an)",
    "simulation.per_max": "Plafond PER maximum (€/an, 0 = illimité)",
    "simulation.section_product_params": "Paramètres par produit",
    "simulation.product_params_caption": "Seuls les paramètres pertinents s'affichent selon la catégorie définie ci-dessus.",
    "simulation.scpi_caption": "Pour une SCPI, les apports sont définis via **'Parts achetées / an'** ci-dessous.",
    "simulation.cash_required_error": "⚠️ Il faut au moins un produit de catégorie 'cash'.",
    "simulation.submit_hint": "Soumets le formulaire pour lancer la simulation.",
    "simulation.section_summary": "Résumé final",
    "simulation.metric_final_value": "Valeur finale",
    "simulation.metric_real_value": "Valeur réelle (inflation)",
    "simulation.metric_invested": "Investi cumulé (hors cash)",
    "simulation.metric_tax_due": "Impôt dû N à payer N+1",
    "simulation.section_tables": "Tableaux de données",
    "simulation.tab_by_period": "Par période",
    "simulation.tab_by_product": "Par produit (long)",
    "simulation.section_charts": "Graphiques",
    "simulation.section_exports": "Exports",
    "simulation.prepare_pdf": "Préparer le rapport PDF",
    "simulation.section_inflation": "Profil d'inflation",
    "simulation.section_categories": "Catégories des produits",
    "simulation.pdf_error": "Erreur lors de la génération du PDF : {e}",

    # ── Products ────────────────────────────────────────────────────────────────
    "products.title": "Mes Produits",
    "products.caption": "Créez, éditez et supprimez vos produits. (La suppression peut échouer si des transactions/valorisations existent.)",
    "products.add_expander": "Ajouter un produit",
    "products.field_name": "Nom *",
    "products.field_type": "Type",
    "products.field_unit": "Unité",
    "products.field_risk": "Niveau de risque (optionnel)",
    "products.field_description": "Description",
    "products.field_fees": "Frais",
    "products.field_tax": "Fiscalité",
    "products.create_btn": "Créer",
    "products.name_required": "Le nom est obligatoire.",
    "products.name_duplicate": "Un produit nommé '{name}' existe déjà.",
    "products.created_success": "✅ Produit créé.",
    "products.error": "❌ Erreur : {e}",
    "products.empty": "Aucun produit pour l'instant.",
    "products.list_title": "Liste des produits (éditable)",
    "products.col_id": "ID",
    "products.col_name": "Nom",
    "products.col_type": "Type",
    "products.col_unit": "Unité",
    "products.col_risk": "Risque",
    "products.col_description": "Description",
    "products.col_fees": "Frais",
    "products.col_tax": "Fiscalité",
    "products.col_created_at": "Créé le",
    "products.col_delete": "🗑️ Supprimer",
    "products.advanced_delete_expander": "Outils suppression (avancé)",
    "products.advanced_delete_help": "Si une suppression de produit échoue, supprimez d'abord les transactions/valorisations associées.",
    "products.advanced_delete_tip": "Astuce : utilisez la page Transactions / Valorisations, filtrez par produit, cochez 🗑️ puis appliquez.",
    "products.apply_btn": "Appliquer les changements",
    "products.name_empty_error": "Tous les produits (non supprimés) doivent avoir un nom.",
    "products.name_unique_error": "Les noms de produits doivent être uniques (au moins parmi les lignes non supprimées).",
    "products.applied_success": "✅ Changements appliqués.",
    "products.reload_btn": "Recharger depuis la DB",

    # ── Transactions ────────────────────────────────────────────────────────────
    "transactions.title": "Mes Transactions",
    "transactions.caption": "Ajout, modification et suppression directement depuis la liste.",
    "transactions.no_products": "Aucun produit. Créez d'abord un produit pour pouvoir ajouter des transactions.",
    "transactions.add_expander": "Ajouter une transaction",
    "transactions.field_product": "Produit",
    "transactions.field_type": "Type",
    "transactions.field_date": "Date",
    "transactions.field_amount": "Montant EUR (optionnel)",
    "transactions.field_qty_sats": "Quantité (en Satoshis)",
    "transactions.field_qty_units": "Quantité (Parts / Unités)",
    "transactions.field_qty_help_btc": "Rappel: 1 BTC = 100 000 000 Sats",
    "transactions.field_note": "Note",
    "transactions.add_btn": "Ajouter",
    "transactions.added_success": "✅ Transaction ajoutée.",
    "transactions.error": "❌ Erreur : {e}",
    "transactions.filter_product": "Filtrer produit",
    "transactions.filter_type": "Filtrer type",
    "transactions.filter_all": "Tous",
    "transactions.sort_label": "Tri",
    "transactions.sort_date_desc": "Date décroissante",
    "transactions.sort_date_asc": "Date croissante",
    "transactions.sort_id_desc": "ID décroissant",
    "transactions.empty_filter": "Aucune transaction pour ce filtre.",
    "transactions.list_title": "Historique (éditable)",
    "transactions.btc_qty_info": "ℹ️ Les quantités concernant Bitcoin sont affichées et enregistrées en **Satoshis** (nombres entiers). Les autres produits restent en unités standards.",
    "transactions.col_id": "ID",
    "transactions.col_date": "Date",
    "transactions.col_product": "Produit",
    "transactions.col_type": "Type",
    "transactions.col_amount": "Montant EUR",
    "transactions.col_qty": "Quantité (Sats ou Unités)",
    "transactions.col_note": "Note",
    "transactions.col_delete": "🗑️ Supprimer",
    "transactions.apply_btn": "Appliquer les changements",
    "transactions.invalid_product": "Produit invalide: {name}",
    "transactions.applied_success": "✅ Changements appliqués.",
    "transactions.reload_btn": "Recharger depuis la DB",

    # ── Valuations ──────────────────────────────────────────────────────────────
    "valuations.title": "Mes Valorisations",
    "valuations.caption": "Snapshots de valeur : ajout, édition et suppression depuis une table unique.",
    "valuations.no_products": "Aucun produit. Créez un produit avant d'ajouter des valorisations.",
    "valuations.add_expander": "Ajouter une valorisation",
    "valuations.field_product": "Produit",
    "valuations.field_date": "Date",
    "valuations.field_total": "Valeur totale EUR",
    "valuations.field_unit_price_btc": "Prix d'un BTC plein (EUR)",
    "valuations.field_unit_price": "Prix unitaire (EUR, optionnel)",
    "valuations.add_btn": "Ajouter",
    "valuations.total_positive_error": "La valeur totale doit être > 0.",
    "valuations.added_success": "✅ Valorisation ajoutée.",
    "valuations.error": "❌ Erreur : {e}",
    "valuations.filter_product": "Filtrer produit",
    "valuations.filter_all": "Tous",
    "valuations.sort_label": "Tri",
    "valuations.sort_date_desc": "Date décroissante",
    "valuations.sort_date_asc": "Date croissante",
    "valuations.sort_id_desc": "ID décroissant",
    "valuations.empty_filter": "Aucune valorisation pour ce filtre.",
    "valuations.list_title": "Historique (éditable)",
    "valuations.col_id": "ID",
    "valuations.col_date": "Date",
    "valuations.col_product": "Produit",
    "valuations.col_total": "Valeur totale EUR",
    "valuations.col_unit_price": "Prix unitaire EUR",
    "valuations.col_delete": "🗑️ Supprimer",
    "valuations.apply_btn": "Appliquer les changements",
    "valuations.invalid_product": "Produit invalide: {name}",
    "valuations.total_positive_update_error": "La valeur totale doit être > 0.",
    "valuations.applied_success": "✅ Changements appliqués.",
    "valuations.reload_btn": "Recharger depuis la DB",

    # ── Bitcoin ─────────────────────────────────────────────────────────────────
    "bitcoin.title": "₿ Espace Bitcoin",
    "bitcoin.redirect_info": (
        "**Cette page a été fusionnée dans le Tableau de Bord.**\n\n"
        "Toutes les fonctionnalités Bitcoin sont désormais accessibles depuis "
        "**📊 Tableau de Bord → Détail par produit → Bitcoin** :\n\n"
        "- Cours live BTC/EUR avec badge LIVE / OFFLINE\n"
        "- Quantité en Satoshis\n"
        "- PRU et P&L latente\n"
        "- Historique des prix (snapshots)\n"
        "- Formulaire de nouveau snapshot\n"
        "- Tableau des derniers snapshots"
    ),
    "bitcoin.redirect_link": "Rendez-vous dans **📊 Tableau de Bord** pour accéder à votre espace Bitcoin.",

    # ── Documentation ───────────────────────────────────────────────────────────
    "documentation.title": "Documentation",
    "documentation.subtitle": "Guide complet pour utiliser et comprendre Finance Tracker",
    "documentation.tab_home": "Accueil",
    "documentation.tab_concepts": "Concepts",
    "documentation.tab_calculs": "Calculs",
    "documentation.tab_interface": "Interface Web",
    "documentation.tab_database": "Base de Données",
    "documentation.tab_install": "Installation",
    "documentation.tab_help": "Aide",
    # Home tab
    "documentation.home_title": "Bienvenue dans Finance Tracker",
    "documentation.home_intro": (
        "**Finance Tracker** est une application complète de gestion de portefeuille d'investissement,\n"
        "conçue pour les investisseurs francophones soucieux de leur vie privée."
    ),
    "documentation.home_features_title": "Fonctionnalités Principales",
    "documentation.home_feature_tracking": "**📊 Suivi Complet**\n- Portefeuille multi-actifs\n- SCPI, Bitcoin, Livrets\n- Assurance-vie, PER",
    "documentation.home_feature_analysis": "**📈 Analyses Avancées**\n- Performance MWRR\n- Intérêts composés\n- Projections long terme",
    "documentation.home_feature_privacy": "**🔒 Vie Privée**\n- Données locales\n- Aucun cloud requis\n- Export/Import facile",
    "documentation.home_quickstart_title": "Démarrage Rapide",
    "documentation.home_quickstart_table": (
        "| Étape | Action | Page |\n"
        "|-------|--------|------|\n"
        "| 1 | Créer vos produits | 🏷️ **Mes Produits** |\n"
        "| 2 | Ajouter des transactions | 💸 **Mes Transactions** |\n"
        "| 3 | Mettre à jour les valorisations | 📈 **Mes Valorisations** |\n"
        "| 4 | Consulter le tableau de bord | 📊 **Tableau de Bord** |"
    ),
    "documentation.home_explore_title": "Explorer la Documentation",
    "documentation.home_explore_text": "Utilisez les **onglets ci-dessus** pour accéder aux différentes sections de documentation.",
    "documentation.home_tip": (
        "**Astuce :** Commencez par l'onglet **Concepts** pour comprendre les 3 piliers\n"
        "du système (Produits, Transactions, Valorisations) avant d'utiliser l'application."
    ),
    # Concepts tab
    "documentation.concepts_title": "Concepts Fondamentaux",
    "documentation.concepts_intro": (
        "Finance Tracker repose sur **trois piliers** essentiels. Comprendre ces concepts\n"
        "est la clé pour utiliser efficacement l'application."
    ),
    "documentation.concepts_products_title": "1. Produits (Products)",
    "documentation.concepts_transactions_title": "2. Transactions (Mouvements)",
    "documentation.concepts_valuations_title": "3. Valorisations (Snapshots)",
    "documentation.full_doc_link": "**[Lire la documentation complète : {title}]({url})**",
    "documentation.expand_full_doc": "Voir le document complet",
    # Calculs tab
    "documentation.calculs_title": "Formules & Calculs",
    "documentation.calculs_intro": (
        "Toutes les formules mathématiques utilisées par Finance Tracker pour calculer\n"
        "les performances, gains et projections."
    ),
    "documentation.calculs_key_metrics": "Indicateurs Clés",
    "documentation.calculs_compound": "Intérêts Composés",
    "documentation.calculs_bitcoin_title": "₿ Cas Spécial : Bitcoin",
    # Interface tab
    "documentation.interface_title": "Guide Interface Web",
    "documentation.interface_intro": "Guide complet page par page de l'interface Streamlit.",
    "documentation.interface_architecture": "Architecture de l'Application",
    "documentation.interface_workflow": "Flux de Travail Recommandé",
    "documentation.interface_tx_types": "Types de Transactions",
    # Installation tab
    "documentation.install_title": "Installation & Développement",
    "documentation.install_intro": "Guides pour installer, configurer et contribuer au projet.",
    "documentation.install_quickstart": "Démarrage Rapide (Développeur)",
    "documentation.install_architecture": "Architecture du Projet",
    "documentation.install_dev_docs": "Documentation Développeur",
    # Database tab
    "documentation.database_title": "Structure de la Base de Données",
    "documentation.database_intro": (
        "Finance Tracker utilise **SQLite** avec **SQLModel** pour la persistance des données."
    ),
    "documentation.database_tables": "Tables Principales",
    "documentation.database_relations": "Relations",
    # Help tab
    "documentation.help_title": "Aide & Support",
    "documentation.help_faq_title": "FAQ",
    "documentation.help_resources_title": "Ressources",
    "documentation.help_resources_official": "**Liens Officiels**",
    "documentation.help_resources_web": "[Application Web](https://finance-tracker-skohscripts.streamlit.app/)",
    "documentation.help_resources_github": "[GitHub](https://github.com/SKOHscripts/finance-tracker)",
    "documentation.help_resources_support": "**Support**",
    "documentation.help_resources_bug": "[Signaler un bug](https://github.com/SKOHscripts/finance-tracker/issues)",
    "documentation.help_resources_feature": "[Proposer une fonctionnalité](https://github.com/SKOHscripts/finance-tracker/discussions)",
    "documentation.help_resources_docs": "**Documentation**",
    "documentation.help_resources_readme": "[README complet]({url}/README.md)",
    "documentation.help_resources_roadmap": "[Roadmap]({url}/ROADMAP.md)",
    "documentation.help_tips_title": "Conseils d'Utilisation",
    "documentation.help_tips": (
        "**Conseil #1 :** Commencez par lire les **Concepts** pour comprendre les 3 piliers du système.\n\n"
        "**Conseil #2 :** Mettez à jour vos **📈 Valorisations** régulièrement (mensuellement minimum).\n\n"
        "**Conseil #3 :** Utilisez le **🔮 Simulateur** pour planifier vos investissements futurs.\n\n"
        "**Conseil #4 :** Sauvegardez régulièrement votre base de données via la sidebar."
    ),
    "documentation.card_read_more": "Lire la documentation complète →",
    "documentation.file_not_found": "⚠️ Fichier {filename} introuvable.",
    "documentation.file_load_error": "❌ Erreur lors du chargement du fichier: {error}",
}
