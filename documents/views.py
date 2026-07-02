from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from .models import Document, VersionDocument
from .serializers import DocumentSerializer, VersionDocumentSerializer
from accounts.models import Utilisateur
import hashlib

class DocumentListView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Document.objects.all()
        if user.role != 'ADMIN':
            qs = qs.filter(entite_emettrice=user.entite)
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(Q(titre__icontains=q)|Q(mots_cles__icontains=q)|Q(direction_emettrice__icontains=q))
        type_doc = self.request.query_params.get('type')
        if type_doc:
            qs = qs.filter(type_document=type_doc)
        statut = self.request.query_params.get('statut')
        if statut:
            qs = qs.filter(statut=statut)
        return qs

    def perform_create(self, serializer):
        serializer.save(auteur=self.request.user, entite_emettrice=self.request.user.entite)

class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

class VersionCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, doc_id):
        try:
            doc = Document.objects.get(pk=doc_id)
        except Document.DoesNotExist:
            return Response({'error': 'Document non trouvé'}, status=404)
        nb = doc.versions.count()
        version = VersionDocument(
            document=doc,
            numero_version=f"{nb+1}.0",
            fichier=request.FILES.get('fichier'),
            auteur=request.user,
            commentaire=request.data.get('commentaire','')
        )
        version.save()
        return Response(VersionDocumentSerializer(version).data, status=201)
