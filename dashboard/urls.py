from django.urls import path
from . import views
urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('documents/', views.DocumentsView.as_view(), name='documents-list'),
    path('documents/deposer/', views.DeposerView.as_view(), name='deposer'),
    path('documents/<int:pk>/', views.DocumentDetailView.as_view(), name='document-detail'),
    path('workflows/', views.WorkflowsView.as_view(), name='workflows-list'),
    path('workflows/<int:pk>/', views.WorkflowDetailView.as_view(), name='workflow-detail'),
    path('api/dashboard/stats/', views.DashboardStatsAPI.as_view(), name='dashboard-stats'),
]
