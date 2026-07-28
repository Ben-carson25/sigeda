"""Tests unitaires du Module 2 : validation des formats de fichiers approuvés."""
from datetime import date

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from accounts.models import Entite, Utilisateur
from documents.models import Document, VersionDocument


class FileExtensionValidatorTest(TestCase):
    """Besoins non fonctionnels d'interopérabilité (mémoire 2.2.5) :
    seuls PDF, DOCX, XLSX, PNG et JPEG sont acceptés au téléversement."""

    def setUp(self):
        siege = Entite.objects.get(code='SIEGE')
        self.gest = Utilisateur.objects.create_user(
            username='gest.doc', password='x', matricule='T-0010',
            role='GESTIONNAIRE', entite=siege)
        self.doc = Document.objects.create(
            titre='MEI de test', type_document='MEI',
            entite_emettrice=siege, auteur=self.gest,
            date_document=date(2026, 7, 1))

    def _version(self, nom_fichier):
        return VersionDocument(
            document=self.doc, numero_version='1.0', auteur=self.gest,
            fichier=SimpleUploadedFile(nom_fichier, b'contenu'))

    def test_pdf_accepte(self):
        self._version('note.pdf').full_clean()  # ne doit pas lever d'exception

    def test_docx_accepte(self):
        self._version('rapport.docx').full_clean()

    def test_executable_rejete(self):
        with self.assertRaises(ValidationError):
            self._version('malware.exe').full_clean()

    def test_script_rejete(self):
        with self.assertRaises(ValidationError):
            self._version('script.sh').full_clean()

    def test_metadonnees_extraites_a_la_sauvegarde(self):
        v = self._version('note.pdf')
        v.full_clean()
        v.save()
        self.assertEqual(v.format_fichier, 'PDF')
        self.assertGreater(v.taille_fichier, 0)
