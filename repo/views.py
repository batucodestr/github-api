from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from drf_spectacular.utils import extend_schema
from .models import Repo
from .serializers import RepoSerializer, RepoDetailSerializer
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from organizations.models import Organization
from organizations.permissions import IsOrganizationMember

# Görünümler burada oluşturulur.

@extend_schema(tags=['Depolar'], summary='Kimliği doğrulanmış kullanıcının sahibi olduğu yeni depo oluşturur')
class RepoCreateView(generics.CreateAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


@extend_schema(tags=['Depolar'], summary='Bir organizasyon içinde yeni depo oluşturur')
class RepoOrganizationCreateView(generics.CreateAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def perform_create(self, serializer):
        organization = get_object_or_404(Organization, pk=self.kwargs['organization_id'])
        serializer.save(owner=None, organization=organization)


# Repoları herkes görebilir ama sadece sahipleri düzenleyebilir. Bu yüzden list kısmında kontrole gerek yok.
@extend_schema(tags=['Depolar'], summary='Tüm depoları listeler')
class RepoListView(generics.ListAPIView):
    serializer_class = RepoSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Repo.objects.all()    


@extend_schema(tags=['Depolar'], summary='Bir depoyu getirir, günceller veya siler')
class RepoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Repo.objects.all()

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