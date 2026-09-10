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
    "app.sidebar_hint": "Ouvrir le menu",
    "app.nav_label": "Navigation",
    "app.doc_link_btn": "📖 Documentation (README)",
    "app.donate_btn": "☕ Buy me a Bitcoffee",
    "app.sidebar_version": "Finance Tracker v1.1.0",
    "app.sidebar_description": "Outil de suivi de portefeuille : SCPI, Bitcoin, épargne, crypto et signal de rotation. Outil éducatif, pas un conseil en investissement.",

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
    "products.advanced_delete_tip": "Astuce : utilisez la page Transactions ou le Tableau de Bord (détail du produit) pour supprimer les valorisations associées.",
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
        "| 3 | Mettre à jour les valorisations & consulter les performances | 📊 **Tableau de Bord** |"
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
    # Inflation tab
    "documentation.tab_inflation": "Inflation",
    "documentation.inflation_title": "📊 Inflation Paramétrable",
    "documentation.inflation_intro": (
        "Le simulateur long terme propose quatre profils d'inflation prédéfinis, "
        "plus une option personnalisée."
    ),
    "documentation.inflation_profiles_title": "Profils d'Inflation",
    "documentation.inflation_how_title": "Comment ça marche ?",
    "documentation.inflation_how": (
        "Dans le simulateur, remplace le simple champ *Inflation annuelle (%)* par un sélecteur "
        "de profil. Le taux correspondant est appliqué automatiquement à toutes les projections "
        "et apparaît dans le rapport PDF exporté."
    ),
    "documentation.inflation_sources": (
        "**Sources :** séries longues [INSEE IPC](https://www.insee.fr/fr/statistiques/4268033), "
        "indices de référence des loyers ([IRL — ANIL](https://www.anil.org/outils/indices-et-plafonds/tableau-de-lirl/)) "
        "et travaux [IGEDD/Friggit](https://www.cgedd.fr/prix-immobilier-friggit.pdf) sur l'évolution des prix immobiliers."
    ),
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
        "**Conseil #2 :** Mettez à jour vos valorisations régulièrement depuis le **📊 Tableau de Bord** (mensuellement minimum).\n\n"
        "**Conseil #3 :** Utilisez le **🔮 Simulateur** pour planifier vos investissements futurs.\n\n"
        "**Conseil #4 :** Sauvegardez régulièrement votre base de données via la sidebar."
    ),
    "documentation.card_read_more": "Lire la documentation complète →",
    "documentation.file_not_found": "⚠️ Fichier {filename} introuvable.",
    "documentation.file_load_error": "❌ Erreur lors du chargement du fichier: {error}",

    # ── Disclaimer ──────────────────────────────────────────────────────────────
    "disclaimer.title": "⚠️ Ceci n'est pas un conseil en investissement",
    "disclaimer.body": (
        "Cet outil est éducatif. Il n'est ni conseiller en investissement, ni intermédiaire "
        "financier, et n'est enregistré auprès d'aucune autorité de marché. Ce qu'il affiche "
        "décrit ce qui s'est déjà produit sur le marché : rien ici ne prédit un prix. "
        "Les crypto-actifs sont extrêmement volatils et tu peux perdre la totalité de ta mise. "
        "Aucune décision n'est exécutée par l'outil : tu restes seul à décider et à agir."
    ),
    "disclaimer.compact": (
        "Paramètres à exécuter à la main, pas une recommandation. Outil éducatif, "
        "aucun conseil en investissement."
    ),
    "disclaimer.more_title": "📄 Portée et limites de cet outil",
    "disclaimer.long": (
        "**Ce que fait cet outil.** Il applique des règles écrites à l'avance à des métriques "
        "rétrospectives — rendements passés, volatilité constatée, repli depuis un plus haut. "
        "Quand toutes les barrières d'un mécanisme passent, il propose un mouvement et en "
        "chiffre les paramètres.\n\n"
        "**Ce qu'il ne fait pas.** Il ne prédit aucun prix, ne tient aucun compte de ta "
        "situation personnelle, de tes objectifs, de ton horizon ou de ta tolérance au risque. "
        "Il n'exécute rien, ne détient aucune clé, ne signe aucune transaction.\n\n"
        "**Les limites que tu dois connaître.**\n\n"
        "- Les métriques décrivent le passé. Un actif qui a bien tenu peut s'effondrer le "
        "lendemain du scan.\n"
        "- Les seuils sont des choix, pas des vérités. Ils sont dans `config/signal_rules.toml` "
        "et tu peux les changer.\n"
        "- Un prix de revient reconstitué depuis une blockchain est une estimation. Une chaîne "
        "enregistre des mouvements, jamais un prix d'achat.\n"
        "- Les coûts de swap sont estimés à partir de moyennes. Ton devis réel peut s'en écarter "
        "nettement.\n\n"
        "**Fiscalité.** Un swap est généralement un fait générateur d'imposition. Cet outil ne "
        "calcule aucun impôt et ne produit aucun document fiscal.\n\n"
        "**En clair :** si tu suis une proposition de cet outil, c'est ta décision et ton risque."
    ),

    # ── Verdicts ────────────────────────────────────────────────────────────────
    "verdict.conserver": "Conserver",
    "verdict.temporiser": "Temporiser",
    "verdict.rotation": "Rotation",
    "verdict.alleger": "Alléger",
    "verdict.sortie_stop": "Sortie stop",

    # ── Barrières ───────────────────────────────────────────────────────────────
    "gate.ecart_de_score": "Écart de score",
    "gate.avantage_momentum_vs_cout": "Avantage momentum vs coût",
    "gate.volatilite_candidat": "Volatilité du candidat",
    "gate.drawdown_candidat": "Drawdown du candidat",
    "gate.liquidite_candidat": "Liquidité du candidat",
    "gate.regime_favorable": "Régime de marché",
    "gate.persistance": "Persistance",
    "gate.position_en_gain": "Position en gain",
    "gate.repli_depuis_le_haut": "Repli depuis le plus haut",
    "gate.plus_value": "Plus-value latente",
    "gate.montant_vendu_suffisant": "Montant vendu suffisant",
    "gate.jamais_pris": "Mise jamais récupérée",
    "gate.momentum_actif_detenu": "Momentum de l'actif détenu",
    "gate.drawdown_actif_detenu": "Drawdown de l'actif détenu",
    "gate.regime_marche": "Marché dégradé",
    "gate.baisse_vs_cout": "Baisse vs coût de sortie",
    "gate.liquidite_refuge": "Liquidité du refuge",

    # ── Confiance du prix de revient ────────────────────────────────────────────
    "confidence.high": "élevée",
    "confidence.medium": "moyenne",
    "confidence.low": "faible",
    "confidence.none": "aucune",

    # ── Signal crypto ───────────────────────────────────────────────────────────
    "signal.title": "📡 Signal Crypto",
    "signal.caption": (
        "Arbitrage de tes positions crypto contre le classement du marché, position par "
        "position, sur des règles écrites à l'avance."
    ),
    "signal.rules_error": "❌ Configuration des règles invalide : {e}",
    "signal.section_inputs": "Ce qui sera arbitré",
    "signal.inputs_help": (
        "Vérifie ces chiffres avant de lancer un scan : un verdict ne vaut que ce que valent "
        "ses entrées."
    ),
    "signal.no_positions": (
        "Aucune position crypto. Ajoute un portefeuille à suivre, ou associe un produit "
        "existant à un identifiant de marché depuis la page Portefeuilles."
    ),
    "signal.col_asset": "Actif",
    "signal.col_units": "Quantité",
    "signal.col_units_source": "Source quantité",
    "signal.col_cost_basis": "Capital investi",
    "signal.col_cost_source": "Source PRU",
    "signal.col_reserve": "Réserve de frais",
    "signal.col_arbitrated": "Arbitré",
    "signal.col_value": "Valeur",
    "signal.col_gain": "Plus-value",
    "signal.col_cost_of_move": "Coût d'un aller-retour",
    "signal.cost_of_move_help": (
        "Deux spreads, deux commissions et les frais de chaîne, rapportés au montant de la "
        "ligne. Une petite ligne les supporte moins bien."
    ),
    "signal.missing_cost_basis": (
        "Capital investi inconnu sur : {assets}. Le stop suiveur et la prise de bénéfice "
        "restent inactifs sur ces lignes."
    ),
    "signal.source_wallet": "chaîne",
    "signal.source_transactions": "transactions",
    "signal.source_manual": "corrigé",
    "signal.source_onchain": "estimé (chaîne)",
    "signal.source_valuation": "valorisation",
    "signal.source_none": "—",
    "signal.run_btn": "🔍 Lancer un scan",
    "signal.persist_opt": "Enregistrer ce scan dans l'historique",
    "signal.persist_help": (
        "Les barrières de persistance comptent les scans consécutifs. Un scan non enregistré "
        "ne fait progresser aucune série."
    ),
    "signal.scanning": "Scan en cours…",
    "signal.scan_error": "❌ Scan impossible : {e}",
    "signal.scan_done": "✅ Scan terminé — verdict global : {verdict}",
    "signal.section_market": "État du marché",
    "signal.regime": "Régime",
    "signal.regime_reference": "{symbol} > moyenne {days}j",
    "signal.regime_breadth": "Largeur du classement",
    "signal.candidate_line": "**Candidat retenu :** {symbol} — {name} (score {score})",
    "signal.no_candidate": (
        "Aucun candidat : tout le classement est déjà détenu."
    ),
    "signal.discarded_title": "Candidats mieux classés écartés",
    "signal.discarded_help": (
        "Le moteur descend le classement jusqu'au premier actif qui passe volatilité, "
        "drawdown et volume. Voici ceux qu'il a sautés, et pourquoi."
    ),
    "signal.insufficient_history": (
        "Historique trop court pour noter fiablement : {assets}."
    ),
    "signal.section_positions": "Verdict par position",
    "signal.not_arbitrated": "Cette ligne n'a pas été arbitrée.",
    "signal.not_evaluated": "Mécanisme non évalué sur ce scan.",
    "signal.mech_rotation": "Rotation",
    "signal.mech_stop": "Stop suiveur",
    "signal.mech_profit": "Prise de bénéfice",
    "signal.mech_temporisation": "Temporisation",
    "signal.gate": "Barrière",
    "signal.gate_status": "État",
    "signal.gate_value": "Mesuré",
    "signal.gate_threshold": "Seuil",
    "signal.gate_unit": "Unité",
    "signal.plan_title": "Plan de swap",
    "signal.plan_from": "Depuis",
    "signal.plan_to": "Vers",
    "signal.plan_amount": "Montant",
    "signal.plan_units": "Unités au prix de référence",
    "signal.plan_min_units": "Minimum acceptable",
    "signal.plan_min_units_help": (
        "Sous ce nombre d'unités, le devis ne correspond plus à ce que le scan a mesuré : "
        "c'est le moment d'annuler. Marge retenue : {pct} %."
    ),
    "signal.plan_quotes": "Fournisseurs à comparer :",
    "signal.ranking_title": "Classement complet",
    "signal.col_score": "Score",
    "signal.col_mom_slow": "Momentum lent",
    "signal.col_mom_fast": "Momentum rapide",
    "signal.col_vol": "Volatilité 30j",
    "signal.col_dd": "Drawdown 90j",
    "signal.section_last": "Dernier scan enregistré",
    "signal.last_scan": "Scan du {date} — verdict global : {verdict}",
    "signal.col_verdict": "Verdict",
    "signal.col_streak": "Série",
    "signal.col_date": "Date",
    "signal.col_candidate": "Candidat",
    "signal.history_title": "Historique des scans",
    "signal.history_help": (
        "C'est cette série qui alimente les barrières de persistance : un mouvement ne se "
        "déclenche que si les conditions tiennent plusieurs scans d'affilée."
    ),
    "signal.never_scanned": (
        "Aucun scan enregistré pour l'instant. Lance-en un pour obtenir un premier verdict."
    ),

    # ── Portefeuilles suivis ────────────────────────────────────────────────────
    "wallets.title": "👛 Portefeuilles Crypto",
    "wallets.caption": (
        "Ajoute une adresse publique : l'outil lit les soldes, reconstitue un prix de revient "
        "quand la chaîne le permet, et alimente le signal."
    ),
    "wallets.settings_title": "⚙️ Clés d'API et points d'accès",
    "wallets.settings_help": (
        "Tout est facultatif sauf pour les chaînes EVM. Rien n'est fourni avec l'application : "
        "chacun apporte son propre quota."
    ),
    "wallets.key_storage_warning": (
        "Ces clés sont stockées dans ta base de données. Elles partent donc avec le fichier "
        "quand tu l'exportes : ne partage pas une sauvegarde qui en contient."
    ),
    "wallets.etherscan_key": "Clé d'explorateur EVM",
    "wallets.etherscan_help": (
        "Gratuite sur etherscan.io. Une seule clé couvre Ethereum, Base, Arbitrum, Optimism, "
        "Polygon et BSC."
    ),
    "wallets.coingecko_key": "Clé CoinGecko (facultative)",
    "wallets.coingecko_help": (
        "Sans clé, le plan gratuit suffit pour un scan hebdomadaire."
    ),
    "wallets.mempool_url": "Indexeur Bitcoin",
    "wallets.mempool_help": (
        "Laisse vide pour mempool.space. Renseigne l'adresse de ton propre nœud si tu ne veux "
        "pas exposer tes adresses à un tiers."
    ),
    "wallets.solana_url": "Nœud RPC Solana",
    "wallets.solana_help": (
        "Laisse vide pour le point d'accès public, qui limite fortement le débit."
    ),
    "wallets.save_settings": "Enregistrer",
    "wallets.settings_saved": "✅ Réglages enregistrés",
    "wallets.add_title": "Ajouter un portefeuille",
    "wallets.privacy_notice": (
        "Interroger un indexeur révèle cette adresse à celui qui l'exploite. La "
        "synchronisation est activable et désactivable par portefeuille, et une adresse "
        "enregistrée sans synchronisation n'est jamais envoyée nulle part.\n\n"
        "**Monero n'est pas lisible** depuis une adresse seule : c'est le principe du "
        "protocole. Ces positions se saisissent à la main."
    ),
    "wallets.field_label": "Nom",
    "wallets.field_chain": "Chaîne",
    "wallets.field_address": "Adresse publique",
    "wallets.field_derive": "Reconstituer le prix de revient",
    "wallets.derive_help": (
        "Récupère l'historique des transferts et le valorise au cours du jour de chaque "
        "mouvement. Plus long, et impossible sur Solana."
    ),
    "wallets.field_autosync": "Autoriser la synchronisation",
    "wallets.autosync_help": (
        "Décoché, l'adresse est conservée mais jamais envoyée à un indexeur."
    ),
    "wallets.add_btn": "Ajouter",
    "wallets.address_required": "L'adresse est obligatoire.",
    "wallets.duplicate": "Cette adresse est déjà suivie sur cette chaîne.",
    "wallets.added": "✅ Portefeuille ajouté",
    "wallets.empty": (
        "Aucun portefeuille suivi. Ajoutes-en un, ou continue en saisie manuelle depuis "
        "la page Produits."
    ),
    "wallets.section_wallets": "Portefeuilles suivis",
    "wallets.col_label": "Nom",
    "wallets.col_chain": "Chaîne",
    "wallets.col_address": "Adresse",
    "wallets.col_sync": "Sync",
    "wallets.col_last": "Dernière sync",
    "wallets.col_error": "Dernier incident",
    "wallets.manage_title": "Gérer les portefeuilles",
    "wallets.toggle_sync": "Sync",
    "wallets.delete": "Supprimer",
    "wallets.sync_btn": "🔄 Synchroniser",
    "wallets.basis_btn": "💶 Recalculer les prix de revient",
    "wallets.sync_ok": "✅ {label} : {balances} solde(s), {transfers} mouvement(s) ajouté(s)",
    "wallets.sync_failed": "❌ {label} : {error}",
    "wallets.basis_done": "✅ {n} prix de revient recalculé(s)",
    "wallets.basis_nothing": "Aucun produit n'est alimenté par un portefeuille suivi.",
    "wallets.section_holdings": "Soldes découverts",
    "wallets.no_holdings": "Rien de découvert pour l'instant. Lance une synchronisation.",
    "wallets.col_asset": "Actif",
    "wallets.col_units": "Quantité",
    "wallets.col_listing": "Cotation",
    "wallets.col_product": "Produit",
    "wallets.unlisted_note": (
        "Sans cotation, donc ni valorisable ni arbitrable : {assets}. C'est le cas normal "
        "d'un token distribué qui ne s'échange nulle part."
    ),
    "wallets.map_title": "Associer les soldes aux produits",
    "wallets.map_help": (
        "Un solde associé à un produit alimente sa quantité et son prix de revient. "
        "Une association survit aux synchronisations suivantes."
    ),
    "wallets.map_to": "Associer à",
    "wallets.map_none": "— non associé —",
    "wallets.create_product": "Créer",
    "wallets.product_created": "✅ Produit « {name} » créé et associé",
    "wallets.ignore": "Ignorer",
    "wallets.section_basis": "Prix de revient",
    "wallets.no_basis": (
        "Aucun prix de revient reconstitué. Associe un solde à un produit, puis recalcule."
    ),
    "wallets.basis_estimate_warning": (
        "Ces montants sont **estimés**. Une blockchain enregistre des mouvements, jamais un "
        "prix d'achat : un token reçu d'un swap est valorisé au cours du jour, et un virement "
        "depuis un de tes autres portefeuilles non suivis est compté comme un achat. "
        "Corrige à la main dès que tu connais ton vrai prix."
    ),
    "wallets.col_unit_cost": "Prix de revient unitaire",
    "wallets.col_total": "Capital total",
    "wallets.col_confidence": "Confiance",
    "wallets.col_uncovered": "Unités non expliquées",
    "wallets.override_title": "Corriger un prix de revient",
    "wallets.override_help": (
        "Ta valeur remplace l'estimation partout, y compris dans le moteur de signal. "
        "Vide le champ pour revenir à la valeur reconstituée."
    ),
    "wallets.override_field": "Prix unitaire",
    "wallets.override_placeholder": "ex. 1250.50",
    "wallets.override_save": "Enregistrer",
    "wallets.override_invalid": "Montant illisible.",
    "wallets.override_saved": "✅ Prix de revient de « {name} » mis à jour",

    # ── Actif saisi à la main (sans adresse) ────────────────────────────────────
    "wallets.manual_title": "Ajouter un actif sans adresse",
    "wallets.manual_help": (
        "Pour un avoir qu'aucune adresse ne peut révéler : Monero, dont le solde "
        "ne se lit pas sans clé de vue, un solde d'échange, ou un actif que tu "
        "préfères ne pas exposer à un indexeur. La quantité et le prix de revient "
        "sont enregistrés comme un achat : ils restent modifiables dans la page "
        "Transactions, comme pour n'importe quel produit."
        ),
    "wallets.manual_search": "Chercher la cotation",
    "wallets.manual_search_placeholder": "ex. monero, ou XMR",
    "wallets.manual_search_btn": "🔍 Chercher",
    "wallets.manual_query_required": "Tape un nom ou un symbole à chercher.",
    "wallets.manual_search_failed": "Recherche impossible : {error}",
    "wallets.manual_no_hit": (
        "Aucune cotation ne correspond. Essaie le nom complet plutôt que le symbole."
        ),
    "wallets.manual_listing": "Cotation",
    "wallets.manual_name": "Nom du produit",
    "wallets.manual_name_help": (
        "Tel qu'il apparaîtra partout dans l'outil. Doit être unique."
        ),
    "wallets.manual_units": "Quantité détenue",
    "wallets.manual_units_placeholder": "ex. 12.5",
    "wallets.manual_units_help": (
        "En unités natives de l'actif (XMR, BTC, ETH…), pas en satoshis ni en wei. "
        "Laisse vide pour créer la ligne et saisir tes achats ensuite."
        ),
    "wallets.manual_units_invalid": "Quantité illisible.",
    "wallets.manual_date": "Date de la position",
    "wallets.manual_cost_mode": "Prix de revient donné en",
    "wallets.manual_cost_unit": "Prix unitaire",
    "wallets.manual_cost_total": "Montant total investi",
    "wallets.manual_cost": "Montant (€)",
    "wallets.manual_cost_placeholder": "ex. 142.30",
    "wallets.manual_cost_help": (
        "Laisse vide si l'actif n'a pas de prix d'achat — un airdrop, du minage. "
        "Le moteur traite alors le prix de revient comme inconnu et désactive le "
        "stop suiveur sur cette ligne, plutôt que de lire l'absence comme un gain total."
        ),
    "wallets.manual_cost_invalid": "Montant illisible.",
    "wallets.manual_reserve": "Réserve de frais (€)",
    "wallets.manual_reserve_help": (
        "Part jamais proposée au swap, pour un actif qui paie aussi les frais de chaîne."
        ),
    "wallets.manual_reserve_invalid": "Réserve illisible.",
    "wallets.manual_arbitrated": "Arbitrer cette ligne",
    "wallets.manual_arbitrated_help": (
        "Décoché, l'actif reste suivi et affiché mais le moteur ne propose aucun "
        "mouvement dessus."
        ),
    "wallets.manual_add_btn": "Ajouter l'actif",
    "wallets.manual_added": "✅ « {name} » ajouté et associé à la cotation {listing}",

    # ── Navigation et base ──────────────────────────────────────────────────────
    "nav.crypto_signal": "📡 Signal Crypto",
    "nav.crypto_wallets": "👛 Portefeuilles Crypto",
    "app.db_migrated": (
        "🔄 Base mise à jour : {n} migration(s) appliquée(s) (schéma v{old} → v{new})"
    ),
    "app.db_migrate_error": (
        "❌ Migration impossible : {e}. Exporte ta base avant toute autre manipulation."
    ),

    # ── Paramètres de rotation ─────────────────────────────────────────────────
    "section.universe": "Univers",
    "sectionhelp.universe": (
        "Ce que le classement examine, et à quel rythme il l'interroge."
        ),
    "section.signal": "Score composite",
    "sectionhelp.signal": (
        "Comment un actif est noté avant toute barrière."
        ),
    "section.costs": "Coûts d'un mouvement",
    "sectionhelp.costs": (
        "Ce qu'un swap coûte réellement — le chiffre que l'avantage doit dépasser."
        ),
    "section.gates": "Barrières de rotation",
    "sectionhelp.gates": (
        "Les six conditions qui doivent toutes passer pour qu'une rotation soit proposée."
        ),
    "section.regime": "Régime de marché",
    "sectionhelp.regime": (
        "L'état constaté du marché. Une description, jamais une prévision."
        ),
    "section.temporisation": "Temporisation en refuge",
    "sectionhelp.temporisation": (
        "Sortir vers un stablecoin pour attendre, quand aucune rotation ne passe et que le régime est dégradé."
        ),
    "section.profit_taking": "Prise de bénéfice",
    "sectionhelp.profit_taking": (
        "Récupérer la mise une fois, puis laisser courir."
        ),
    "section.trailing_stop": "Stop suiveur",
    "sectionhelp.trailing_stop": (
        "Sortie complète quand une ligne gagnante rend trop de son plus haut."
        ),

    "param.universe.top_n": "Profondeur du classement",
    "paramhelp.universe.top_n": (
        "Combien d'actifs le classement examine, par capitalisation. Plus haut ouvre le champ à des lignes moins liquides ; plus bas resserre sur les plus établies."
        ),
    "param.universe.request_delay_seconds": "Délai entre deux appels",
    "paramhelp.universe.request_delay_seconds": (
        "Temps d'attente entre deux appels à CoinGecko. Le plan gratuit coupe les rafales : descendre trop bas fait échouer le scan plutôt que l'accélérer."
        ),
    "param.signal.fast_window_days": "Fenêtre courte",
    "paramhelp.signal.fast_window_days": (
        "Fenêtre courte du momentum. Elle capte le mouvement récent, donc elle réagit vite et se trompe plus souvent."
        ),
    "param.signal.slow_window_days": "Fenêtre longue",
    "paramhelp.signal.slow_window_days": (
        "Fenêtre longue du momentum, la tendance de fond. Elle doit rester strictement plus longue que la fenêtre courte, sinon le score compte deux fois la même mesure."
        ),
    "param.signal.weight_slow_momentum": "Poids de la tendance de fond",
    "paramhelp.signal.weight_slow_momentum": (
        "Poids de la tendance de fond dans le score composite. C'est le terme dominant par défaut."
        ),
    "param.signal.weight_fast_momentum": "Poids du mouvement récent",
    "paramhelp.signal.weight_fast_momentum": (
        "Poids du mouvement récent. L'augmenter rend le classement plus nerveux, et les rotations plus fréquentes."
        ),
    "param.signal.weight_volatility": "Poids de la pénalité de volatilité",
    "paramhelp.signal.weight_volatility": (
        "Poids de la pénalité de volatilité, soustraite du score. À momentum égal, il départage celui qui y est arrivé le plus calmement."
        ),
    "param.costs.swap_spread_pct": "Spread par jambe",
    "paramhelp.costs.swap_spread_pct": (
        "Écart constaté entre le prix affiché et le prix obtenu, par jambe de swap. Il entre dans le coût que l'avantage doit dépasser."
        ),
    "param.costs.provider_fee_pct": "Commission par jambe",
    "paramhelp.costs.provider_fee_pct": (
        "Commission affichée par le fournisseur, par jambe de swap. S'ajoute au spread."
        ),
    "param.costs.network_fees_total": "Frais de chaîne, aller-retour",
    "paramhelp.costs.network_fees_total": (
        "Frais de chaîne pour un aller-retour, en euros. Montant fixe, donc il pèse proportionnellement bien plus lourd sur une petite ligne — c'est exactement pourquoi une petite position se justifie moins de bouger."
        ),
    "param.costs.max_extra_slippage_pct": "Glissement accepté",
    "paramhelp.costs.max_extra_slippage_pct": (
        "Écart accepté entre le devis et l'exécution. Il fixe le nombre minimal d'unités en dessous duquel il faut annuler le swap."
        ),
    "param.gates.min_score_delta": "Écart de score minimal",
    "paramhelp.gates.min_score_delta": (
        "De combien le candidat doit dominer l'actif détenu, en écarts-type. Sous ce seuil, l'écart n'est pas distinguable du bruit."
        ),
    "param.gates.cost_margin_multiple": "Marge sur le coût",
    "paramhelp.gates.cost_margin_multiple": (
        "Combien de fois l'avantage attendu doit valoir le coût de l'aller-retour. À 2, un gain qui couvre tout juste les frais ne suffit pas."
        ),
    "param.gates.max_candidate_vol_pct": "Volatilité maximale du candidat",
    "paramhelp.gates.max_candidate_vol_pct": (
        "Volatilité annualisée sur 30 jours au-delà de laquelle un candidat est écarté. Plus haut, le gain espéré tient surtout au jour où on l'a mesuré."
        ),
    "param.gates.max_candidate_drawdown_pct": "Drawdown maximal du candidat",
    "paramhelp.gates.max_candidate_drawdown_pct": (
        "Repli maximal sur 90 jours toléré chez un candidat. Filtre ce qui remonte fort après être tombé plus fort encore."
        ),
    "param.gates.min_volume_24h": "Volume 24 h minimal",
    "paramhelp.gates.min_volume_24h": (
        "Volume échangé sur 24 heures minimal pour un candidat, en euros. Sous ce seuil, ressortir de la position coûtera plus cher que d'y entrer."
        ),
    "param.gates.required_consecutive_weeks": "Scans consécutifs requis",
    "paramhelp.gates.required_consecutive_weeks": (
        "Nombre de scans consécutifs pendant lesquels le même candidat doit tenir. C'est ce qui évite de payer deux jambes pour un signal d'une semaine."
        ),
    "param.gates.use_fallback_candidate": "Repli sur le candidat suivant",
    "paramhelp.gates.use_fallback_candidate": (
        "Activé, le moteur descend le classement jusqu'au premier actif qui passe volatilité, drawdown et volume. Désactivé, il ne regarde que le mieux classé — et un leader trop volatil bloque alors toute rotation, semaine après semaine."
        ),
    "param.regime.enabled": "Détection de régime",
    "paramhelp.regime.enabled": (
        "Lecture de l'état du marché. Désactivée, les rotations ne sont plus suspendues en marché baissier et la temporisation ne se déclenche jamais."
        ),
    "param.regime.long_average_days": "Moyenne longue de référence",
    "paramhelp.regime.long_average_days": (
        "Longueur de la moyenne mobile de l'actif de référence. Au-dessus d'elle, la mesure est favorable ; en dessous, défavorable."
        ),
    "param.regime.min_breadth_pct": "Largeur de marché minimale",
    "paramhelp.regime.min_breadth_pct": (
        "Part du classement en momentum 90 jours positif à partir de laquelle la seconde mesure est favorable. Deux mesures favorables donnent BULL, une seule MIXTE, aucune BEAR."
        ),
    "param.temporisation.enabled": "Temporisation en refuge",
    "paramhelp.temporisation.enabled": (
        "Troisième verdict possible : sortir vers un stablecoin pour attendre. Désactivé, une position dégradée n'a plus que le stop suiveur pour sortir."
        ),
    "param.temporisation.max_held_slow_momentum_pct": "Momentum lent maximal de la ligne",
    "paramhelp.temporisation.max_held_slow_momentum_pct": (
        "Momentum lent de l'actif détenu sous lequel la dégradation est constatée. Doit être négatif ou nul : il décrit une baisse, pas une hausse."
        ),
    "param.temporisation.min_held_drawdown_pct": "Drawdown minimal de la ligne",
    "paramhelp.temporisation.min_held_drawdown_pct": (
        "Repli sur 90 jours de l'actif détenu à partir duquel la dégradation est constatée."
        ),
    "param.temporisation.min_bearish_share_pct": "Part baissière minimale",
    "paramhelp.temporisation.min_bearish_share_pct": (
        "Part du classement en momentum lent négatif à partir de laquelle le marché est jugé dégradé dans son ensemble, et pas seulement ta ligne."
        ),
    "param.temporisation.cost_margin_multiple": "Marge sur le coût",
    "paramhelp.temporisation.cost_margin_multiple": (
        "Combien de fois la baisse constatée doit valoir le coût de l'aller simple vers le refuge. Plus bas qu'en rotation, parce qu'un aller simple coûte moins qu'un aller-retour."
        ),
    "param.temporisation.required_consecutive_weeks": "Scans consécutifs requis",
    "paramhelp.temporisation.required_consecutive_weeks": (
        "Nombre de scans consécutifs de dégradation avant de passer en refuge."
        ),
    "param.profit_taking.enabled": "Prise de bénéfice",
    "paramhelp.profit_taking.enabled": (
        "Récupérer la mise une fois, puis laisser courir le reste. Répond au risque de ne jamais vendre."
        ),
    "param.profit_taking.trigger_gain_pct": "Seuil de déclenchement",
    "paramhelp.profit_taking.trigger_gain_pct": (
        "Plus-value latente à partir de laquelle la récupération se déclenche."
        ),
    "param.profit_taking.max_fraction": "Fraction maximale vendue",
    "paramhelp.profit_taking.max_fraction": (
        "Part maximale de la ligne que ce mécanisme peut vendre. Il récupère le capital investi net de frais, jamais la position entière."
        ),
    "param.profit_taking.min_notional": "Notionnel minimal",
    "paramhelp.profit_taking.min_notional": (
        "Montant en dessous duquel une vente partielle ne vaut pas ses frais."
        ),
    "param.profit_taking.once_only": "Une seule fois par position",
    "paramhelp.profit_taking.once_only": (
        "Une seule récupération par position. Désactivé, la ligne peut être allégée à chaque nouveau franchissement du seuil."
        ),
    "param.trailing_stop.enabled": "Stop suiveur",
    "paramhelp.trailing_stop.enabled": (
        "Sortie complète vers le refuge quand le prix décroche de son plus haut."
        ),
    "param.trailing_stop.max_drawdown_pct": "Repli toléré",
    "paramhelp.trailing_stop.max_drawdown_pct": (
        "Repli depuis le plus haut de la fenêtre au-delà duquel la position est soldée."
        ),
    "param.trailing_stop.window_days": "Fenêtre du plus haut",
    "paramhelp.trailing_stop.window_days": (
        "Fenêtre sur laquelle le plus haut est mesuré. Plus elle est longue, plus le stop est difficile à déclencher."
        ),
    "param.trailing_stop.min_gain_pct": "Gain minimal requis",
    "paramhelp.trailing_stop.min_gain_pct": (
        "Plus-value minimale au-dessus du prix de revient pour que le stop agisse. À zéro, il ne touche jamais une position en perte — c'est la temporisation qui décide alors."
        ),

    # ── Éditeur de positions et panneau de réglages ─────────────────────────
    "editor.title": "Corriger les chiffres d'une ligne",
    "editor.help": (
        "Une colonne montre le chiffre dérivé et d'où il vient ; la colonne « corrigé » "
        "à côté est vide tant que tu n'y touches pas. Ce que tu y écris prime sur tout, "
        "y compris sur ce que dit la chaîne. Vider la case rend la ligne à sa source "
        "automatique."
        ),
    "editor.cost_mode": "Saisir le capital corrigé en",
    "editor.cost_mode_total": "Capital total investi",
    "editor.cost_mode_unit": "Prix de revient unitaire",
    "editor.col_asset": "Actif",
    "editor.col_units_auto": "Quantité (auto)",
    "editor.col_units_auto_help": (
        "Quantité déduite automatiquement, suivie de sa source : chaîne, transactions, "
        "ou correction déjà en place."
        ),
    "editor.col_units_fix": "Quantité corrigée",
    "editor.col_units_fix_help": (
        "En unités natives de l'actif. Prime sur la chaîne comme sur le journal. "
        "Vide = automatique ; zéro = ligne réellement vidée."
        ),
    "editor.col_cost_auto": "Capital investi (auto)",
    "editor.col_cost_auto_help": (
        "Capital déduit automatiquement, suivi de sa source : transactions, estimation "
        "on-chain, ou correction déjà en place."
        ),
    "editor.col_cost_fix_total": "Capital corrigé (€)",
    "editor.col_cost_fix_unit": "PRU corrigé (€/unité)",
    "editor.col_cost_fix_help": (
        "Vide = automatique. Sans capital investi, ni stop suiveur ni prise de bénéfice "
        "ne peuvent se déclencher sur cette ligne."
        ),
    "editor.col_reserve": "Réserve (€)",
    "editor.col_reserve_help": (
        "Part jamais proposée au swap, pour un actif qui paie aussi les frais de chaîne."
        ),
    "editor.col_arbitrated": "Arbitrer",
    "editor.col_arbitrated_help": (
        "Décoché, la ligne reste suivie et affichée mais le moteur ne propose aucun "
        "mouvement dessus."
        ),
    "editor.apply": "Appliquer les corrections",
    "editor.applied": "✅ {n} ligne(s) mise(s) à jour",
    "editor.nothing_changed": "Rien n'a changé.",
    "editor.reset_all": "Tout remettre en automatique",
    "editor.reset_done": "✅ Toutes les corrections ont été retirées",
    "editor.unreadable": "Chiffre illisible : « {value} ».",
    "editor.divergence": (
        "⚠️ {symbol} : ta correction annonce {manual} alors que les adresses suivies "
        "en rapportent {chain}. C'est peut-être exact — un solde ailleurs, une adresse "
        "que tu ne suis pas — mais l'écart est signalé plutôt que masqué."
        ),

    "settings.title": "Paramètres de rotation",
    "settings.help": (
        "Ces seuils décident quand le moteur propose un mouvement. Chacun est expliqué "
        "sous son champ. Ce que tu ne touches pas suit la valeur livrée avec l'outil et "
        "profitera de ses futures corrections ; ce que tu changes est conservé et marqué."
        ),
    "settings.moved_count": "✍️ {n} paramètre(s) écarté(s) de la valeur livrée.",
    "settings.default_is": "valeur livrée : {value}",
    "settings.save_section": "Enregistrer cette section",
    "settings.saved": "✅ Paramètres enregistrés",
    "settings.reset_all": "Remettre tous les paramètres par défaut",
    "settings.reset_done": "✅ {n} paramètre(s) remis à la valeur livrée",
    "settings.reset_nothing": "Aucun paramètre n'était modifié.",
    "settings.on": "activé",
    "settings.off": "désactivé",
    "signal.settings_error": (
        "Un seuil enregistré rend le jeu de règles incohérent : {e} "
        "Les valeurs livrées s'appliquent en attendant — corrige-le dans les paramètres."
        ),
}
