from rest_framework import generics
from drf_spectacular.utils import extend_schema
from .models import Organization, OrganizationMember
from .serializers import OrganizationMemberSerializer, OrganizationSerializer, OrganizationDetailSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
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
        organization_id = self.kwargs['organization_id']
        return OrganizationMember.objects.filter(organization_id=organization_id)