from django.urls import path
from . import views
urlpatterns = [
    path('circuits/', views.CircuitListView.as_view(), name='circuits'),
    path('', views.WorkflowListView.as_view(), name='workflows'),
    path('soumettre/<int:doc_id>/', views.SoumettreworkflowView.as_view(), name='soumettre'),
    path('<int:wf_id>/action/', views.ActionView.as_view(), name='action'),
]
