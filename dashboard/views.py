from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
import csv
from django.db.models import Q, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from documents.models import Document, VersionDocument, StatutDocument, TypeDocument
from workflows.models import Workflow, CircuitValidation
from accounts.models import Entite

class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        entites = Entite.objects.filter(actif=True)
        return render(request, 'dashboard/login.html', {'entites': entites})

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        entites = Entite.objects.filter(actif=True)
        return render(request, 'dashboard/login.html', {'entites': entites, 'error': 'Identifiants incorrects'})

class LogoutView(LoginRequiredMixin, View):
    login_url = '/login/'
    def get(self, request):
        logout(request)
        return redirect('login')

class DashboardView(LoginRequiredMixin, View):
    login_url = '/login/'
    def get(self, request):
        user = request.user
        entite_filtre = ''
        if user.voit_toutes_entites:
            docs = Document.objects.all()
            wfs  = Workflow.objects.all()
            entite_filtre = request.GET.get('entite', '')
            if entite_filtre:  # UC-15 : filtrer par entité
                docs = docs.filter(entite_emettrice_id=entite_filtre)
                wfs  = wfs.filter(document__entite_emettrice_id=entite_filtre)
        else:
            docs = Document.objects.filter(entite_emettrice=user.entite)
            wfs  = Workflow.objects.filter(document__entite_emettrice=user.entite)
        stats = {
            'total': docs.count(),
            'en_attente': docs.filter(statut='EN_VALIDATION').count(),
            'approuves': docs.filter(statut='APPROUVE').count(),
            'rejetes': docs.filter(statut='REJETE').count(),
        }
        workflows_en_cours = wfs.filter(statut='EN_COURS').select_related('document','etape_courante')[:5]
        docs_recents = docs.order_by('-date_creation')[:8]
        entites_stats = Entite.objects.filter(actif=True).annotate(nb_docs=Count('documents')).order_by('-nb_docs')[:6]
        return render(request, 'dashboard/dashboard.html', {
            'stats': stats,
            'workflows_en_cours': workflows_en_cours,
            'docs_recents': docs_recents,
            'entites_stats': entites_stats,
            'entites': Entite.objects.filter(actif=True) if user.voit_toutes_entites else [],
            'entite_filtre': entite_filtre,
        })

class DocumentsView(LoginRequiredMixin, View):
    login_url = '/login/'
    def get(self, request):
        user = request.user
        qs = Document.objects.all() if user.voit_toutes_entites else Document.objects.filter(entite_emettrice=user.entite)
        q = request.GET.get('q','')
        type_doc = request.GET.get('type','')
        statut = request.GET.get('statut','')
        if q:
            qs = qs.filter(Q(titre__icontains=q)|Q(mots_cles__icontains=q))
        if type_doc:
            qs = qs.filter(type_document=type_doc)
        if statut:
            qs = qs.filter(statut=statut)
        return render(request, 'dashboard/documents.html', {
            'documents': qs.select_related('auteur','entite_emettrice')[:50],
            'q': q, 'type_doc': type_doc, 'statut': statut,
            'types': TypeDocument.choices,
            'statuts': StatutDocument.choices,
            'total': qs.count(),
        })

class DeposerView(LoginRequiredMixin, View):
    login_url = '/login/'
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.peut_deposer:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        circuits = CircuitValidation.objects.filter(entite=request.user.entite, actif=True)
        return render(request, 'dashboard/deposer.html', {
            'types': TypeDocument.choices,
            'circuits': circuits,
        })

    def post(self, request):
        from documents.models import VersionDocument
        doc = Document(
            titre=request.POST.get('titre'),
            type_document=request.POST.get('type_document'),
            direction_emettrice=request.POST.get('direction_emettrice',''),
            mots_cles=request.POST.get('mots_cles',''),
            date_document=request.POST.get('date_document'),
            classification=request.POST.get('classification','INTERNE'),
            auteur=request.user,
            entite_emettrice=request.user.entite,
            statut='BROUILLON',
        )
        doc.save()
        if request.FILES.get('fichier'):
            VersionDocument.objects.create(
                document=doc,
                numero_version='1.0',
                fichier=request.FILES['fichier'],
                auteur=request.user,
            )
        circuit_id = request.POST.get('circuit_id')
        if circuit_id:
            try:
                circuit = CircuitValidation.objects.get(pk=circuit_id)
                premiere_etape = circuit.etapes.first()
                Workflow.objects.create(document=doc, circuit=circuit, etape_courante=premiere_etape)
                doc.statut = 'EN_VALIDATION'
                doc.save()
            except CircuitValidation.DoesNotExist:
                pass
        return redirect('documents-list')

