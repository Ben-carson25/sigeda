"""Tests unitaires du Module 1 (IAM) : seed des entités et cloisonnement par entité."""
from datetime import date

from django.test import TestCase

from accounts.models import Entite, Utilisateur
from documents.models import Document


class SeedEntitesTest(TestCase):
    """La migration 0002_seed_entites doit peupler exactement les 20 entités ASECNA."""

    def test_vingt_entites_creees(self):
        self.assertEqual(Entite.objects.count(), 20)

    def test_repartition_par_type(self):
        self.assertEqual(Entite.objects.filter(type_entite='SIEGE').count(), 1)
        self.assertEqual(Entite.objects.filter(type_entite='REPRESENTATION').count(), 17)
        self.assertEqual(Entite.objects.filter(type_entite='DELEGATION').count(), 2)

    def test_siege_est_dakar(self):
        siege = Entite.objects.get(type_entite='SIEGE')
        self.assertEqual(siege.pays, 'Sénégal')

    def test_france_couverte_par_delegation_paris(self):
        """La France (19e État membre) est rattachée à la délégation de Paris,
        et non à une représentation nationale."""
        self.assertTrue(Entite.objects.filter(code='DEL-PAR', pays='France').exists())
        self.assertFalse(
            Entite.objects.filter(type_entite='REPRESENTATION', pays='France').exists())


class CloisonnementEntiteTest(TestCase):
    """Règle métier centrale du Module 1 : isolation des données entre entités."""

    def setUp(self):
        self.siege = Entite.objects.get(code='SIEGE')
        self.rep_ci = Entite.objects.get(code='REP-CI')
        self.gest_siege = Utilisateur.objects.create_user(
            username='gest.siege', password='x', matricule='T-0001',
            role='GESTIONNAIRE', entite=self.siege)
        self.gest_ci = Utilisateur.objects.create_user(
            username='gest.ci', password='x', matricule='T-0002',
            role='GESTIONNAIRE', entite=self.rep_ci)
        self.admin = Utilisateur.objects.create_user(
            username='admin.t', password='x', matricule='T-0003',
            role='ADMIN', entite=self.siege)
        self.doc_siege = Document.objects.create(
            titre='Note interne Siège', type_document='NOTE',
            entite_emettrice=self.siege, auteur=self.gest_siege,
            date_document=date(2026, 7, 1))

    def test_acces_meme_entite(self):
        self.assertTrue(self.gest_siege.peut_acceder(self.doc_siege))

    def test_acces_refuse_autre_entite(self):
        self.assertFalse(self.gest_ci.peut_acceder(self.doc_siege))

    def test_admin_acces_transversal(self):
        self.assertTrue(self.admin.peut_acceder(self.doc_siege))
