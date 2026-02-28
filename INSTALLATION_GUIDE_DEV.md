# 💻 Guide Complet d'Installation (Développeurs)

> Pour les développeurs qui veulent contribuer ou exécuter l'application localement

**Table des matières:**
- [1. Prérequis Système](#-1-prérequis-système)
- [2. Installation Locale](#-2-installation-locale)
- [3. Configuration Initiale](#-3-configuration-initiale)
- [4. Vérification de l'Installation](#-4-vérification-de-linstallation)
- [5. Utilisation CLI](#-5-utilisation-cli)
- [6. Déploiement (Optionnel)](#-6-déploiement-optionnel)
- [7. Troubleshooting](#-7-troubleshooting)

---

## 🎉 1. Prérequis Système

### Système d'Exploitation

| OS | Version | Vérifié |
|----|---------|----------|
| **Windows** | 10+ (WSL2 recommandé) | ✅ |
| **macOS** | 10.14+ | ✅ |
| **Linux** | Ubuntu 18.04+, Debian 10+, Fedora 30+ | ✅ |

### Python

**Requirement:** Python 3.11+

**Vérifier votre version:**
```bash
python3 --version
# Output: Python 3.11.x ou supérieur
```

**Installation Python 3.11:**

**Windows:**
- Télécharger depuis [python.org](https://www.python.org/downloads/)
- Cocher "Add Python to PATH"
- Installer

**macOS:**
```bash
brew install python@3.11
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

**Linux (Fedora):**
```bash
sudo dnf install python3.11 python3.11-pip
```

### Dépendances Système (pour export PDF)

Optionnel mais recommandé pour WeasyPrint (génération de rapports PDF).

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get update
sudo apt-get install -y \
  libpango-1.0-0 libpango1.0-dev \
  libcairo2 libcairo2-dev \
  libgdk-pixbuf2.0-0 libgdk-pixbuf2.0-dev
```

**macOS:**
```bash
brew install cairo pango gdk-pixbuf libffi
```

**Windows:**
- Les dépendances binaires sont généralement pré-compilées
- Si problème, installer [GTK+ via MSYS2](http://www.msys2.org/)

### Git

**Vérifier:**
```bash
git --version
# Output: git version 2.x.x
```

**Installation:**
- **Windows/macOS:** Télécharger depuis [git-scm.com](https://git-scm.com)
- **Linux:** `sudo apt install git` (Debian) ou `sudo dnf install git` (Fedora)

---

## 💻 2. Installation Locale

### ✅ Checklist Pré-installation

- [ ] Python 3.11+ installé
- [ ] Git installé
- [ ] Dépendances système installées (optionnel mais recommandé)
- [ ] Accès internet disponible
- [ ] Espace disque: 500MB minimum

### Étape 1: Cloner le Dépôt

```bash
# Cloner le repository
git clone https://github.com/SKOHscripts/finance-tracker.git

# Aller dans le dossier
cd finance-tracker

# Vérifier le clonage
ls -la
# Vous devriez voir: app, cli, core, services, docs, tests, etc.
```

**Alternative: Fork personnel**

Si vous prévoyez de contribuer:

```bash
# 1. Sur GitHub: cliquez "Fork"
# 2. Cloner votre fork
git clone https://github.com/YOUR_USERNAME/finance-tracker.git
cd finance-tracker

# 3. Ajouter le repo original en tant que "upstream"
git remote add upstream https://github.com/SKOHscripts/finance-tracker.git
```

### Étape 2: Créer un Environnement Virtuel

#### Option A: venv (Python Natif) 👋

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (Command Prompt):**
```bash
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Vérifier l'activation:
```bash
# Vous devriez voir (venv) avant votre prompt
which python
# Output: /chemin/vers/venv/bin/python
```

#### Option B: Poetry (Recommandé) 🚀

**Installation Poetry:**
```bash
curl -sSL https://install.python-poetry.org | python3 -

# Vérifier
poetry --version
```

**Setup avec Poetry:**
```bash
# Poetry crée automatiquement le venv et installe les dépendances
poetry install

# Activer le shell Poetry
poetry shell

# Vérifier
which python
```

#### Option C: Conda (Alternative) 💾

```bash
conda create -n finance-tracker python=3.11
conda activate finance-tracker
```

### Étape 3: Installer les Dépendances

#### Avec pip:
```bash
# Vérifier que l'env est activé
which pip

# Installer requirements
pip install -r requirements.txt

# Vérifier l'installation
pip list | grep -E "streamlit|sqlmodel|typer|pydantic"
```

#### Avec Poetry:
```bash
# Si pas déjà fait
poetry install

# Vérifier
poetry show | grep -E "streamlit|sqlmodel|typer|pydantic"
```

#### Dépendances pour Développement (Optionnel):
```bash
# Si vous contribuez au code
pip install -r requirements-dev.txt

# Contient: pytest, black, ruff, mypy, etc.
```

**Ou avec Poetry:**
```bash
poetry install --with dev
```

### Étape 4: Initialiser la Base de Données

```bash
# S'assurer que l'env est activé
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows

# Initialiser la BD
finance-tracker init-db

# Output attendu:
# ✅ Base de données créée
# ✅ Fichier: ./finance_tracker.db
# ✅ Tables: products, transactions, valuations
```

**Problème?** Voir [Troubleshooting](#-7-troubleshooting)

### Étape 5: Charger les Données de Base

```bash
# Créer 6 produits standards
finance-tracker seed-products

# Output attendu:
# ✅ Products créés:
# - Cash Account (Cash)
# - SCPI Eurizon (SCPI)
# - Bitcoin (Crypto)
# - Livret A (Cash)
# - Assurance Vie (Insurance)
# - PER (PER)
```

---

## 🌐 3. Configuration Initiale

### Lancer l'Application Web

```bash
# S'assurer que l'env est activé
source venv/bin/activate

# Lancer Streamlit
streamlit run app.py

# Output:
#   You can now view your Streamlit app in your browser.
#
#   Local URL: http://localhost:8501
#   Network URL: http://192.168.x.x:8501
```

**Ouvrir dans le navigateur:** http://localhost:8501

**Arrêter l'application:** `Ctrl+C` dans le terminal

### Ports Alternatifs

Si le port 8501 est déjà utilisé:

```bash
streamlit run app.py --server.port 8502
```

### Configuration Streamlit Avancée

Modifier `~/.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#138d89"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#000000"

[client]
toolbarMode = "minimal"

[server]
headless = false
maxUploadSize = 500
```

---

## 🧪 4. Vérification de l'Installation

### Vérification Simple

```bash
# Vérifier les dépendances principales
python3 -c "import streamlit, sqlmodel, typer, pydantic; print('\u2705 OK')"
```

### Vérification Complète

**Script de vérification complet:**

```bash
#!/bin/bash

echo "🔍 Vérification de l'installation Finance Tracker"
echo "═════════════════════════════════════════════════"
echo ""

# Python
echo -n "✅ Python 3.11+: "
python3 --version

echo -n "✅ Pip: "
pip --version

echo ""
echo "Dépendances principales:"

echo -n "✅ Streamlit: "
python3 -c "import streamlit; print(streamlit.__version__)"

echo -n "✅ SQLModel: "
python3 -c "import sqlmodel; print(sqlmodel.__version__)"

echo -n "✅ Typer: "
python3 -c "import typer; print(typer.__version__)"

echo -n "✅ Pydantic: "
python3 -c "import pydantic; print(pydantic.__version__)"

echo ""
echo "CLI:"

echo -n "✅ Finance Tracker: "
finance-tracker --version

echo ""
echo "Base de données:"

if [ -f "finance_tracker.db" ]; then
    echo "✅ Base de données: Trouvée"
    echo -n "  Taille: "
    ls -lh finance_tracker.db | awk '{print $5}'
else
    echo "❌ Base de données: Non trouvée"
fi

echo ""
echo "✅✅✅ Installation vérifiée!"
```

**Utilisation:**
```bash
# Linux/macOS
chmod +x verify-install.sh
./verify-install.sh

# Windows (PowerShell)
python3 -c "import streamlit, sqlmodel, typer, pydantic; print('OK')"
```

### Tests Unités

```bash
# Exécuter tous les tests
pytest

# Avec coverage
pytest --cov=finance_tracker tests/

# Tests spécifiques
pytest tests/test_models.py -v
pytest tests/test_calculations.py -v
```

**Linter & Formatage:**

```bash
# Vérifier le style
black finance_tracker tests --check
ruff check finance_tracker tests
mypy finance_tracker

# Corriger les problèmes de style
black finance_tracker tests
ruff check finance_tracker tests --fix
```

---

## ⌨️ 5. Utilisation CLI

### Commandes de Base

```bash
# Afficher l'aide
finance-tracker --help

# Voir la version
finance-tracker --version

# Voir le portefeuille actuel
finance-tracker dashboard

# Avec format JSON
finance-tracker dashboard --json

# Avec format table
finance-tracker dashboard --format table
```

### Gestion des Produits

```bash
# Lister tous les produits
finance-tracker list-products

# Ajouter un produit (manuel)
finance-tracker add-product --name "Euribor 3M" --category insurance

# Voir les produits par catégorie
finance-tracker list-products --category crypto
```

### Gestion des Transactions

```bash
# Ajouter une transaction
finance-tracker add-transaction \
  --product "Bitcoin" \
  --quantity 0.5 \
  --price 45000 \
  --type buy \
  --date "2026-02-28"

# Lister les transactions
finance-tracker list-transactions

# Transactions d'un produit
finance-tracker list-transactions --product "Bitcoin"
```

### Rapports

```bash
# Générer un rapport
finance-tracker report --format pdf --output rapport.pdf

# Rapport en JSON
finance-tracker report --format json

# Rapport avec plages de dates
finance-tracker report --from "2026-01-01" --to "2026-02-28"
```

### Simulation

```bash
# Lancer une simulation
finance-tracker simulate \
  --years 10 \
  --annual-return 0.07 \
  --annual-contribution 5000

# Voir les scénarios
finance-tracker simulate --scenarios
```

---

## 🗡️ 6. Déploiement (Optionnel)

### Sur Serveur Linux

```bash
# 1. Mise à jour système
sudo apt update && sudo apt upgrade -y

# 2. Installer Python 3.11
sudo apt install -y python3.11 python3-pip

# 3. Cloner le repo
git clone https://github.com/SKOHscripts/finance-tracker.git
cd finance-tracker

# 4. Créer venv
python3.11 -m venv venv
source venv/bin/activate

# 5. Installer dépendances
pip install -r requirements.txt

# 6. Initialiser
finance-tracker init-db
finance-tracker seed-products

# 7. Lancer
streamlit run app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --logger.level=info
```

### Avec Docker

**Créer `Dockerfile`:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Installer dépendances système
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 libpango1.0-dev \
    libcairo2 libcairo2-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier code
COPY . .

# Initialiser BD
RUN finance-tracker init-db && \
    finance-tracker seed-products

# Lancer Streamlit
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]

EXPOSE 8501
```

**Build et run:**

```bash
# Build
docker build -t finance-tracker .

# Run
docker run -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  finance-tracker

# Accés: http://localhost:8501
```

### Avec Streamlit Cloud

Si vous avez un fork sur GitHub:

1. Accéder à [share.streamlit.io](https://share.streamlit.io)
2. Cliquer "Deploy an app"
3. Sélectionner le repository GitHub
4. Choisir la branche `main` et le fichier `app.py`
5. Cliquer "Deploy"

---

## 🔧 7. Troubleshooting

### ❌ Erreur: "command not found: finance-tracker"

**Cause:** CLI non installé ou env non actif

**Solution 1: Activer l'environnement**
```bash
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows
```

**Solution 2: Réinstaller en mode développement**
```bash
pip install -e .
```

**Solution 3: Utiliser via Python**
```bash
python3 -m finance_tracker.cli.main --help
```

### ❌ "ModuleNotFoundError: No module named 'streamlit'"

**Cause:** Dépendances non installées

**Solution:**
```bash
# Vérifier que venv est activé
which python
# Doit afficher le chemin dans venv

# Réinstaller
pip install -r requirements.txt

# Vérifier
python3 -c "import streamlit; print('OK')"
```

### ❌ Erreur WeasyPrint (PDF)

**Cause:** Dépendances système manquantes

**Solution:**

**Linux:**
```bash
sudo apt install libpango-1.0-0 libpango1.0-dev libcairo2 libcairo2-dev
```

**macOS:**
```bash
brew install cairo pango gdk-pixbuf
```

**Windows:**
```bash
pip install --upgrade weasyprint
```

### ❌ Port 8501 déjà utilisé

**Solution 1: Changer de port**
```bash
streamlit run app.py --server.port 8502
```

**Solution 2: Trouver et tuer le processus (Linux/macOS)**
```bash
lsof -i :8501
# Voir le PID

kill -9 <PID>

# Puis relancer
streamlit run app.py
```

### ❌ Base de données corrompue

**Cause:** Fermeture brutale ou erreur d'accès

**Solution:**
```bash
# Sauvegarder
cp finance_tracker.db finance_tracker.db.backup

# Vérifier l'intégrité
sqlite3 finance_tracker.db "PRAGMA integrity_check;"

# Si "ok", fichier valide
# Si erreur, réinitialiser:

rm finance_tracker.db
finance-tracker init-db
finance-tracker seed-products
```

### ❌ Problème de permissions (Linux)

**Solution:**
```bash
# Donner permissions au fichier
chmod +x app.py

# Pour le dossier venv
chmod -R u+w venv/

# Pour la BD
chmod 666 finance_tracker.db
```

### ❌ Streamlit crash au démarrage

**Vérifier:**
```bash
# 1. Python fonctionne
python3 --version

# 2. Streamlit installé
python3 -c "import streamlit; print(streamlit.__version__)"

# 3. App valide
python3 app.py  # Doit pas avoir d'erreur de syntaxe

# 4. Lancer avec debug
streamlit run app.py --logger.level=debug
```

### 🐛 Autres Problèmes?

1. Vérifier les [Issues GitHub](https://github.com/SKOHscripts/finance-tracker/issues)
2. Ouvrir une new [Discussion](https://github.com/SKOHscripts/finance-tracker/discussions)
3. Créer un [Issue Bug Report](https://github.com/SKOHscripts/finance-tracker/issues/new?labels=bug)

---

## 📄 Ressources Supplémentaires

### Documentation Officielle
- [Streamlit Docs](https://docs.streamlit.io/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Pydantic V2](https://docs.pydantic.dev/latest/)
- [Typer CLI](https://typer.tiangolo.com/)

### Références du Projet
- [🌐 README.md](./README.md) - Vue d'ensemble générale
- [📋 Architecture](./DOCUMENTATION_TECHNIQUE.md) - Structure technique
- [📚 Concepts](./docs/CONCEPTS_FONDAMENTAUX.md) - Principes clés
- [🌐 Interface](./docs/INTERFACE_WEB.md) - Guide utilisateur

### Outils Utiles
- [Pytest](https://docs.pytest.org/) - Testing
- [Black](https://github.com/psf/black) - Formatage code
- [Ruff](https://github.com/astral-sh/ruff) - Linting
- [MyPy](http://mypy-lang.org/) - Type checking

---

## 📺 Prochaines Étapes

Après une installation réussie:

1. **Explorez l'app:**
   - Accédez à http://localhost:8501
   - Lisez la page "Documentation"
   - Ajoutez quelques données test

2. **Lire la documentation:**
   - [Concepts Fondamentaux](./docs/CONCEPTS_FONDAMENTAUX.md)
   - [Architecture](./DOCUMENTATION_TECHNIQUE.md)
   - [Guide Interface](./docs/INTERFACE_WEB.md)

3. **Contribuer:**
   - Consulter [README.md](./README.md) section Contribution
   - Cloner votre fork
   - Créer une branche feature
   - Soumettre une PR

4. **Supporter:**
   - ★ Laisser une star sur GitHub
   - 🐜 Partager le projet
   - 🐛 Reporter les bugs
   - 💡 Proposer des idées

---

**Happy Coding!** 🚀

Dernière mise à jour: 28/02/2026
