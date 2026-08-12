from django.urls import path
from .views import (
OrganizationCreateView,
OrganizationListView,
OrganizationDetailView,
OrganizationUpdateView,
OrganizationDeleteView,
OrganizationAddMemberView,
OrganizationRemoveMemberView,
OrganizationMemberListView,
OrganizationInvitationCreateView,
MyInvitationListView,
OrganizationInvitationAcceptView,
OrganizationInvitationRejectView,
TeamListCreateView,
TeamDetailView,
TeamMemberListCreateView,
TeamMemberRemoveView,
TeamRepositoryListCreateView,
TeamRepositoryRemoveView,
)

urlpatterns = [
    path('create/', OrganizationCreateView.as_view(), name='organization-create'),
    path('', OrganizationListView.as_view(), name='organization-list'),
    path('invitations/', MyInvitationListView.as_view(), name='organization-my-invitations'),
    path('invitations/<int:pk>/accept/', OrganizationInvitationAcceptView.as_view(), name='organization-invitation-accept'),
    path('invitations/<int:pk>/reject/', OrganizationInvitationRejectView.as_view(), name='organization-invitation-reject'),

    path('<int:pk>/', OrganizationDetailView.as_view(), name='organization-detail'),
    path('<int:pk>/update/', OrganizationUpdateView.as_view(), name='organization-update'),
    path('<int:pk>/delete/', OrganizationDeleteView.as_view(), name='organization-delete'),
    path('<int:pk>/members/', OrganizationAddMemberView.as_view(), name='organization-add-member'),
    path('<int:organization_id>/members/', OrganizationMemberListView.as_view(), name='organization-member-list'),
    path('<int:organization_id>/members/<int:pk>/remove/', OrganizationRemoveMemberView.as_view(), name='organization-remove-member'),

    path('<int:organization_id>/invitations/', OrganizationInvitationCreateView.as_view(), name='organization-invitation-create'),

    path('<int:organization_id>/teams/', TeamListCreateView.as_view(), name='organization-team-list-create'),
    path('<int:organization_id>/teams/<int:pk>/', TeamDetailView.as_view(), name='organization-team-detail'),
    path('<int:organization_id>/teams/<int:team_id>/members/', TeamMemberListCreateView.as_view(), name='organization-team-member-list-create'),
    path('<int:organization_id>/teams/<int:team_id>/members/<int:pk>/remove/', TeamMemberRemoveView.as_view(), name='organization-team-member-remove'),
    path('<int:organization_id>/teams/<int:team_id>/repositories/', TeamRepositoryListCreateView.as_view(), name='organization-team-repository-list-create'),
    path('<int:organization_id>/teams/<int:team_id>/repositories/<int:pk>/remove/', TeamRepositoryRemoveView.as_view(), name='organization-team-repository-remove'),
]