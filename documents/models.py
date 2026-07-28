from django.db import models
from django.core.validators import FileExtensionValidator
from accounts.models import Utilisateur, Entite
import hashlib, os

class TypeDocument(models.TextChoices):
    MEI            = 'MEI', 'Mémorandum d\'Échange Interne'
    NOTE_SERVICE   = 'NOTE', 'Note de service'
    DECISION       = 'DEC', 'Décision'
    RAPPORT        = 'RAP', 'Rapport'
    CORRESPONDANCE = 'COR', 'Correspondance officielle'
    CR_REUNION     = 'CR', 'Compte rendu de réunion'
    CONTRAT        = 'CTR', 'Document contractuel'

class Classification(models.TextChoices):
    PUBLIC       = 'PUBLIC', 'Public'
    INTERNE      = 'INTERNE', 'Interne'
    CONFIDENTIEL = 'CONF', 'Confidentiel'

class StatutDocument(models.TextChoices):
    BROUILLON     = 'BROUILLON', 'Brouillon'
    EN_VALIDATION = 'EN_VALIDATION', 'En validation'
    APPROUVE      = 'APPROUVE', 'Approuvé'
    REJETE        = 'REJETE', 'Rejeté'
    ARCHIVE       = 'ARCHIVE', 'Archivé'

class Document(models.Model):
    titre              = models.CharField(max_length=255)
    type_document      = models.CharField(max_length=10, choices=TypeDocument.choices, default=TypeDocument.MEI)
    classification     = models.CharField(max_length=10, choices=Classification.choices, default=Classification.INTERNE)
    entite_emettrice   = models.ForeignKey(Entite, on_delete=models.PROTECT, related_name='documents')
    auteur             = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name='documents_crees')
    direction_emettrice = models.CharField(max_length=100, blank=True)
    mots_cles          = models.TextField(blank=True)
    statut             = models.CharField(max_length=20, choices=StatutDocument.choices, default=StatutDocument.BROUILLON)
    date_document      = models.DateField()
    date_creation      = models.DateTimeField(auto_now_add=True)
    date_modification  = models.DateTimeField(auto_now=True)
    checksum           = models.CharField(max_length=64, blank=True)

    class Meta:
        verbose_name = "Document"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.titre} ({self.get_type_document_display()})"

def upload_path(instance, filename):
    return f"documents/{instance.document.id}/v{instance.numero_version}/{filename}"

class VersionDocument(models.Model):
    document        = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    numero_version  = models.CharField(max_length=10)
    fichier         = models.FileField(
        upload_to=upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'docx', 'xlsx', 'png', 'jpeg', 'jpg'],
            message="Format non supporté. Formats approuvés : PDF, DOCX, XLSX, PNG, JPEG.",
        )],
    )
    taille_fichier  = models.BigIntegerField(default=0)
    format_fichier  = models.CharField(max_length=10, blank=True)
    auteur          = models.ForeignKey(Utilisateur, on_delete=models.PROTECT)
    date_creation   = models.DateTimeField(auto_now_add=True)
    commentaire     = models.TextField(blank=True)

    class Meta:
        verbose_name = "Version de document"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.document.titre} — v{self.numero_version}"

    def save(self, *args, **kwargs):
        if self.fichier:
            self.taille_fichier = self.fichier.size
            ext = os.path.splitext(self.fichier.name)[1].lower()
            self.format_fichier = ext.replace('.', '').upper()
        super().save(*args, **kwargs)
