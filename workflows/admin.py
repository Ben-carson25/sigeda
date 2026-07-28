from django.contrib import admin
from .models import CircuitValidation, EtapeCircuit, Workflow, ActionWorkflow, JournalAudit

class EtapeInline(admin.TabularInline):
    model = EtapeCircuit
    extra = 1

@admin.register(CircuitValidation)
class CircuitAdmin(admin.ModelAdmin):
    list_display = ['nom','entite','delai_max','actif']
    inlines = [EtapeInline]

@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ['document','circuit','statut','etape_courante','date_debut']
    list_filter = ['statut']

@admin.register(ActionWorkflow)
class ActionAdmin(admin.ModelAdmin):
    list_display = ['workflow','etape','acteur','type_action','date_action']

@admin.register(JournalAudit)
class JournalAuditAdmin(admin.ModelAdmin):
    """Journal d'audit en lecture seule : les entrées ne se modifient ni ne se suppriment
    (exigence de traçabilité OACI)."""
    list_display = ['date_operation', 'acteur', 'type_operation', 'objet_cible', 'adresse_ip']
    list_filter = ['type_operation', 'date_operation']
    search_fields = ['objet_cible', 'acteur__matricule', 'acteur__username']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
