from rest_framework import serializers
from .models import Utilisateur, Entite

class EntiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entite
        fields = '__all__'

class UtilisateurSerializer(serializers.ModelSerializer):
    entite_detail = EntiteSerializer(source='entite', read_only=True)
    class Meta:
        model = Utilisateur
        fields = ['id','username','first_name','last_name','email','matricule','role','entite','entite_detail','actif']
