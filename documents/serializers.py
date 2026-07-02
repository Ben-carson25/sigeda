from rest_framework import serializers
from .models import Document, VersionDocument
from accounts.serializers import UtilisateurSerializer, EntiteSerializer

class VersionDocumentSerializer(serializers.ModelSerializer):
    auteur_detail = UtilisateurSerializer(source='auteur', read_only=True)
    class Meta:
        model = VersionDocument
        fields = ['id','numero_version','fichier','taille_fichier','format_fichier','auteur','auteur_detail','date_creation','commentaire']

class DocumentSerializer(serializers.ModelSerializer):
    auteur_detail = UtilisateurSerializer(source='auteur', read_only=True)
    entite_detail = EntiteSerializer(source='entite_emettrice', read_only=True)
    versions = VersionDocumentSerializer(many=True, read_only=True)
    derniere_version = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['id','titre','type_document','classification','entite_emettrice','entite_detail',
                  'auteur','auteur_detail','direction_emettrice','mots_cles','statut',
                  'date_document','date_creation','date_modification','checksum','versions','derniere_version']

    def get_derniere_version(self, obj):
        v = obj.versions.first()
        return VersionDocumentSerializer(v).data if v else None
