from rest_framework import serializers
from .models import CircuitValidation, EtapeCircuit, Workflow, ActionWorkflow
from accounts.serializers import UtilisateurSerializer

class EtapeCircuitSerializer(serializers.ModelSerializer):
    validateur_detail = UtilisateurSerializer(source='validateur', read_only=True)
    class Meta:
        model = EtapeCircuit
        fields = '__all__'

class CircuitValidationSerializer(serializers.ModelSerializer):
    etapes = EtapeCircuitSerializer(many=True, read_only=True)
    class Meta:
        model = CircuitValidation
        fields = '__all__'

class ActionWorkflowSerializer(serializers.ModelSerializer):
    acteur_detail = UtilisateurSerializer(source='acteur', read_only=True)
    class Meta:
        model = ActionWorkflow
        fields = '__all__'

class WorkflowSerializer(serializers.ModelSerializer):
    actions = ActionWorkflowSerializer(many=True, read_only=True)
    etape_courante_detail = EtapeCircuitSerializer(source='etape_courante', read_only=True)
    class Meta:
        model = Workflow
        fields = '__all__'
