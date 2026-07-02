from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Entite

@admin.register(Entite)
class EntiteAdmin(admin.ModelAdmin):
    list_display = ['libelle','type_entite','pays','actif']
    list_filter = ['type_entite','actif']

@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ['username','first_name','last_name','matricule','role','entite','actif']
    list_filter = ['role','entite','actif']
    fieldsets = UserAdmin.fieldsets + (
        ('SIGEDA', {'fields': ('matricule','role','entite','actif')}),
    )
