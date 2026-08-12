from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics
from drf_spectacular.utils import extend_schema
from .models import Organization, OrganizationMember, OrganizationInvitation, Team, TeamMember, TeamRepository
from .serializers import (
    OrganizationMemberSerializer,
    OrganizationSerializer,
    OrganizationDetailSerializer,
    OrganizationInvitationSerializer,
    TeamSerializer,
    TeamMemberSerializer,
    TeamRepositorySerializer,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.views import APIView
from rest_framework import status
from .permissions import IsOrganizationAdmin,IsOrganizationOwner, IsOrganizationMember

# Görünümler burada oluşturulur.

# Organization Views
@extend_schema(tags=['Organizasyonlar'], summary='Yeni bir organizasyon oluşturur')
class OrganizationCreateView(generics.CreateAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = serializer.save(owner=request.user)
        OrganizationMember.objects.create(
            organization=organization,
            user=request.user,
            role='admin'
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "message": "Organizasyon başarıyla oluşturuldu",
                "organization": OrganizationSerializer(organization).data,
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

@extend_schema(tags=['Organizasyonlar'], summary='Tüm organizasyonları listeler')
class OrganizationListView(generics.ListAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

@extend_schema(tags=['Organizasyonlar'], summary='Belirli bir organizasyonun detaylarını getirir')
class OrganizationDetailView(generics.RetrieveAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationDetailSerializer
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(60))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

@extend_schema(tags=['Organizasyonlar'], summary='Yönetici olarak bir organizasyonu günceller')
class OrganizationUpdateView(generics.UpdateAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

@extend_schema(tags=['Organizasyonlar'], summary='Sahip olarak bir organizasyonu siler')
class OrganizationDeleteView(generics.DestroyAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsOrganizationOwner]


# Organization Member Views
@extend_schema(tags=['Organizasyonlar'], summary='Organizasyona bir üye ekler')
class OrganizationAddMemberView(generics.CreateAPIView):
    queryset = OrganizationMember.objects.all()
    serializer_class = OrganizationMemberSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization_member = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "message": "Üye organizasyona başarıyla eklendi",
                "organization_member": OrganizationMemberSerializer(organization_member).data,
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

@extend_schema(tags=['Organizasyonlar'], summary='Organizasyondan bir üyeyi kaldırır')
class OrganizationRemoveMemberView(generics.DestroyAPIView):
    queryset = OrganizationMember.objects.all()
    serializer_class = OrganizationMemberSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Üye organizasyondan başarıyla kaldırıldı"},
            status=status.HTTP_200_OK,
        )

@extend_schema(tags=['Organizasyonlar'], summary='Bir organizasyonun üyelerini listeler')
class OrganizationMemberListView(generics.ListAPIView):
    serializer_class = OrganizationMemberSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return OrganizationMember.objects.none()
        organization_id = self.kwargs['organization_id']
        return OrganizationMember.objects.filter(organization_id=organization_id)


# Organization Invitation Views

@extend_schema(tags=['Organizasyonlar'], summary='Bir kullanıcıyı organizasyona davet eder')
class OrganizationInvitationCreateView(generics.CreateAPIView):
    queryset = OrganizationInvitation.objects.all()
    serializer_class = OrganizationInvitationSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

    def create(self, request, *args, **kwargs):
        organization = get_object_or_404(Organization, pk=self.kwargs['organization_id'])
        invited_user_id = request.data.get('invited_user')

        if not invited_user_id:
            raise ValidationError({'invited_user': 'Bu alan zorunludur.'})

        if OrganizationMember.objects.filter(organization=organization, user_id=invited_user_id).exists():
            raise ValidationError({'detail': 'Kullanıcı zaten bu organizasyonun üyesi.'})

        if OrganizationInvitation.objects.filter(
            organization=organization, invited_user_id=invited_user_id, status='pending'
        ).exists():
            raise ValidationError({'detail': 'Bu kullanıcı için zaten bekleyen bir davet var.'})

        invitation = OrganizationInvitation.objects.create(
            organization=organization,
            invited_user_id=invited_user_id,
            invited_by=request.user,
        )
        return Response(
            OrganizationInvitationSerializer(invitation).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=['Organizasyonlar'], summary='Kimliği doğrulanmış kullanıcının aldığı davetleri listeler')
class MyInvitationListView(generics.ListAPIView):
    serializer_class = OrganizationInvitationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return OrganizationInvitation.objects.none()
        return OrganizationInvitation.objects.filter(invited_user=self.request.user)


@extend_schema(tags=['Organizasyonlar'], summary='Bir organizasyon davetini kabul eder', request=None)
class OrganizationInvitationAcceptView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationInvitationSerializer

    def post(self, request, pk):
        invitation = get_object_or_404(OrganizationInvitation, pk=pk, invited_user=request.user)
        if invitation.status != 'pending':
            raise ValidationError({'detail': 'Bu davet artık geçerli değil.'})

        invitation.status = 'accepted'
        invitation.save(update_fields=['status', 'updated_at'])
        OrganizationMember.objects.get_or_create(
            organization=invitation.organization,
            user=request.user,
            defaults={'role': 'member'},
        )
        return Response(OrganizationInvitationSerializer(invitation).data)


@extend_schema(tags=['Organizasyonlar'], summary='Bir organizasyon davetini reddeder', request=None)
class OrganizationInvitationRejectView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationInvitationSerializer

    def post(self, request, pk):
        invitation = get_object_or_404(OrganizationInvitation, pk=pk, invited_user=request.user)
        if invitation.status != 'pending':
            raise ValidationError({'detail': 'Bu davet artık geçerli değil.'})

        invitation.status = 'rejected'
        invitation.save(update_fields=['status', 'updated_at'])
        return Response(OrganizationInvitationSerializer(invitation).data)


# Team Views

@extend_schema(tags=['Organizasyonlar'], summary='Bir organizasyonun takımlarını listeler veya yeni takım oluşturur')
class TeamListCreateView(generics.ListCreateAPIView):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Team.objects.none()
        return Team.objects.filter(organization_id=self.kwargs['organization_id'])

    def perform_create(self, serializer):
        organization_id = self.kwargs['organization_id']
        if not OrganizationMember.objects.filter(
            organization_id=organization_id, user=self.request.user, role='admin'
        ).exists():
            raise PermissionDenied('Takım oluşturmak için organizasyon yöneticisi olmalısınız.')
        organization = get_object_or_404(Organization, pk=organization_id)
        if Team.objects.filter(organization=organization, name=serializer.validated_data['name']).exists():
            raise ValidationError({'name': 'Bu isimde bir takım zaten mevcut.'})
        serializer.save(organization=organization)


@extend_schema(tags=['Organizasyonlar'], summary='Bir takımın detayını getirir veya siler')
class TeamDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Team.objects.none()
        return Team.objects.filter(organization_id=self.kwargs['organization_id'])

    def perform_destroy(self, instance):
        if not OrganizationMember.objects.filter(
            organization_id=self.kwargs['organization_id'], user=self.request.user, role='admin'
        ).exists():
            raise PermissionDenied('Takımı silmek için organizasyon yöneticisi olmalısınız.')
        instance.delete()


@extend_schema(tags=['Organizasyonlar'], summary='Bir takımın üyelerini listeler veya üye ekler')
class TeamMemberListCreateView(generics.ListCreateAPIView):
    serializer_class = TeamMemberSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_team(self):
        return get_object_or_404(
            Team, pk=self.kwargs['team_id'], organization_id=self.kwargs['organization_id']
        )

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return TeamMember.objects.none()
        return TeamMember.objects.filter(team=self.get_team())

    def perform_create(self, serializer):
        organization_id = self.kwargs['organization_id']
        if not OrganizationMember.objects.filter(
            organization_id=organization_id, user=self.request.user, role='admin'
        ).exists():
            raise PermissionDenied('Takıma üye eklemek için organizasyon yöneticisi olmalısınız.')
        team = self.get_team()
        user_id = serializer.validated_data['user'].id
        if not OrganizationMember.objects.filter(organization_id=organization_id, user_id=user_id).exists():
            raise ValidationError({'user': 'Kullanıcı bu organizasyonun üyesi değil.'})
        serializer.save(team=team)


@extend_schema(tags=['Organizasyonlar'], summary='Bir takımdan üyeyi çıkarır')
class TeamMemberRemoveView(generics.DestroyAPIView):
    serializer_class = TeamMemberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TeamMember.objects.filter(
            team_id=self.kwargs['team_id'], team__organization_id=self.kwargs['organization_id']
        )

    def perform_destroy(self, instance):
        if not OrganizationMember.objects.filter(
            organization_id=self.kwargs['organization_id'], user=self.request.user, role='admin'
        ).exists():
            raise PermissionDenied('Takımdan üye çıkarmak için organizasyon yöneticisi olmalısınız.')
        instance.delete()


@extend_schema(tags=['Organizasyonlar'], summary='Bir takımın erişebildiği depoları listeler veya erişim ekler')
class TeamRepositoryListCreateView(generics.ListCreateAPIView):
    serializer_class = TeamRepositorySerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_team(self):
        return get_object_or_404(
            Team, pk=self.kwargs['team_id'], organization_id=self.kwargs['organization_id']
        )

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return TeamRepository.objects.none()
        return TeamRepository.objects.filter(team=self.get_team())

    def perform_create(self, serializer):
        organization_id = self.kwargs['organization_id']
        if not OrganizationMember.objects.filter(
            organization_id=organization_id, user=self.request.user, role='admin'
        ).exists():
            raise PermissionDenied('Takıma depo eklemek için organizasyon yöneticisi olmalısınız.')
        team = self.get_team()
        repository = serializer.validated_data['repository']
        if repository.organization_id != int(organization_id):
            raise ValidationError({'repository': 'Depo bu organizasyona ait değil.'})
        serializer.save(team=team)


@extend_schema(tags=['Organizasyonlar'], summary='Bir takımın depo erişimini kaldırır')
class TeamRepositoryRemoveView(generics.DestroyAPIView):
    serializer_class = TeamRepositorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TeamRepository.objects.filter(
            team_id=self.kwargs['team_id'], team__organization_id=self.kwargs['organization_id']
        )

    def perform_destroy(self, instance):
        if not OrganizationMember.objects.filter(
            organization_id=self.kwargs['organization_id'], user=self.request.user, role='admin'
        ).exists():
            raise PermissionDenied('Takımın depo erişimini kaldırmak için organizasyon yöneticisi olmalısınız.')
        instance.delete()