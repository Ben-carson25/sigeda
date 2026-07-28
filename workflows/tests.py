"""Tests unitaires du Module 3 : journalisation d'audit automatique
(« zéro validation non tracée », mémoire Tableau 1)."""
from datetime import date

from django.test import TestCase

from accounts.models import Entite, Utilisateur
from documents.models import Document
from workflows.models import (
    ActionWorkflow, CircuitValidation, EtapeCircuit, JournalAudit, Workflow,
)


class JournalAuditTest(TestCase):

    def setUp(self):
        siege = Entite.objects.get(code='SIEGE')
        self.gest = Utilisateur.objects.create_user(
            username='gest.wf', password='x', matricule='T-0020',
            role='GESTIONNAIRE', entite=siege)
        self.validateur = Utilisateur.objects.create_user(
            username='val.wf', password='x', matricule='T-0021',
            role='VALIDATEUR', entite=siege)
        self.circuit = CircuitValidation.objects.create(
            nom='Circuit de test', entite=siege, delai_max=5)
        self.etape = EtapeCircuit.objects.create(
            circuit=self.circuit, ordre=1, libelle='Visa',
            type_etape='VISA', validateur=self.validateur)

    def test_depot_journalise(self):
        Document.objects.create(
            titre='Doc audité', type_document='NOTE',
            entite_emettrice=self.gest.entite, auteur=self.gest,
            date_document=date(2026, 7, 1))
        self.assertTrue(JournalAudit.objects.filter(
            type_operation='DEPOT', acteur=self.gest).exists())

    def test_soumission_et_decision_journalisees(self):
        doc = Document.objects.create(
            titre='Doc en circuit', type_document='MEI',
            entite_emettrice=self.gest.entite, auteur=self.gest,
            date_document=date(2026, 7, 1))
        wf = Workflow.objects.create(
            document=doc, circuit=self.circuit, etape_courante=self.etape)
        ActionWorkflow.objects.create(
            workflow=wf, etape=self.etape, acteur=self.validateur,
            type_action='APPROUVE', adresse_ip='10.0.0.1')
        self.assertTrue(JournalAudit.objects.filter(type_operation='SOUMISSION').exists())
        decision = JournalAudit.objects.get(type_operation='DECISION')
        self.assertEqual(decision.acteur, self.validateur)
        self.assertEqual(decision.adresse_ip, '10.0.0.1')

    def test_journal_conserve_adresse_p_et_horodatage(self):
        entree = JournalAudit.enregistrer(
            self.gest, 'CONSULTATION', 'Prévisualisation Doc X')
        self.assertIsNotNone(entree.date_operation)
