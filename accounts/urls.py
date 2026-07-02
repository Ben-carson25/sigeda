from django.urls import path
from . import views
urlpatterns = [
    path('utilisateurs/', views.UtilisateurListView.as_view(), name='utilisateurs'),
    path('entites/', views.EntiteListView.as_view(), name='entites'),
    path('me/', views.MeView.as_view(), name='me'),
]
