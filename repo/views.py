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

# Create your views here.

@extend_schema(tags=['Repositories'], summary='Create a new repository owned by the authenticated user')
class RepoCreateView(generics.CreateAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


@extend_schema(tags=['Repositories'], summary='Create a new repository within an organization')
class RepoOrganizationCreateView(generics.CreateAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def perform_create(self, serializer):
        organization = get_object_or_404(Organization, pk=self.kwargs['organization_id'])
        serializer.save(owner=None, organization=organization)


# Repoları herkes görebilir ama sadece sahipleri düzenleyebilir. Bu yüzden list kısmında kontrole gerek yok.
@extend_schema(tags=['Repositories'], summary='List all repositories')
class RepoListView(generics.ListAPIView):
    serializer_class = RepoSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Repo.objects.all()    


@extend_schema(tags=['Repositories'], summary='Retrieve, update, or delete a repository')
class RepoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Repo.objects.all()

@extend_schema(tags=['Repositories'], summary='Update a repository owned by the authenticated user')
class RepoUpdateView(generics.UpdateAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Repo.objects.filter(owner=self.request.user)

@extend_schema(tags=['Repositories'], summary='Delete a repository owned by the authenticated user')
class RepoDeleteView(generics.DestroyAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Repo.objects.filter(owner=self.request.user)


# Admin İşlemleri

@extend_schema(tags=['Repositories'], summary='Admin list all repositories')
class RepoAdminListView(generics.ListAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAdminUser]

@extend_schema(tags=['Repositories'], summary='Admin retrieve, update, or delete a repository')
class RepoAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAdminUser]

@extend_schema(tags=['Repositories'], summary='Admin update any repository')
class RepoAdminUpdateView(generics.UpdateAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAdminUser]

@extend_schema(tags=['Repositories'], summary='Admin delete any repository')
class RepoAdminDeleteView(generics.DestroyAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAdminUser]

class RepoAdminCreateView(generics.CreateAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAdminUser]