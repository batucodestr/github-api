from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from organizations.models import Organization, OrganizationMember
from .models import Branch, Commit, Issue, PullRequest, Repo, Star

User = get_user_model()


class RepoTestCaseBase(APITestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(email='owner@example.com', password='StrongPass123!')
        self.other_user = User.objects.create_user(email='other@example.com', password='StrongPass123!')
        self.repo = Repo.objects.create(owner=self.owner, name='demo-repo', visibility='public')
        self.private_repo = Repo.objects.create(owner=self.owner, name='secret-repo', visibility='private')
        self.branch = Branch.objects.create(repository=self.repo, name='main', is_default=True)


class StarTests(RepoTestCaseBase):
    def test_authenticated_user_can_star_repo(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.post(f'/api/repos/{self.repo.id}/star/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Star.objects.filter(user=self.other_user, repository=self.repo).count(), 1)

    def test_duplicate_star_rejected(self):
        Star.objects.create(user=self.other_user, repository=self.repo)
        self.client.force_authenticate(self.other_user)
        response = self.client.post(f'/api/repos/{self.repo.id}/star/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_user_cannot_star(self):
        response = self.client.post(f'/api/repos/{self.repo.id}/star/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unstar_removes_star(self):
        Star.objects.create(user=self.other_user, repository=self.repo)
        self.client.force_authenticate(self.other_user)
        response = self.client.delete(f'/api/repos/{self.repo.id}/unstar/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Star.objects.filter(user=self.other_user, repository=self.repo).exists())

    def test_repo_detail_shows_stars_count(self):
        Star.objects.create(user=self.other_user, repository=self.repo)
        response = self.client.get(f'/api/repos/{self.repo.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['stars_count'], 1)

    def test_user_can_list_starred_repos(self):
        Star.objects.create(user=self.other_user, repository=self.repo)
        self.client.force_authenticate(self.other_user)
        response = self.client.get('/api/repos/starred/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_cannot_star_private_repo_without_access(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.post(f'/api/repos/{self.private_repo.id}/star/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ForkTests(RepoTestCaseBase):
    def test_authenticated_user_can_fork_public_repo(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.post(f'/api/repos/{self.repo.id}/fork/', {'name': 'demo-repo-fork'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        fork = Repo.objects.get(pk=response.data['id'])
        self.assertTrue(fork.is_fork)
        self.assertEqual(fork.fork_parent_id, self.repo.id)
        self.assertEqual(fork.owner, self.other_user)

    def test_fork_creates_default_branch(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.post(f'/api/repos/{self.repo.id}/fork/')
        fork = Repo.objects.get(pk=response.data['id'])
        self.assertTrue(Branch.objects.filter(repository=fork, is_default=True).exists())

    def test_cannot_fork_private_repo_without_access(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.post(f'/api/repos/{self.private_repo.id}/fork/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_fork_into_organization_without_membership(self):
        org = Organization.objects.create(owner=self.owner, name='other-org')
        self.client.force_authenticate(self.other_user)
        response = self.client.post(f'/api/repos/{self.repo.id}/fork/', {'organization': org.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_forks_of_repository(self):
        Repo.objects.create(owner=self.other_user, name='demo-repo', is_fork=True, fork_parent=self.repo)
        response = self.client.get(f'/api/repos/{self.repo.id}/forks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)


class BranchTests(RepoTestCaseBase):
    def test_owner_can_create_branch(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(f'/api/repos/{self.repo.id}/branches/', {'name': 'develop'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_non_owner_cannot_create_branch(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.post(f'/api/repos/{self.repo.id}/branches/', {'name': 'develop'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_branch_name_rejected(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(f'/api/repos/{self.repo.id}/branches/', {'name': 'main'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_default_branch_cannot_be_deleted(self):
        self.client.force_authenticate(self.owner)
        response = self.client.delete(f'/api/repos/{self.repo.id}/branches/{self.branch.id}/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_default_branch(self):
        develop = Branch.objects.create(repository=self.repo, name='develop')
        self.client.force_authenticate(self.owner)
        response = self.client.post(f'/api/repos/{self.repo.id}/branches/{develop.id}/set-default/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.repo.refresh_from_db()
        self.assertEqual(self.repo.default_branch, 'develop')
        self.branch.refresh_from_db()
        self.assertFalse(self.branch.is_default)


class CommitTests(RepoTestCaseBase):
    def test_owner_can_create_commit(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            f'/api/repos/{self.repo.id}/commits/',
            {'branch': self.branch.id, 'message': 'initial commit'},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['hash'])

    def test_non_member_cannot_create_commit(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.post(
            f'/api/repos/{self.repo.id}/commits/',
            {'branch': self.branch.id, 'message': 'hack'},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_branch_from_other_repo_rejected(self):
        other_repo = Repo.objects.create(owner=self.owner, name='other-repo')
        other_branch = Branch.objects.create(repository=other_repo, name='main', is_default=True)
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            f'/api/repos/{self.repo.id}/commits/',
            {'branch': other_branch.id, 'message': 'wrong branch'},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_branch_commit_history(self):
        Commit.objects.create(repository=self.repo, branch=self.branch, author=self.owner, message='c1')
        response = self.client.get(f'/api/repos/{self.repo.id}/branches/{self.branch.id}/commits/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)


class IssueTests(RepoTestCaseBase):
    def test_authenticated_user_can_create_issue(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.post(f'/api/repos/{self.repo.id}/issues/', {'title': 'Bug found', 'body': 'details'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'open')

    def test_author_can_close_issue(self):
        issue = Issue.objects.create(repository=self.repo, author=self.other_user, title='Bug')
        self.client.force_authenticate(self.other_user)
        response = self.client.post(f'/api/repos/{self.repo.id}/issues/{issue.id}/close/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'closed')

    def test_non_author_non_maintainer_cannot_close_issue(self):
        issue = Issue.objects.create(repository=self.repo, author=self.owner, title='Bug')
        stranger = User.objects.create_user(email='stranger@example.com', password='StrongPass123!')
        self.client.force_authenticate(stranger)
        response = self.client.post(f'/api/repos/{self.repo.id}/issues/{issue.id}/close/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_maintainer_can_reopen_issue(self):
        issue = Issue.objects.create(repository=self.repo, author=self.other_user, title='Bug', status='closed')
        self.client.force_authenticate(self.owner)
        response = self.client.post(f'/api/repos/{self.repo.id}/issues/{issue.id}/reopen/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'open')

    def test_add_comment_to_issue(self):
        issue = Issue.objects.create(repository=self.repo, author=self.owner, title='Bug')
        self.client.force_authenticate(self.other_user)
        response = self.client.post(
            f'/api/repos/{self.repo.id}/issues/{issue.id}/comments/', {'body': 'I can reproduce this'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_delete_issue_by_non_author_forbidden(self):
        issue = Issue.objects.create(repository=self.repo, author=self.other_user, title='Bug')
        stranger = User.objects.create_user(email='stranger2@example.com', password='StrongPass123!')
        self.client.force_authenticate(stranger)
        response = self.client.delete(f'/api/repos/{self.repo.id}/issues/{issue.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PullRequestTests(RepoTestCaseBase):
    def setUp(self):
        super().setUp()
        self.feature_branch = Branch.objects.create(repository=self.repo, name='feature')

    def test_create_pull_request(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.post(
            f'/api/repos/{self.repo.id}/pulls/',
            {
                'source_branch': self.feature_branch.id,
                'target_branch': self.branch.id,
                'title': 'Add feature',
                'body': 'This adds a feature',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'open')

    def test_pull_request_rejects_branches_from_different_repos(self):
        other_repo = Repo.objects.create(owner=self.owner, name='other-repo2')
        other_branch = Branch.objects.create(repository=other_repo, name='main', is_default=True)
        self.client.force_authenticate(self.other_user)
        response = self.client.post(
            f'/api/repos/{self.repo.id}/pulls/',
            {
                'source_branch': other_branch.id,
                'target_branch': self.branch.id,
                'title': 'Invalid PR',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_can_close_pull_request(self):
        pr = PullRequest.objects.create(
            repository=self.repo,
            author=self.other_user,
            source_branch=self.feature_branch,
            target_branch=self.branch,
            title='Add feature',
        )
        self.client.force_authenticate(self.owner)
        response = self.client.post(f'/api/repos/{self.repo.id}/pulls/{pr.id}/close/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'closed')

    def test_merged_pull_request_cannot_be_reopened(self):
        pr = PullRequest.objects.create(
            repository=self.repo,
            author=self.other_user,
            source_branch=self.feature_branch,
            target_branch=self.branch,
            title='Add feature',
            status='merged',
        )
        self.client.force_authenticate(self.owner)
        response = self.client.post(f'/api/repos/{self.repo.id}/pulls/{pr.id}/reopen/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RepoVisibilityAndSearchTests(RepoTestCaseBase):
    def test_private_repo_hidden_from_repo_list(self):
        response = self.client.get('/api/repos/')
        names = [item['name'] for item in response.data['results']]
        self.assertIn('demo-repo', names)
        self.assertNotIn('secret-repo', names)

    def test_owner_sees_own_private_repo_in_list(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get('/api/repos/')
        names = [item['name'] for item in response.data['results']]
        self.assertIn('secret-repo', names)

    def test_private_repo_detail_returns_404_for_stranger(self):
        response = self.client.get(f'/api/repos/{self.private_repo.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_search_repositories_by_name(self):
        Repo.objects.create(owner=self.owner, name='django-project', description='A django app')
        response = self.client.get('/api/search/repositories/?q=django')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item['name'] for item in response.data['results']]
        self.assertIn('django-project', names)

    def test_filter_repos_by_visibility(self):
        response = self.client.get('/api/repos/?visibility=public')
        for item in response.data['results']:
            self.assertEqual(item['id'] and Repo.objects.get(pk=item['id']).visibility, 'public')

    def test_ordering_by_name(self):
        response = self.client.get('/api/repos/?ordering=name')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
