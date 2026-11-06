"""Tests des vues web : profils, décision du validateur, nouvelle version, rapport."""
from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from accounts.models import Entite, Utilisateur
from documents.models import Document, VersionDocument
from workflows.models import ActionWorkflow, CircuitValidation, EtapeCircuit, Workflow


class BaseCase(TestCase):
    def setUp(self):
        self.siege = Entite.objects.get(code='SIEGE')
        self.ci = Entite.objects.get(code='REP-CI')
        mk = lambda u, role, ent=None: Utilisateur.objects.create_user(
            username=u, password='x', matricule=u, role=role, entite=ent or self.siege)
        self.gest = mk('gest', 'GESTIONNAIRE')
        self.valid = mk('valid', 'VALIDATEUR')
        self.agent = mk('agent', 'AGENT')
        self.resp = mk('resp', 'RESPONSABLE')
        self.admin = mk('adm', 'ADMIN')
        self.gest_ci = mk('gest_ci', 'GESTIONNAIRE', self.ci)
        self.doc = Document.objects.create(
            titre='MEI test', type_document='MEI', entite_emettrice=self.siege,
            auteur=self.gest, date_document=date(2026, 7, 1), statut='EN_VALIDATION')
        VersionDocument.objects.create(
            document=self.doc, numero_version='1.0', auteur=self.gest,
            fichier=SimpleUploadedFile('a.pdf', b'%PDF-1.4 test'))
        circuit = CircuitValidation.objects.create(nom='C', entite=self.siege)
        self.etape = EtapeCircuit.objects.create(
            circuit=circuit, ordre=1, libelle='Avis', type_etape='AVIS', validateur=self.valid)
        self.wf = Workflow.objects.create(document=self.doc, circuit=circuit, etape_courante=self.etape)


class ProfilsTest(BaseCase):
    def test_cinq_profils(self):
        roles = {r for r, _ in Utilisateur.ROLE_CHOICES}
        self.assertEqual(roles, {'ADMIN', 'GESTIONNAIRE', 'VALIDATEUR', 'AGENT', 'RESPONSABLE'})

    def test_responsable_vue_transversale(self):
        self.assertTrue(self.resp.peut_acceder(self.doc))
        self.assertFalse(self.gest_ci.peut_acceder(self.doc))

    def test_agent_ne_peut_pas_deposer(self):
        self.client.force_login(self.agent)
        self.assertEqual(self.client.get('/documents/deposer/').status_code, 403)

    def test_gestionnaire_peut_deposer(self):
        self.client.force_login(self.gest)
        self.assertEqual(self.client.get('/documents/deposer/').status_code, 200)

    def test_autre_entite_refusee_sur_document(self):
        self.client.force_login(self.gest_ci)
        self.assertEqual(self.client.get(f'/documents/{self.doc.pk}/').status_code, 403)


class DecisionValidateurTest(BaseCase):
    def decider(self, user, action, commentaire=''):
        self.client.force_login(user)
        return self.client.post(f'/workflows/{self.wf.pk}/',
                                {'type_action': action, 'commentaire': commentaire})

    def test_renvoyer_en_correction(self):
        self.decider(self.valid, 'RENVOYE', 'À corriger')
        self.wf.refresh_from_db(); self.doc.refresh_from_db()
        self.assertEqual(self.wf.statut, 'EN_CORRECTION')
        self.assertEqual(self.doc.statut, 'BROUILLON')
        self.assertTrue(ActionWorkflow.objects.filter(type_action='RENVOYE').exists())

    def test_rejet_sans_commentaire_refuse(self):
        self.decider(self.valid, 'REJETE', '')
        self.wf.refresh_from_db()
        self.assertEqual(self.wf.statut, 'EN_COURS')

    def test_rejet_avec_commentaire(self):
        self.decider(self.valid, 'REJETE', 'Non conforme')
        self.wf.refresh_from_db()
        self.assertEqual(self.wf.statut, 'REJETE')

    def test_autre_utilisateur_ne_peut_pas_decider(self):
        self.assertEqual(self.decider(self.gest, 'APPROUVE').status_code, 403)

    def test_decision_tracee_au_journal(self):
        from workflows.models import JournalAudit
        self.decider(self.valid, 'APPROUVE')
        self.assertTrue(JournalAudit.objects.filter(type_operation='DECISION').exists())


class NouvelleVersionTest(BaseCase):
    def test_nouvelle_version_incremente(self):
        self.client.force_login(self.gest)
        self.client.post(f'/documents/{self.doc.pk}/',
                         {'fichier': SimpleUploadedFile('b.pdf', b'%PDF-1.4 v2')})
        self.assertEqual(self.doc.versions.count(), 2)
        self.assertTrue(self.doc.versions.filter(numero_version='2.0').exists())

    def test_agent_ne_peut_pas_versionner(self):
        self.client.force_login(self.agent)
        r = self.client.post(f'/documents/{self.doc.pk}/',
                             {'fichier': SimpleUploadedFile('b.pdf', b'x')})
        self.assertEqual(r.status_code, 403)

    def test_nouvelle_version_relance_circuit_apres_renvoi(self):
        self.wf.statut = 'EN_CORRECTION'; self.wf.save()
        self.client.force_login(self.gest)
        self.client.post(f'/documents/{self.doc.pk}/',
                         {'fichier': SimpleUploadedFile('b.pdf', b'x')})
        self.wf.refresh_from_db(); self.doc.refresh_from_db()
        self.assertEqual(self.wf.statut, 'EN_COURS')
        self.assertEqual(self.doc.statut, 'EN_VALIDATION')


class SupervisionTest(BaseCase):
    def test_rapport_responsable(self):
        self.client.force_login(self.resp)
        r = self.client.get('/rapport/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('MEI test', r.content.decode('utf-8'))

    def test_rapport_interdit_agent(self):
        self.client.force_login(self.agent)
        self.assertEqual(self.client.get('/rapport/').status_code, 403)

    def test_filtre_entite_tableau_de_bord(self):
        self.client.force_login(self.resp)
        r = self.client.get(f'/?entite={self.ci.pk}')
        self.assertEqual(r.context['stats']['total'], 0)
        r = self.client.get(f'/?entite={self.siege.pk}')
        self.assertEqual(r.context['stats']['total'], 1)
