from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from repo.models import Repo
from .models import Organization, OrganizationInvitation, OrganizationMember, Team, TeamMember

User = get_user_model()


class OrganizationTestCaseBase(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin_user = User.objects.create_user(email='admin@example.com', password='StrongPass123!')
        self.member_user = User.objects.create_user(email='member@example.com', password='StrongPass123!')
        self.outsider = User.objects.create_user(email='outsider@example.com', password='StrongPass123!')
        self.org = Organization.objects.create(owner=self.admin_user, name='acme')
        OrganizationMember.objects.create(organization=self.org, user=self.admin_user, role='admin')
        OrganizationMember.objects.create(organization=self.org, user=self.member_user, role='member')


class OrganizationInvitationTests(OrganizationTestCaseBase):
    def test_admin_can_invite_user(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(
            f'/api/organizations/{self.org.id}/invitations/', {'invited_user': self.outsider.id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending')

    def test_non_admin_cannot_invite_user(self):
        self.client.force_authenticate(self.member_user)
        response = self.client.post(
            f'/api/organizations/{self.org.id}/invitations/', {'invited_user': self.outsider.id}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_pending_invitation_rejected(self):
        OrganizationInvitation.objects.create(
            organization=self.org, invited_user=self.outsider, invited_by=self.admin_user
        )
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(
            f'/api/organizations/{self.org.id}/invitations/', {'invited_user': self.outsider.id}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_accept_invitation(self):
        invitation = OrganizationInvitation.objects.create(
            organization=self.org, invited_user=self.outsider, invited_by=self.admin_user
        )
        self.client.force_authenticate(self.outsider)
        response = self.client.post(f'/api/organizations/invitations/{invitation.id}/accept/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            OrganizationMember.objects.filter(organization=self.org, user=self.outsider).exists()
        )

    def test_user_can_reject_invitation(self):
        invitation = OrganizationInvitation.objects.create(
            organization=self.org, invited_user=self.outsider, invited_by=self.admin_user
        )
        self.client.force_authenticate(self.outsider)
        response = self.client.post(f'/api/organizations/invitations/{invitation.id}/reject/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            OrganizationMember.objects.filter(organization=self.org, user=self.outsider).exists()
        )

    def test_another_user_cannot_accept_someone_elses_invitation(self):
        invitation = OrganizationInvitation.objects.create(
            organization=self.org, invited_user=self.outsider, invited_by=self.admin_user
        )
        self.client.force_authenticate(self.member_user)
        response = self.client.post(f'/api/organizations/invitations/{invitation.id}/accept/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TeamTests(OrganizationTestCaseBase):
    def test_admin_can_create_team(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(f'/api/organizations/{self.org.id}/teams/', {'name': 'backend'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_member_cannot_create_team(self):
        self.client.force_authenticate(self.member_user)
        response = self.client.post(f'/api/organizations/{self.org.id}/teams/', {'name': 'backend'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_team_name_rejected(self):
        Team.objects.create(organization=self.org, name='backend')
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(f'/api/organizations/{self.org.id}/teams/', {'name': 'backend'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_add_org_member_to_team(self):
        team = Team.objects.create(organization=self.org, name='backend')
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(
            f'/api/organizations/{self.org.id}/teams/{team.id}/members/', {'user': self.member_user.id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_add_non_org_member_to_team(self):
        team = Team.objects.create(organization=self.org, name='backend')
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(
            f'/api/organizations/{self.org.id}/teams/{team.id}/members/', {'user': self.outsider.id}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_remove_team_member(self):
        team = Team.objects.create(organization=self.org, name='backend')
        team_member = TeamMember.objects.create(team=team, user=self.member_user)
        self.client.force_authenticate(self.admin_user)
        response = self.client.delete(
            f'/api/organizations/{self.org.id}/teams/{team.id}/members/{team_member.id}/remove/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_can_add_org_repository_to_team(self):
        team = Team.objects.create(organization=self.org, name='backend')
        repo = Repo.objects.create(organization=self.org, name='org-repo')
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(
            f'/api/organizations/{self.org.id}/teams/{team.id}/repositories/', {'repository': repo.id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_add_foreign_repository_to_team(self):
        team = Team.objects.create(organization=self.org, name='backend')
        other_org = Organization.objects.create(owner=self.admin_user, name='other-org')
        foreign_repo = Repo.objects.create(organization=other_org, name='foreign-repo')
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(
            f'/api/organizations/{self.org.id}/teams/{team.id}/repositories/', {'repository': foreign_repo.id}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_admin_cannot_delete_team(self):
        team = Team.objects.create(organization=self.org, name='backend')
        self.client.force_authenticate(self.member_user)
        response = self.client.delete(f'/api/organizations/{self.org.id}/teams/{team.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
