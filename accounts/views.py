from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Utilisateur, Entite
from .serializers import UtilisateurSerializer, EntiteSerializer

class UtilisateurListView(generics.ListCreateAPIView):
    queryset = Utilisateur.objects.all()
    serializer_class = UtilisateurSerializer
    permission_classes = [permissions.IsAuthenticated]

class EntiteListView(generics.ListAPIView):
    queryset = Entite.objects.filter(actif=True)
    serializer_class = EntiteSerializer
    permission_classes = [permissions.IsAuthenticated]

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        return Response(UtilisateurSerializer(request.user).data)
