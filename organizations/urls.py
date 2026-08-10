from django.urls import path
from .views import (
OrganizationCreateView,
OrganizationListView,
OrganizationDetailView,
OrganizationUpdateView,
OrganizationDeleteView,
OrganizationAddMemberView,
OrganizationRemoveMemberView,
OrganizationMemberListView
)

urlpatterns = [
    path('/create/', OrganizationCreateView.as_view(), name='organization-create'),
    path('/', OrganizationListView.as_view(), name='organization-list'),
    path('<int:pk>/', OrganizationDetailView.as_view(), name='organization-detail'),
    path('<int:pk>/update/', OrganizationUpdateView.as_view(), name='organization-update'),
    path('<int:pk>/delete/', OrganizationDeleteView.as_view(), name='organization-delete'),
    path('<int:pk>/members/', OrganizationAddMemberView.as_view(), name='organization-add-member'),
    path('<int:organization_id>/members/', OrganizationMemberListView.as_view(), name='organization-member-list'),
    path('<int:organization_id>/members/<int:pk>/remove/', OrganizationRemoveMemberView.as_view(), name='organization-remove-member'),

]