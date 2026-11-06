"""Crée les données de démonstration pour la soutenance :
- 5 comptes utilisateurs (un par profil), rattachés au Siège de Dakar
- 1 compte gestionnaire rattaché à la Représentation de Côte d'Ivoire
  (pour démontrer le cloisonnement par entité)
- 1 circuit de validation « MEI standard » à 4 étapes

Usage : python manage.py seed_demo
Idempotente : peut être relancée sans créer de doublons.
"""
from django.core.management.base import BaseCommand

from accounts.models import Entite, Utilisateur
from workflows.models import CircuitValidation, EtapeCircuit

COMPTES = [
    # (username, matricule, prenom, nom, role, code_entite, mot_de_passe)
    ('admin.demo',        'ASE-2026-0001', 'Aminata',  'DIALLO',  'ADMIN',        'SIEGE',  'Sigeda#2026'),
    ('gestionnaire.demo', 'ASE-2026-0002', 'Bénoni',   'MOUELE',  'GESTIONNAIRE', 'SIEGE',  'Sigeda#2026'),
    ('validateur.demo',   'ASE-2026-0003', 'Mamadou',  'FALL',    'VALIDATEUR',   'SIEGE',  'Sigeda#2026'),
    ('agent.demo',        'ASE-2026-0004', 'Fatou',    'NDIAYE',  'AGENT',        'SIEGE',  'Sigeda#2026'),
    ('responsable.demo',  'ASE-2026-0006', 'Ibrahima', 'SARR',    'RESPONSABLE',  'SIEGE',  'Sigeda#2026'),
    ('gestionnaire.ci',   'ASE-2026-0005', 'Koffi',    'KOUAME',  'GESTIONNAIRE', 'REP-CI', 'Sigeda#2026'),
]

ETAPES_MEI = [
    # (ordre, libelle, type_etape, username_validateur, delai_jours)
    (1, 'Instruction',        'INSTRUCTION', 'gestionnaire.demo', 1),
    (2, 'Avis technique',     'AVIS',        'validateur.demo',   2),
    (3, 'Visa',               'VISA',        'validateur.demo',   1),
    (4, 'Approbation finale', 'APPROBATION', 'admin.demo',        1),
]


class Command(BaseCommand):
    help = "Crée les comptes de démonstration et le circuit MEI standard pour la soutenance."

    def handle(self, *args, **options):
        # 1. Comptes utilisateurs
        for username, matricule, prenom, nom, role, code_entite, mdp in COMPTES:
            entite = Entite.objects.get(code=code_entite)
            user, created = Utilisateur.objects.get_or_create(
                matricule=matricule,
                defaults={
                    'username': username,
                    'first_name': prenom,
                    'last_name': nom,
                    'role': role,
                    'entite': entite,
                    'is_staff': role == 'ADMIN',
                    'is_superuser': role == 'ADMIN',
                },
            )
            if created:
                user.set_password(mdp)
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f"Compte créé : {username} / {mdp} ({role} — {entite.libelle})"))
            else:
                self.stdout.write(f"Compte déjà présent : {username}")

        # 2. Circuit de validation « MEI standard » (Siège)
        siege = Entite.objects.get(code='SIEGE')
        circuit, created = CircuitValidation.objects.get_or_create(
            nom='Circuit MEI standard',
            entite=siege,
            defaults={'type_document': 'MEI', 'delai_max': 5, 'actif': True},
        )
        if created:
            for ordre, libelle, type_etape, username, delai in ETAPES_MEI:
                EtapeCircuit.objects.create(
                    circuit=circuit,
                    ordre=ordre,
                    libelle=libelle,
                    type_etape=type_etape,
                    validateur=Utilisateur.objects.get(username=username),
                    delai_jours=delai,
                )
            self.stdout.write(self.style.SUCCESS(
                "Circuit « MEI standard » créé avec 4 étapes."))
        else:
            self.stdout.write("Circuit « MEI standard » déjà présent.")

        self.stdout.write(self.style.SUCCESS("Données de démonstration prêtes."))
