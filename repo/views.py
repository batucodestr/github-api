from django.core.cache import cache
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import Organization
from organizations.permissions import IsOrganizationMember

from .models import Branch, Commit, Issue, IssueComment, PullRequest, PullRequestComment, Repo, Star
from .permissions import can_view_repo, has_repo_write_access
from .serializers import (
    BranchSerializer,
    CommitSerializer,
    IssueCommentSerializer,
    IssueDetailSerializer,
    IssueSerializer,
    PullRequestCommentSerializer,
    PullRequestDetailSerializer,
    PullRequestSerializer,
    RepoDetailSerializer,
    RepoSerializer,
    StarredRepoSerializer,
    StarSerializer,
)

# Görünümler burada oluşturulur.
 
def _visible_repos_queryset(user, base_queryset=None):
    qs = base_queryset if base_queryset is not None else Repo.objects.all()
    if user and user.is_authenticated:
        qs = qs.filter(
            Q(visibility='public') | Q(owner=user) | Q(organization__members__user=user)
        )
    else:
        qs = qs.filter(visibility='public')
    return qs.distinct().order_by('-created_at')


def _create_default_branch(repo):
    Branch.objects.get_or_create(
        repository=repo,
        name=repo.default_branch,
        defaults={'is_default': True},
    )


@extend_schema(tags=['Depolar'], summary='Kimliği doğrulanmış kullanıcının sahibi olduğu yeni depo oluşturur')
class RepoCreateView(generics.CreateAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        repo = serializer.save(owner=self.request.user)
        _create_default_branch(repo)


@extend_schema(tags=['Depolar'], summary='Bir organizasyon içinde yeni depo oluşturur')
class RepoOrganizationCreateView(generics.CreateAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def perform_create(self, serializer):
        organization = get_object_or_404(Organization, pk=self.kwargs['organization_id'])
        repo = serializer.save(owner=None, organization=organization)
        _create_default_branch(repo)


# Repoları herkes görebilir ama sadece görünürlük kuralına uyanlar görüntülenir.
@extend_schema(tags=['Depolar'], summary='Depoları listeler (filtreleme, sıralama destekli)')
class RepoListView(generics.ListAPIView):
    serializer_class = RepoSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['visibility', 'owner', 'organization', 'is_fork']
    ordering_fields = ['name', 'created_at', 'updated_at', 'stars_count']
    ordering = ['-created_at']

    def get_queryset(self):
        return _visible_repos_queryset(self.request.user).annotate(stars_count=Count('stars', distinct=True))


@extend_schema(tags=['Depolar'], summary='GitHub tarzı depo arama (isim ve açıklamada arama yapar)')
class RepositorySearchView(generics.ListAPIView):
    serializer_class = RepoSerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at', 'stars_count']
    ordering = ['-created_at']

    def get_queryset(self):
        return _visible_repos_queryset(self.request.user).annotate(stars_count=Count('stars', distinct=True))


@extend_schema(tags=['Depolar'], summary='Bir depoyu getirir')
class RepoDetailView(generics.RetrieveAPIView):
    serializer_class = RepoDetailSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Repo.objects.all()

    def get_object(self):
        obj = super().get_object()
        if not can_view_repo(self.request.user, obj):
            raise Http404
        return obj

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        cache_key = f'repo_detail_{instance.pk}'
        if instance.visibility == 'public':
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return Response(cached_data)
        serializer = self.get_serializer(instance)
        if instance.visibility == 'public':
            cache.set(cache_key, serializer.data, 60)
        return Response(serializer.data)


@extend_schema(tags=['Depolar'], summary='Kimliği doğrulanmış kullanıcının sahibi olduğu depoyu günceller')
class RepoUpdateView(generics.UpdateAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Repo.objects.filter(owner=self.request.user)

@extend_schema(tags=['Depolar'], summary='Kimliği doğrulanmış kullanıcının sahibi olduğu depoyu siler')
class RepoDeleteView(generics.DestroyAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Repo.objects.filter(owner=self.request.user)


# Yönetici işlemleri

@extend_schema(tags=['Depolar'], summary='Yönetici için tüm depoları listeler')
class RepoAdminListView(generics.ListAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAdminUser]

@extend_schema(tags=['Depolar'], summary='Yönetici için bir depoyu getirir, günceller veya siler')
class RepoAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAdminUser]

@extend_schema(tags=['Depolar'], summary='Yönetici için herhangi bir depoyu günceller')
class RepoAdminUpdateView(generics.UpdateAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAdminUser]

@extend_schema(tags=['Depolar'], summary='Yönetici için herhangi bir depoyu siler')
class RepoAdminDeleteView(generics.DestroyAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAdminUser]

@extend_schema(tags=['Depolar'], summary='Yönetici için yeni bir depo oluşturur')
class RepoAdminCreateView(generics.CreateAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAdminUser]


# --- Stars ---

@extend_schema(tags=['Depolar'], summary='Bir depoyu yıldızlar', request=None)
class RepoStarView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StarSerializer

    def post(self, request, pk):
        repo = get_object_or_404(Repo, pk=pk)
        if not can_view_repo(request.user, repo):
            raise Http404
        if Star.objects.filter(user=request.user, repository=repo).exists():
            raise ValidationError({'detail': 'Bu depoyu zaten yıldızladınız.'})
        star = Star.objects.create(user=request.user, repository=repo)
        return Response(StarSerializer(star).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Depolar'], summary='Bir depodan yıldızı kaldırır', request=None)
class RepoUnstarView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StarSerializer

    def delete(self, request, pk):
        repo = get_object_or_404(Repo, pk=pk)
        star = Star.objects.filter(user=request.user, repository=repo).first()
        if not star:
            raise ValidationError({'detail': 'Bu depoyu yıldızlamadınız.'})
        star.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['Depolar'], summary='Bir depoyu yıldızlayan kullanıcıları listeler')
class RepoStargazersListView(generics.ListAPIView):
    serializer_class = StarSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Star.objects.none()
        repo = get_object_or_404(Repo, pk=self.kwargs['pk'])
        if not can_view_repo(self.request.user, repo):
            raise Http404
        return Star.objects.filter(repository=repo)


@extend_schema(tags=['Depolar'], summary='Kimliği doğrulanmış kullanıcının yıldızladığı depoları listeler')
class UserStarredReposListView(generics.ListAPIView):
    serializer_class = StarredRepoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Star.objects.none()
        return Star.objects.filter(user=self.request.user)


# --- Forks ---

@extend_schema(tags=['Depolar'], summary='Bir depoyu fork\'lar', request=None)
class RepoForkView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RepoDetailSerializer

    def post(self, request, pk):
        parent = get_object_or_404(Repo, pk=pk)
        if not can_view_repo(request.user, parent):
            raise Http404

        organization_id = request.data.get('organization')
        organization = None
        if organization_id:
            organization = get_object_or_404(Organization, pk=organization_id)
            if not organization.members.filter(user=request.user).exists():
                raise PermissionDenied('Bu organizasyon adına fork oluşturamazsınız.')
            owner = None
        else:
            owner = request.user

        fork = Repo.objects.create(
            owner=owner,
            organization=organization,
            name=request.data.get('name') or parent.name,
            description=parent.description,
            visibility=parent.visibility,
            default_branch=parent.default_branch,
            license=parent.license,
            is_fork=True,
            fork_parent=parent,
        )
        _create_default_branch(fork)
        return Response(RepoDetailSerializer(fork).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Depolar'], summary='Bir deponun fork\'larını listeler')
class RepoForksListView(generics.ListAPIView):
    serializer_class = RepoSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Repo.objects.none()
        parent = get_object_or_404(Repo, pk=self.kwargs['pk'])
        if not can_view_repo(self.request.user, parent):
            raise Http404
        return _visible_repos_queryset(self.request.user, parent.forks.all())


# --- Branches ---

def _get_accessible_repo(request, pk):
    repo = get_object_or_404(Repo, pk=pk)
    if not can_view_repo(request.user, repo):
        raise Http404
    return repo


@extend_schema(tags=['Depolar'], summary='Bir deponun dallarını listeler veya yeni dal oluşturur')
class BranchListCreateView(generics.ListCreateAPIView):
    serializer_class = BranchSerializer
    permission_classes = [AllowAny]

    def get_repo(self):
        return _get_accessible_repo(self.request, self.kwargs['pk'])

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Branch.objects.none()
        return Branch.objects.filter(repository=self.get_repo())

    def perform_create(self, serializer):
        repo = self.get_repo()
        if not has_repo_write_access(self.request.user, repo):
            raise PermissionDenied('Bu depoda dal oluşturma yetkiniz yok.')
        if Branch.objects.filter(repository=repo, name=serializer.validated_data['name']).exists():
            raise ValidationError({'name': 'Bu isimde bir dal zaten mevcut.'})
        serializer.save(repository=repo)


@extend_schema(tags=['Depolar'], summary='Bir dalın detayını getirir veya siler')
class BranchDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = BranchSerializer
    permission_classes = [AllowAny]
    lookup_url_kwarg = 'branch_pk'

    def get_queryset(self):
        repo = _get_accessible_repo(self.request, self.kwargs['pk'])
        return Branch.objects.filter(repository=repo)

    def perform_destroy(self, instance):
        if not has_repo_write_access(self.request.user, instance.repository):
            raise PermissionDenied('Bu dalı silme yetkiniz yok.')
        if instance.is_default:
            raise ValidationError({'detail': 'Varsayılan dal silinemez.'})
        instance.delete()


@extend_schema(tags=['Depolar'], summary='Bir dalı deponun varsayılan dalı yapar', request=None)
class BranchSetDefaultView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BranchSerializer

    def post(self, request, pk, branch_pk):
        repo = get_object_or_404(Repo, pk=pk)
        if not has_repo_write_access(request.user, repo):
            raise PermissionDenied('Bu depoda varsayılan dalı değiştirme yetkiniz yok.')
        branch = get_object_or_404(Branch, pk=branch_pk, repository=repo)

        Branch.objects.filter(repository=repo, is_default=True).exclude(pk=branch.pk).update(is_default=False)
        branch.is_default = True
        branch.save(update_fields=['is_default'])
        repo.default_branch = branch.name
        repo.save(update_fields=['default_branch'])
        return Response(BranchSerializer(branch).data)


# --- Commits ---

@extend_schema(tags=['Depolar'], summary='Bir deponun commit geçmişini listeler veya yeni commit oluşturur')
class RepoCommitListCreateView(generics.ListCreateAPIView):
    serializer_class = CommitSerializer
    permission_classes = [AllowAny]

    def get_repo(self):
        return _get_accessible_repo(self.request, self.kwargs['pk'])

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Commit.objects.none()
        return Commit.objects.filter(repository=self.get_repo())

    def perform_create(self, serializer):
        repo = self.get_repo()
        if not has_repo_write_access(self.request.user, repo):
            raise PermissionDenied('Bu depoya commit oluşturma yetkiniz yok.')
        branch = serializer.validated_data.get('branch')
        if branch.repository_id != repo.id:
            raise ValidationError({'branch': 'Dal bu depoya ait değil.'})
        serializer.save(repository=repo, author=self.request.user)


@extend_schema(tags=['Depolar'], summary='Bir dalın commit geçmişini listeler')
class BranchCommitListView(generics.ListAPIView):
    serializer_class = CommitSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Commit.objects.none()
        repo = _get_accessible_repo(self.request, self.kwargs['pk'])
        branch = get_object_or_404(Branch, pk=self.kwargs['branch_pk'], repository=repo)
        return Commit.objects.filter(branch=branch)


@extend_schema(tags=['Depolar'], summary='Bir commit\'in detayını getirir')
class CommitDetailView(generics.RetrieveAPIView):
    serializer_class = CommitSerializer
    permission_classes = [AllowAny]
    lookup_url_kwarg = 'commit_pk'

    def get_queryset(self):
        repo = _get_accessible_repo(self.request, self.kwargs['pk'])
        return Commit.objects.filter(repository=repo)


# --- Issues ---

@extend_schema(tags=['Depolar'], summary='Bir deponun issue\'larını listeler veya yeni issue oluşturur')
class IssueListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

    def get_serializer_class(self):
        return IssueSerializer

    def get_repo(self):
        return _get_accessible_repo(self.request, self.kwargs['pk'])

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Issue.objects.none()
        return Issue.objects.filter(repository=self.get_repo())

    def perform_create(self, serializer):
        serializer.save(repository=self.get_repo(), author=self.request.user)


@extend_schema(tags=['Depolar'], summary='Bir issue\'nun detayını getirir, günceller veya siler')
class IssueDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = IssueDetailSerializer
    permission_classes = [AllowAny]
    lookup_url_kwarg = 'issue_pk'

    def get_queryset(self):
        repo = _get_accessible_repo(self.request, self.kwargs['pk'])
        return Issue.objects.filter(repository=repo)

    def check_write_permission(self, issue):
        user = self.request.user
        if not (user.is_authenticated and (user == issue.author or has_repo_write_access(user, issue.repository))):
            raise PermissionDenied('Bu issue üzerinde işlem yapma yetkiniz yok.')

    def perform_update(self, serializer):
        self.check_write_permission(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self.check_write_permission(instance)
        instance.delete()


@extend_schema(tags=['Depolar'], summary='Bir issue\'yu kapatır', request=None)
class IssueCloseView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = IssueSerializer

    def post(self, request, pk, issue_pk):
        repo = _get_accessible_repo(request, pk)
        issue = get_object_or_404(Issue, pk=issue_pk, repository=repo)
        if not (request.user == issue.author or has_repo_write_access(request.user, repo)):
            raise PermissionDenied('Bu issue\'yu kapatma yetkiniz yok.')
        issue.status = 'closed'
        issue.save(update_fields=['status', 'updated_at'])
        return Response(IssueSerializer(issue).data)


@extend_schema(tags=['Depolar'], summary='Bir issue\'yu yeniden açar', request=None)
class IssueReopenView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = IssueSerializer

    def post(self, request, pk, issue_pk):
        repo = _get_accessible_repo(request, pk)
        issue = get_object_or_404(Issue, pk=issue_pk, repository=repo)
        if not (request.user == issue.author or has_repo_write_access(request.user, repo)):
            raise PermissionDenied('Bu issue\'yu yeniden açma yetkiniz yok.')
        issue.status = 'open'
        issue.save(update_fields=['status', 'updated_at'])
        return Response(IssueSerializer(issue).data)


@extend_schema(tags=['Depolar'], summary='Bir issue\'nun yorumlarını listeler veya yeni yorum oluşturur')
class IssueCommentListCreateView(generics.ListCreateAPIView):
    serializer_class = IssueCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_issue(self):
        repo = _get_accessible_repo(self.request, self.kwargs['pk'])
        return get_object_or_404(Issue, pk=self.kwargs['issue_pk'], repository=repo)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return IssueComment.objects.none()
        return IssueComment.objects.filter(issue=self.get_issue())

    def perform_create(self, serializer):
        serializer.save(issue=self.get_issue(), author=self.request.user)


@extend_schema(tags=['Depolar'], summary='Bir issue yorumunu günceller veya siler')
class IssueCommentDetailView(generics.UpdateAPIView, generics.DestroyAPIView):
    serializer_class = IssueCommentSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'comment_pk'

    def get_queryset(self):
        return IssueComment.objects.filter(issue_id=self.kwargs['issue_pk'], issue__repository_id=self.kwargs['pk'])

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if obj.author != request.user:
            raise PermissionDenied('Bu yorumu düzenleme veya silme yetkiniz yok.')


# --- Pull Requests ---

@extend_schema(tags=['Depolar'], summary='Bir deponun pull request\'lerini listeler veya yeni PR oluşturur')
class PullRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = PullRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

    def get_repo(self):
        return _get_accessible_repo(self.request, self.kwargs['pk'])

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return PullRequest.objects.none()
        return PullRequest.objects.filter(repository=self.get_repo())

    def perform_create(self, serializer):
        serializer.save(repository=self.get_repo(), author=self.request.user)


@extend_schema(tags=['Depolar'], summary='Bir pull request\'in detayını getirir veya günceller')
class PullRequestDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = PullRequestDetailSerializer
    permission_classes = [AllowAny]
    lookup_url_kwarg = 'pr_pk'

    def get_queryset(self):
        repo = _get_accessible_repo(self.request, self.kwargs['pk'])
        return PullRequest.objects.filter(repository=repo)

    def perform_update(self, serializer):
        pr = serializer.instance
        user = self.request.user
        if not (user.is_authenticated and (user == pr.author or has_repo_write_access(user, pr.repository))):
            raise PermissionDenied('Bu pull request üzerinde işlem yapma yetkiniz yok.')
        serializer.save()


@extend_schema(tags=['Depolar'], summary='Bir pull request\'i kapatır', request=None)
class PullRequestCloseView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PullRequestSerializer

    def post(self, request, pk, pr_pk):
        repo = _get_accessible_repo(request, pk)
        pr = get_object_or_404(PullRequest, pk=pr_pk, repository=repo)
        if not (request.user == pr.author or has_repo_write_access(request.user, repo)):
            raise PermissionDenied('Bu pull request\'i kapatma yetkiniz yok.')
        pr.status = 'closed'
        pr.save(update_fields=['status', 'updated_at'])
        return Response(PullRequestSerializer(pr).data)


@extend_schema(tags=['Depolar'], summary='Bir pull request\'i yeniden açar', request=None)
class PullRequestReopenView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PullRequestSerializer

    def post(self, request, pk, pr_pk):
        repo = _get_accessible_repo(request, pk)
        pr = get_object_or_404(PullRequest, pk=pr_pk, repository=repo)
        if not (request.user == pr.author or has_repo_write_access(request.user, repo)):
            raise PermissionDenied('Bu pull request\'i yeniden açma yetkiniz yok.')
        if pr.status == 'merged':
            raise ValidationError({'detail': 'Birleştirilmiş bir pull request yeniden açılamaz.'})
        pr.status = 'open'
        pr.save(update_fields=['status', 'updated_at'])
        return Response(PullRequestSerializer(pr).data)


@extend_schema(tags=['Depolar'], summary='Bir pull request\'in yorumlarını listeler veya yeni yorum oluşturur')
class PullRequestCommentListCreateView(generics.ListCreateAPIView):
    serializer_class = PullRequestCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_pull_request(self):
        repo = _get_accessible_repo(self.request, self.kwargs['pk'])
        return get_object_or_404(PullRequest, pk=self.kwargs['pr_pk'], repository=repo)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return PullRequestComment.objects.none()
        return PullRequestComment.objects.filter(pull_request=self.get_pull_request())

    def perform_create(self, serializer):
        serializer.save(pull_request=self.get_pull_request(), author=self.request.user)


@extend_schema(tags=['Depolar'], summary='Bir pull request yorumunu günceller veya siler')
class PullRequestCommentDetailView(generics.UpdateAPIView, generics.DestroyAPIView):
    serializer_class = PullRequestCommentSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'comment_pk'

    def get_queryset(self):
        return PullRequestComment.objects.filter(
            pull_request_id=self.kwargs['pr_pk'],
            pull_request__repository_id=self.kwargs['pk'],
        )

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if obj.author != request.user:
            raise PermissionDenied('Bu yorumu düzenleme veya silme yetkiniz yok.')
