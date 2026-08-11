from django.urls import path
from .views import (
    RepoCreateView,
    RepoOrganizationCreateView,
    RepoListView,
    RepoDetailView,
    RepoUpdateView,
    RepoDeleteView,
    RepoAdminListView,
    RepoAdminDetailView,
    RepoAdminUpdateView,
    RepoAdminDeleteView,
    RepoAdminCreateView
)

urlpatterns = [
    path('', RepoListView.as_view(), name='repo_list'),
    path('create/', RepoCreateView.as_view(), name='repo_create'),
    path('organizations/<int:organization_id>/create/', RepoOrganizationCreateView.as_view(), name='repo_organization_create'),
    path('<int:pk>/', RepoDetailView.as_view(), name='repo_detail'),
    path('<int:pk>/update/', RepoUpdateView.as_view(), name='repo_update'),
    path('<int:pk>/delete/', RepoDeleteView.as_view(), name='repo_delete'),
    path('admin/', RepoAdminListView.as_view(), name='repo_admin_list'),
    path('admin/<int:pk>/', RepoAdminDetailView.as_view(), name='repo_admin_detail'),
    path('admin/<int:pk>/update/', RepoAdminUpdateView.as_view(), name='repo_admin_update'),
    path('admin/<int:pk>/delete/', RepoAdminDeleteView.as_view(), name='repo_admin_delete'),
    path('admin/create/', RepoAdminCreateView.as_view(), name='repo_admin_create'),
]