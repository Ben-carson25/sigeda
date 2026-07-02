# SIGEDA — Système Intégré de Gestion Électronique de Documents Administratifs

Projet de fin de cycle Licence 3 Génie Logiciel — ISI Dakar  
**Auteur :** Bénoni MOUELE NGOYE  
**Encadreur pédagogique :** M. ElHadji Mar DIOP  
**Encadreur professionnel :** Dr FOOVI Komlan Mawuli  
**Année académique :** 2025/2026

## Contexte
Solution GED sur mesure développée pour l'ASECNA (Agence pour la Sécurité de la Navigation Aérienne en Afrique et à Madagascar), couvrant les 19 États membres.

## Stack technique
- **Backend :** Python 3.11 / Django 4.2
- **API REST :** Django REST Framework + JWT
- **Base de données :** PostgreSQL (prod) / SQLite (dev)
- **Déploiement :** Docker + Gunicorn

## Modules MVP
- Module 1 — Authentification et gestion des accès (IAM)
- Module 2 — Dépôt, indexation et recherche documentaire
- Module 3 — Workflow de validation
- Module 4 — Tableau de bord et reporting

## Installation rapide

```bash
git clone https://github.com/Ben-carson25/sigeda.git
cd sigeda
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Comptes de démonstration

| Rôle | Identifiant | Mot de passe |
|------|-------------|--------------|
| Administrateur | admin | sigeda2026 |
| Gestionnaire | benoni | sigeda2026 |
| Validateur | elhadji | sigeda2026 |
| Validateur | foovi | sigeda2026 |

## Déploiement Docker

```bash
docker-compose up --build
```
