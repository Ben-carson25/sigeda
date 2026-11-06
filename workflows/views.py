from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import CircuitValidation, Workflow, ActionWorkflow, EtapeCircuit
from .serializers import CircuitValidationSerializer, WorkflowSerializer, ActionWorkflowSerializer
from documents.models import Document, StatutDocument

class CircuitListView(generics.ListAPIView):
    serializer_class = CircuitValidationSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return CircuitValidation.objects.filter(entite=self.request.user.entite, actif=True)

class WorkflowListView(generics.ListAPIView):
    serializer_class = WorkflowSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if user.voit_toutes_entites:
            return Workflow.objects.all()
        return Workflow.objects.filter(document__entite_emettrice=user.entite)

class SoumettreworkflowView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, doc_id):
        try:
            doc = Document.objects.get(pk=doc_id)
            circuit_id = request.data.get('circuit_id')
            circuit = CircuitValidation.objects.get(pk=circuit_id)
        except (Document.DoesNotExist, CircuitValidation.DoesNotExist):
            return Response({'error': 'Document ou circuit non trouvé'}, status=404)
        premiere_etape = circuit.etapes.first()
        wf = Workflow.objects.create(document=doc, circuit=circuit, etape_courante=premiere_etape)
        doc.statut = StatutDocument.EN_VALIDATION
        doc.save()
        return Response(WorkflowSerializer(wf).data, status=201)

class ActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, wf_id):
        try:
            wf = Workflow.objects.get(pk=wf_id)
        except Workflow.DoesNotExist:
            return Response({'error': 'Workflow non trouvé'}, status=404)
        type_action = request.data.get('type_action')
        commentaire = request.data.get('commentaire', '')
        ip = request.META.get('REMOTE_ADDR')
        action = ActionWorkflow.objects.create(
            workflow=wf, etape=wf.etape_courante, acteur=request.user,
            type_action=type_action, commentaire=commentaire, adresse_ip=ip
        )
        if type_action == 'APPROUVE':
            etapes = list(wf.circuit.etapes.order_by('ordre'))
            idx = etapes.index(wf.etape_courante)
            if idx + 1 < len(etapes):
                wf.etape_courante = etapes[idx + 1]
                wf.save()
            else:
                wf.statut = 'APPROUVE'
                wf.date_fin = timezone.now()
                wf.save()
                wf.document.statut = StatutDocument.APPROUVE
                wf.document.save()
        elif type_action == 'REJETE':
            wf.statut = 'REJETE'
            wf.date_fin = timezone.now()
            wf.save()
            wf.document.statut = StatutDocument.REJETE
            wf.document.save()
        elif type_action == 'RENVOYE':
            wf.statut = 'EN_CORRECTION'
            wf.save()
            wf.document.statut = StatutDocument.BROUILLON
            wf.document.save()
        return Response(ActionWorkflowSerializer(action).data, status=201)
