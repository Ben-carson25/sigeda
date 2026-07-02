from django.contrib.auth.models import AbstractUser
from django.db import models

class Entite(models.Model):
    TYPE_CHOICES = [
        ('SIEGE', 'Siège'),
        ('REPRESENTATION', 'Représentation nationale'),
        ('DELEGATION', 'Délégation permanente'),
    ]
    code = models.CharField(max_length=10, unique=True)
    libelle = models.CharField(max_length=100)
    type_entite = models.CharField(max_length=20, choices=TYPE_CHOICES)
    pays = models.CharField(max_length=100)
    fuseau_horaire = models.CharField(max_length=50, default='Africa/Dakar')
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Entité"
        ordering = ['libelle']

    def __str__(self):
        return f"{self.libelle} ({self.pays})"

class Utilisateur(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrateur'),
        ('GESTIONNAIRE', 'Gestionnaire documentaire'),
        ('VALIDATEUR', 'Validateur'),
        ('LECTEUR', 'Lecteur'),
    ]
    matricule = models.CharField(max_length=20, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='LECTEUR')
    entite = models.ForeignKey(Entite, on_delete=models.SET_NULL, null=True, blank=True, related_name='utilisateurs')
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Utilisateur"

    def __str__(self):
        return f"{self.get_full_name()} ({self.matricule})"

    def peut_acceder(self, document):
        if self.role == 'ADMIN':
            return True
        return document.entite_emettrice == self.entite