class DocumentDetailView(LoginRequiredMixin, View):
    login_url = '/login/'
    def get(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)
        if not request.user.peut_acceder(doc):
            raise PermissionDenied
        workflows = doc.workflows.all().select_related('circuit','etape_courante')
        return render(request, 'dashboard/document_detail.html', {
            'doc': doc, 'workflows': workflows,
            'versions': doc.versions.all(),
            'peut_versionner': request.user.peut_deposer and request.user.peut_acceder(doc),
        })

    def post(self, request, pk):
        """UC-06 : déposer une nouvelle version (incrémente le numéro de version)."""
        from django.utils import timezone
        doc = get_object_or_404(Document, pk=pk)
        if not (request.user.peut_deposer and request.user.peut_acceder(doc)):
            raise PermissionDenied
        fichier = request.FILES.get('fichier')
        if fichier:
            VersionDocument.objects.create(
                document=doc,
                numero_version=f"{doc.versions.count() + 1}.0",
                fichier=fichier,
                auteur=request.user,
                commentaire=request.POST.get('commentaire', ''),
            )
            # Document renvoyé en correction : la nouvelle version relance le circuit
            wf = doc.workflows.filter(statut='EN_CORRECTION').first()
            if wf:
                wf.statut = 'EN_COURS'
                wf.etape_courante = wf.circuit.etapes.first()
                wf.date_fin = None
                wf.save()
                doc.statut = 'EN_VALIDATION'
                doc.save()
        return redirect('document-detail', pk=pk)

class WorkflowsView(LoginRequiredMixin, View):
    login_url = '/login/'
    def get(self, request):
        user = request.user
        wfs = Workflow.objects.all() if user.voit_toutes_entites else Workflow.objects.filter(document__entite_emettrice=user.entite)
        wfs = wfs.select_related('document','circuit','etape_courante')
        return render(request, 'dashboard/workflows.html', {'workflows': wfs})

class WorkflowDetailView(LoginRequiredMixin, View):
    login_url = '/login/'
    def get(self, request, pk):
        wf = get_object_or_404(Workflow, pk=pk)
        if not request.user.peut_acceder(wf.document):
            raise PermissionDenied
        etapes = wf.circuit.etapes.all().select_related('validateur')
        actions = wf.actions.all().select_related('acteur','etape')
        return render(request, 'dashboard/workflow_detail.html', {'wf': wf, 'etapes': etapes, 'actions': actions})

    def post(self, request, pk):
        from workflows.models import ActionWorkflow
        from django.utils import timezone
        wf = get_object_or_404(Workflow, pk=pk)
        type_action = request.POST.get('type_action')
        commentaire = request.POST.get('commentaire','').strip()
        # Seul le validateur de l'étape courante peut décider, sur un workflow en cours
        if wf.statut != 'EN_COURS' or not wf.etape_courante or wf.etape_courante.validateur != request.user:
            raise PermissionDenied
        if type_action not in ('APPROUVE', 'REJETE', 'RENVOYE'):
            return redirect('workflow-detail', pk=pk)
        # Le commentaire est obligatoire pour un rejet (mémoire, 2.4.4)
        if type_action == 'REJETE' and not commentaire:
            return redirect('workflow-detail', pk=pk)
        ip = request.META.get('REMOTE_ADDR')
        ActionWorkflow.objects.create(
            workflow=wf, etape=wf.etape_courante, acteur=request.user,
            type_action=type_action, commentaire=commentaire, adresse_ip=ip
        )
        if type_action == 'APPROUVE':
            etapes = list(wf.circuit.etapes.order_by('ordre'))
            idx = next((i for i,e in enumerate(etapes) if e.pk == wf.etape_courante.pk), None)
            if idx is not None and idx + 1 < len(etapes):
                wf.etape_courante = etapes[idx + 1]
                wf.save()
            else:
                wf.statut = 'APPROUVE'
                wf.date_fin = timezone.now()
                wf.save()
                wf.document.statut = 'APPROUVE'
                wf.document.save()
        elif type_action == 'REJETE':
            wf.statut = 'REJETE'
            wf.date_fin = timezone.now()
            wf.save()
            wf.document.statut = 'REJETE'
            wf.document.save()
        elif type_action == 'RENVOYE':  # UC-14 : renvoi au déposant pour correction
            wf.statut = 'EN_CORRECTION'
            wf.save()
            wf.document.statut = 'BROUILLON'
            wf.document.save()
        return redirect('workflow-detail', pk=pk)

class RapportView(LoginRequiredMixin, View):
    """UC-12 : génération et téléchargement du rapport d'activité (CSV)."""
    login_url = '/login/'
    def get(self, request):
        user = request.user
        if user.role not in ('ADMIN', 'RESPONSABLE'):
            raise PermissionDenied
        docs = Document.objects.select_related('entite_emettrice', 'auteur')
        entite = request.GET.get('entite', '')
        if entite:
            docs = docs.filter(entite_emettrice_id=entite)
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="rapport_sigeda.csv"'
        response.write('\ufeff')
        w = csv.writer(response, delimiter=';')
        w.writerow(['Titre', 'Type', 'Entité', 'Auteur', 'Statut', 'Date du document'])
        for d in docs:
            w.writerow([d.titre, d.get_type_document_display(), d.entite_emettrice.libelle,
                        d.auteur.get_full_name(), d.get_statut_display(), d.date_document])
        from workflows.models import JournalAudit
        JournalAudit.enregistrer(user, 'ADMINISTRATION', 'Génération du rapport d\'activité', request)
        return response

class DashboardStatsAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        docs = Document.objects.all() if user.voit_toutes_entites else Document.objects.filter(entite_emettrice=user.entite)
        return Response({
            'total': docs.count(),
            'en_attente': docs.filter(statut='EN_VALIDATION').count(),
            'approuves': docs.filter(statut='APPROUVE').count(),
            'rejetes': docs.filter(statut='REJETE').count(),
        })
