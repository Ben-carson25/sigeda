from django.contrib import admin
from .models import Document, VersionDocument

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['titre','type_document','statut','entite_emettrice','auteur','date_creation']
    list_filter = ['type_document','statut','entite_emettrice']
    search_fields = ['titre','mots_cles']

@admin.register(VersionDocument)
class VersionDocumentAdmin(admin.ModelAdmin):
    list_display = ['document','numero_version','format_fichier','taille_fichier','auteur','date_creation']
