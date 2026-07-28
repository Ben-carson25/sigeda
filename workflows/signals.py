"""Journalisation automatique des événements clés dans le JournalAudit.
Garantit l'objectif « zéro validation non tracée » (mémoire, Tableau 1)."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from documents.models import Document, VersionDocument
from .models import ActionWorkflow, Workflow, JournalAudit


@receiver(post_save, sender=ActionWorkflow)
def journaliser_decision(sender, instance, created, **kwargs):
    if created:
        JournalAudit.objects.create(
            acteur=instance.acteur,
            type_operation='DECISION',
            objet_cible=f"{instance.get_type_action_display()} — "
                        f"{instance.workflow.document.titre} (étape : {instance.etape.libelle})",
            adresse_ip=instance.adresse_ip,
        )


@receiver(post_save, sender=Workflow)
def journaliser_soumission(sender, instance, created, **kwargs):
    if created:
        JournalAudit.objects.create(
            acteur=instance.document.auteur,
            type_operation='SOUMISSION',
            objet_cible=f"{instance.document.titre} — circuit : {instance.circuit.nom}",
        )


@receiver(post_save, sender=Document)
def journaliser_depot(sender, instance, created, **kwargs):
    if created:
        JournalAudit.objects.create(
            acteur=instance.auteur,
            type_operation='DEPOT',
            objet_cible=f"{instance.titre} ({instance.get_type_document_display()})",
        )


@receiver(post_save, sender=VersionDocument)
def journaliser_version(sender, instance, created, **kwargs):
    if created and instance.numero_version not in ('1.0', 'v1.0'):
        JournalAudit.objects.create(
            acteur=instance.auteur,
            type_operation='NOUVELLE_VERSION',
            objet_cible=f"{instance.document.titre} — v{instance.numero_version}",
        )
