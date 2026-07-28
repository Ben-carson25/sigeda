from django.db import models
from accounts.models import Utilisateur, Entite
from documents.models import Document

class CircuitValidation(models.Model):
    nom           = models.CharField(max_length=100)
    entite        = models.ForeignKey(Entite, on_delete=models.CASCADE, related_name='circuits')
    type_document = models.CharField(max_length=10, blank=True)
    delai_max     = models.IntegerField(default=5, help_text="Délai maximum en jours")
    actif         = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Circuit de validation"

    def __str__(self):
        return f"{self.nom} — {self.entite}"

class EtapeCircuit(models.Model):
    TYPE_CHOICES = [
        ('INSTRUCTION', 'Instruction'),
        ('AVIS', 'Avis technique'),
        ('VISA', 'Visa'),
        ('APPROBATION', 'Approbation finale'),
    ]
    circuit     = models.ForeignKey(CircuitValidation, on_delete=models.CASCADE, related_name='etapes')
    ordre       = models.IntegerField()
    libelle     = models.CharField(max_length=100)
    type_etape  = models.CharField(max_length=20, choices=TYPE_CHOICES)
    validateur  = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name='etapes_assignees')
    delai_jours = models.IntegerField(default=2)

    class Meta:
        ordering = ['ordre']
        verbose_name = "Étape de circuit"

    def __str__(self):
        return f"{self.circuit.nom} — Étape {self.ordre} : {self.libelle}"

class Workflow(models.Model):
    STATUT_CHOICES = [
        ('EN_COURS', 'En cours'),
        ('APPROUVE', 'Approuvé'),
        ('REJETE', 'Rejeté'),
        ('EN_CORRECTION', 'En correction'),
    ]
    document      = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='workflows')
    circuit       = models.ForeignKey(CircuitValidation, on_delete=models.PROTECT)
    etape_courante = models.ForeignKey(EtapeCircuit, on_delete=models.SET_NULL, null=True, blank=True)
    statut        = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_COURS')
    date_debut    = models.DateTimeField(auto_now_add=True)
    date_fin      = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Workflow"

    def __str__(self):
        return f"Workflow {self.document.titre} — {self.get_statut_display()}"

class ActionWorkflow(models.Model):
    TYPE_CHOICES = [
        ('APPROUVE', 'Approuvé'),
        ('REJETE', 'Rejeté'),
        ('RENVOYE', 'Renvoyé en correction'),
        ('RELANCE', 'Relancé'),
    ]
    workflow     = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='actions')
    etape        = models.ForeignKey(EtapeCircuit, on_delete=models.PROTECT)
    acteur       = models.ForeignKey(Utilisateur, on_delete=models.PROTECT)
    type_action  = models.CharField(max_length=20, choices=TYPE_CHOICES)
    commentaire  = models.TextField(blank=True)
    date_action  = models.DateTimeField(auto_now_add=True)
    adresse_ip   = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['date_action']
        verbose_name = "Action workflow"

    def __str__(self):
        return f"{self.acteur} — {self.get_type_action_display()} — {self.date_action.strftime('%d/%m/%Y %H:%M')}"


class JournalAudit(models.Model):
    """Journal d'audit transversal, volontairement non cloisonné par entité,
    pour permettre des audits OACI à l'échelle de l'Agence (voir mémoire, 2.3.4)."""
    TYPE_OPERATIONS = [
        ('DEPOT', 'Dépôt de document'),
        ('NOUVELLE_VERSION', 'Dépôt de nouvelle version'),
        ('SOUMISSION', 'Soumission au circuit de validation'),
        ('DECISION', 'Décision de validation'),
        ('CONSULTATION', 'Consultation / prévisualisation'),
        ('CONNEXION', 'Connexion utilisateur'),
        ('ADMINISTRATION', 'Opération d\'administration'),
    ]
    acteur         = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name='operations_audit')
    type_operation = models.CharField(max_length=20, choices=TYPE_OPERATIONS)
    objet_cible    = models.CharField(max_length=255)
    date_operation = models.DateTimeField(auto_now_add=True)
    adresse_ip     = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Journal d'audit"
        verbose_name_plural = "Journal d'audit"
        ordering = ['-date_operation']

    def __str__(self):
        return f"{self.date_operation:%d/%m/%Y %H:%M} — {self.acteur} — {self.get_type_operation_display()}"

    @classmethod
    def enregistrer(cls, acteur, type_operation, objet_cible, request=None):
        """Point d'entrée unique de journalisation (appelable depuis les vues)."""
        adresse_ip = None
        if request is not None:
            adresse_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() \
                or request.META.get('REMOTE_ADDR')
        return cls.objects.create(
            acteur=acteur,
            type_operation=type_operation,
            objet_cible=objet_cible,
            adresse_ip=adresse_ip,
        )
