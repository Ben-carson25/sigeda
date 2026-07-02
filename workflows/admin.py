from django.contrib import admin
from .models import CircuitValidation, EtapeCircuit, Workflow, ActionWorkflow

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
