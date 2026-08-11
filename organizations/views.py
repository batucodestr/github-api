from rest_framework import generics
from drf_spectacular.utils import extend_schema
from .models import Organization, OrganizationMember
from .serializers import OrganizationMemberSerializer, OrganizationSerializer, OrganizationDetailSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .permissions import IsOrganizationAdmin,IsOrganizationOwner, IsOrganizationMember

# Create your views here.

# Organization Views
@extend_schema(tags=['Organizations'], summary='Create a new organization')
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
                "message": "Organization created successfully",
                "organization": OrganizationSerializer(organization).data,
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

@extend_schema(tags=['Organizations'], summary='List all organizations')
class OrganizationListView(generics.ListAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

@extend_schema(tags=['Organizations'], summary='Retrieve details for a specific organization')
class OrganizationDetailView(generics.RetrieveAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationDetailSerializer
    permission_classes = [IsAuthenticated]

@extend_schema(tags=['Organizations'], summary='Update an organization as an admin')
class OrganizationUpdateView(generics.UpdateAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

@extend_schema(tags=['Organizations'], summary='Delete an organization as the owner')
class OrganizationDeleteView(generics.DestroyAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsOrganizationOwner]


# Organization Member Views
@extend_schema(tags=['Organizations'], summary='Add a member to an organization')
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
                "message": "Member added to organization successfully",
                "organization_member": OrganizationMemberSerializer(organization_member).data,
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

@extend_schema(tags=['Organizations'], summary='Remove a member from an organization')
class OrganizationRemoveMemberView(generics.DestroyAPIView):
    queryset = OrganizationMember.objects.all()
    serializer_class = OrganizationMemberSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Member removed from organization successfully"},
            status=status.HTTP_200_OK,
        )

@extend_schema(tags=['Organizations'], summary='List members of an organization')
class OrganizationMemberListView(generics.ListAPIView):
    serializer_class = OrganizationMemberSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        organization_id = self.kwargs['organization_id']
        return OrganizationMember.objects.filter(organization_id=organization_id)