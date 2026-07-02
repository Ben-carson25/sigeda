from django.urls import path
from . import views
urlpatterns = [
    path('', views.DocumentListView.as_view(), name='documents'),
    path('<int:pk>/', views.DocumentDetailView.as_view(), name='document-detail'),
    path('<int:doc_id>/versions/', views.VersionCreateView.as_view(), name='version-create'),
]
