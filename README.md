# SIGEDA — Système Intégré de Gestion Électronique de Documents Administratifs

Projet de fin de cycle Licence 3 Génie Logiciel — ISI Dakar
**Auteur :** Bénoni MOUELE NGOYE
**Encadreur pédagogique :** M. ElHadji Mar DIOP
**Encadreur professionnel :** Dr FOOVI Komlan Mawuli
**Année académique :** 2025/2026

## Contexte

Solution GED sur mesure développée pour l'ASECNA (Agence pour la Sécurité de la
Navigation Aérienne en Afrique et à Madagascar), couvrant les 19 États membres.
Démonstration en ligne : https://sigeda.onrender.com

## Stack technique

- **Backend :** Python 3.11 / Django 4.2
- **API REST :** Django REST Framework + JWT
- **Base de données :** PostgreSQL 16 (local et démonstration), configurée via `DATABASE_URL` (.env)
- **Serveur :** Gunicorn + WhiteNoise
- **Hébergement :** Render.com (service web + PostgreSQL managé), déploiement depuis GitHub ;
  `Dockerfile` et `docker-compose.yml` fournis pour une exécution en conteneur
- **Fichiers :** stockés dans le dossier `media/` du serveur (système de fichiers)
- **Gestion de projet :** méthode Scrum, tableau Kanban Trello

## Modules MVP

- Module 1 — Authentification et gestion des accès (IAM), cloisonnement par entité
- Module 2 — Dépôt, indexation et recherche documentaire
- Module 3 — Workflow de validation avec journal d'audit intégral
- Module 4 — Tableau de bord et reporting

## Installation locale (Windows / Git Bash)


# 1. Cloner le dépôt
git clone https://github.com/Ben-carson25/sigeda.git
cd sigeda

# 2. Environnement virtuel
python -m venv venv
source venv/Scripts/activate

# 3. Dépendances
pip install -r requirements.txt

# 4. Base PostgreSQL (dans psql ou pgAdmin 4)
#    CREATE USER sigeda_user WITH PASSWORD 'votre_mot_de_passe' CREATEDB;
#    CREATE DATABASE sigeda_db OWNER sigeda_user;

# 5. Configuration
cp .env.example .env
#    → éditer .env : SECRET_KEY, DATABASE_URL

# 6. Migrations (crée les tables ET les 20 entités ASECNA)
python manage.py migrate

# 7. Données de démonstration (comptes de test + circuit MEI standard)
python manage.py seed_demo

# 8. Lancer
python manage.py runserver
```

## Profils utilisateurs

Agent, Gestionnaire documentaire, Validateur, Administrateur, Responsable.

## Comptes de démonstration (jury)

| Compte | Profil | Entité | Mot de passe |
|---|---|---|---|
| `admin.demo` | Administrateur | Siège de Dakar | `Sigeda#2026` |
| `gestionnaire.demo` | Gestionnaire documentaire | Siège de Dakar | `Sigeda#2026` |
| `validateur.demo` | Validateur | Siège de Dakar | `Sigeda#2026` |
| `agent.demo` | Agent | Siège de Dakar | `Sigeda#2026` |
| `responsable.demo` | Responsable | Siège de Dakar | `Sigeda#2026` |
| `gestionnaire.ci` | Gestionnaire documentaire | Représentation Côte d'Ivoire | `Sigeda#2026` |

Le compte `gestionnaire.ci` permet de démontrer le cloisonnement par entité :
il ne voit pas les documents du Siège.

## Tests

```bash
python manage.py test
```

31 tests unitaires couvrent les règles métier critiques : seed des 20 entités,
cloisonnement par entité, profils, décision du validateur (approuver, renvoyer, rejeter), nouvelle version, rapport, validation des formats de fichiers, journalisation d'audit.

## Variables d'environnement (production — Render)

| Variable | Valeur |
|---|---|
| `SECRET_KEY` | clé longue et aléatoire, jamais commitée |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `sigeda.onrender.com` |
| `DATABASE_URL` | URL interne de la base PostgreSQL managée Render |

## Structure du projet

```
config/      Configuration Django (settings 12-factor via .env)
accounts/    Module 1 — Entités, utilisateurs, rôles, seed, commande seed_demo
documents/   Module 2 — Documents, versions, validation des formats
workflows/   Module 3 — Circuits, étapes, workflows, actions, journal d'audit
dashboard/   Module 4 — Vues web, tableau de bord
templates/   Gabarits HTML
```
