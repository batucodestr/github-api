from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from .models import Repo
from .serializers import RepoSerializer, RepoDetailSerializer
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from organizations.models import Organization
from organizations.permissions import IsOrganizationMember

# Create your views here.

class RepoCreateView(generics.CreateAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class RepoOrganizationCreateView(generics.CreateAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def perform_create(self, serializer):
        organization = get_object_or_404(Organization, pk=self.kwargs['organization_id'])
        serializer.save(owner=None, organization=organization)


# Repoları herkes görebilir ama sadece sahipleri düzenleyebilir. Bu yüzden list kısmında kontrole gerek yok.
class RepoListView(generics.ListAPIView):
    serializer_class = RepoSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Repo.objects.all()    


class RepoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Repo.objects.all()

class RepoUpdateView(generics.UpdateAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Repo.objects.filter(owner=self.request.user)

class RepoDeleteView(generics.DestroyAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Repo.objects.filter(owner=self.request.user)


# Admin İşlemleri

class RepoAdminListView(generics.ListAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAdminUser]

class RepoAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAdminUser]

class RepoAdminUpdateView(generics.UpdateAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAdminUser]

class RepoAdminDeleteView(generics.DestroyAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAdminUser]

class RepoAdminCreateView(generics.CreateAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoDetailSerializer
    permission_classes = [IsAdminUser]