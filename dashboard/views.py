from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
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
        if user.role == 'ADMIN':
            docs = Document.objects.all()
            wfs  = Workflow.objects.all()
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
        })

class DocumentsView(LoginRequiredMixin, View):
    login_url = '/login/'
    def get(self, request):
        user = request.user
        qs = Document.objects.all() if user.role == 'ADMIN' else Document.objects.filter(entite_emettrice=user.entite)
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
        workflows = doc.workflows.all().select_related('circuit','etape_courante')
        return render(request, 'dashboard/document_detail.html', {'doc': doc, 'workflows': workflows})

class WorkflowsView(LoginRequiredMixin, View):
    login_url = '/login/'
    def get(self, request):
        user = request.user
        wfs = Workflow.objects.filter(document__entite_emettrice=user.entite).select_related('document','circuit','etape_courante')
        return render(request, 'dashboard/workflows.html', {'workflows': wfs})

class WorkflowDetailView(LoginRequiredMixin, View):
    login_url = '/login/'
    def get(self, request, pk):
        wf = get_object_or_404(Workflow, pk=pk)
        etapes = wf.circuit.etapes.all().select_related('validateur')
        actions = wf.actions.all().select_related('acteur','etape')
        return render(request, 'dashboard/workflow_detail.html', {'wf': wf, 'etapes': etapes, 'actions': actions})

    def post(self, request, pk):
        from workflows.models import ActionWorkflow
        from django.utils import timezone
        wf = get_object_or_404(Workflow, pk=pk)
        type_action = request.POST.get('type_action')
        commentaire = request.POST.get('commentaire','')
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
        return redirect('workflow-detail', pk=pk)

class DashboardStatsAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        docs = Document.objects.all() if user.role == 'ADMIN' else Document.objects.filter(entite_emettrice=user.entite)
        return Response({
            'total': docs.count(),
            'en_attente': docs.filter(statut='EN_VALIDATION').count(),
            'approuves': docs.filter(statut='APPROUVE').count(),
            'rejetes': docs.filter(statut='REJETE').count(),
        })
